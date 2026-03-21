import logging

import requests
from django.conf import settings
from ninja import Router

from core.api.v1.customers.handlers import user_auth
from core.api.v1.status.exeptions import handle_service_errors
from core.api.v1.status.service import (
    calculate_conversion_percent,
    calculate_progress_percent,
)
from core.api.v1.status.shemas import (
    StatusScreenSchema,
    ScenarioScreenInSchema,
    ScenarioScreenOutSchema,
)
from core.infrastructure.django_apps.customers.models import (
    Employee,
    LevelBenefit,
    RatingConfig,
    UserModels,
)

GO_SERVICE_URL = getattr(settings, "GO_SERVICE_URL", "http://go-calc-service:8080")
GO_SERVICE_TIMEOUT = getattr(settings, "GO_SERVICE_TIMEOUT", 10)

router = Router(tags=["test"])
logger = logging.getLogger(__name__)


# -------------------- VALIDATION --------------------


def validate_employee(employee: Employee):
    if employee.volume_plan <= 0:
        raise Exception("volume_plan must be > 0")

    if employee.deals_plan <= 0:
        raise Exception("deals_plan must be > 0")

    if employee.bank_share_goal <= 0:
        raise Exception("bank_share_goal must be > 0")

    if employee.approved_requests > employee.submitted_requests:
        raise Exception("approved_requests cannot exceed submitted_requests")


def get_active_rating_config() -> RatingConfig:
    return RatingConfig.objects.get(is_active=True)


# -------------------- GO REQUEST BUILDERS --------------------


def build_go_request(employee: Employee, config: RatingConfig) -> dict:
    return {
        "fact_volume": employee.volume,
        "plan_volume": employee.volume_plan,
        "fact_deals": employee.deals_count,
        "plan_deals": employee.deals_plan,
        "fact_bank_share": employee.bank_share,
        "target_bank_share": employee.bank_share_goal,
        "submitted_apps": employee.submitted_requests,
        "approved_apps": employee.approved_requests,
        "conversion_percent": calculate_conversion_percent(
            employee.submitted_requests,
            employee.approved_requests,
        ),
        "max_index": config.max_index,
        "weights": {
            "volume": config.weight_volume,
            "deals": config.weight_deals,
            "bank_share": config.weight_bank_share,
            "conversion": config.weight_conversion,
        },
        "thresholds": {
            "gold_from": config.gold_from,
            "black_from": config.black_from,
        },
    }


def build_finance_rules(config: RatingConfig) -> dict:
    return {
        "silver": config.silver_bonus,
        "gold": config.gold_bonus,
        "black": config.black_bonus,
    }


def map_extra_products_to_bank_share(extra_products: int) -> float:
    """
    Временная логика для хакатона:
    1 доп. продукт = +2 п.п. к доле банка.
    """
    return extra_products * 2.0


def build_go_scenario_delta(data: ScenarioScreenInSchema) -> dict:
    effective_extra_bank_share = (
        data.extra_bank_share + map_extra_products_to_bank_share(data.extra_products)
    )

    return {
        "extra_volume": data.extra_volume,
        "extra_deals": data.extra_deals,
        "extra_bank_share": effective_extra_bank_share,
        "extra_submitted": data.extra_submitted,
        "extra_approved": data.extra_approved,
    }


# -------------------- GO CALLS --------------------


def call_go_calculate(payload: dict) -> dict:
    response = requests.post(
        f"{GO_SERVICE_URL}/api/v1/calculate",
        json=payload,
        timeout=GO_SERVICE_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def call_go_scenario(payload: dict) -> dict:
    response = requests.post(
        f"{GO_SERVICE_URL}/api/v1/scenario",
        json=payload,
        timeout=GO_SERVICE_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def call_go_finance_scenario(payload: dict) -> dict:
    response = requests.post(
        f"{GO_SERVICE_URL}/api/v1/finance/scenario",
        json=payload,
        timeout=GO_SERVICE_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


# -------------------- DOMAIN LOGIC --------------------


def update_employee(employee: Employee, result: dict):
    employee.points = result["score"]
    employee.level = result["level"]
    employee.save(update_fields=["points", "level"])


def build_financial_forecast(next_level: str | None) -> dict:
    if not next_level:
        return {
            "next_level": None,
            "income_growth_year": 0,
            "mortgage_saving_year": 0,
            "other_benefit_year": 0,
            "total_benefit_year": 0,
            "title": "Максимальный уровень достигнут",
            "description": "Дополнительные привилегии уже активны",
        }

    benefit = LevelBenefit.objects.get(level=next_level, is_active=True)

    return {
        "next_level": next_level,
        "income_growth_year": benefit.income_growth_year,
        "mortgage_saving_year": benefit.mortgage_saving_year,
        "other_benefit_year": benefit.other_benefit_year,
        "total_benefit_year": (
            benefit.income_growth_year
            + benefit.mortgage_saving_year
            + benefit.other_benefit_year
        ),
        "title": benefit.title,
        "description": benefit.description,
    }


def build_mobile_response(employee: Employee, result: dict, config: RatingConfig) -> dict:
    next_level_data = result.get("next_level") or {}

    next_level = next_level_data.get("next_level")
    missing_score = next_level_data.get("missing_score")

    score = float(result.get("score", 0))
    missing_score_value = float(missing_score) if missing_score is not None else 0.0

    return {
        "employee_id": employee.id,
        "name": employee.name,
        "level": result.get("level"),
        "score": score,
        "next_level": next_level,
        "next_level_points": score + missing_score_value,
        "points_to_next_level": missing_score,
        "progress_percent": calculate_progress_percent(
            score=score,
            level=result.get("level"),
            gold_from=config.gold_from,
            black_from=config.black_from,
        ),
        "financial_forecast": build_financial_forecast(next_level),
    }


def get_level_benefit_payload(level: str | None) -> dict:
    if not level:
        return {
            "income_growth_year": 0,
            "mortgage_saving_year": 0,
            "other_benefit_year": 0,
            "total_benefit_year": 0,
        }

    benefit = LevelBenefit.objects.get(level=level, is_active=True)

    total_benefit_year = (
        benefit.income_growth_year
        + benefit.mortgage_saving_year
        + benefit.other_benefit_year
    )

    return {
        "income_growth_year": benefit.income_growth_year,
        "mortgage_saving_year": benefit.mortgage_saving_year,
        "other_benefit_year": benefit.other_benefit_year,
        "total_benefit_year": total_benefit_year,
    }


def build_scenario_mobile_response(
    data: ScenarioScreenInSchema,
    scenario_result: dict,
    finance_result: dict,
) -> dict:
    current_level = scenario_result["current"]["level"]
    scenario_level = scenario_result["scenario"]["level"]

    benefit_payload = get_level_benefit_payload(scenario_level)

    return {
        "current": {
            "level": current_level,
            "score": scenario_result["current"]["score"],
            "bonus": finance_result["current"]["bonus"],
        },
        "scenario": {
            "level": scenario_level,
            "score": scenario_result["scenario"]["score"],
            "bonus": finance_result["scenario"]["bonus"],
        },
        "delta": {
            "score_delta": scenario_result["score_delta"],
            "bonus_delta": finance_result["bonus_delta"],
            "income_growth_year": benefit_payload["income_growth_year"],
            "mortgage_saving_year": benefit_payload["mortgage_saving_year"],
            "other_benefit_year": benefit_payload["other_benefit_year"],
            "total_benefit_year": benefit_payload["total_benefit_year"],
        },
        "applied_changes": {
            "extra_volume": data.extra_volume,
            "extra_deals": data.extra_deals,
            "extra_bank_share": data.extra_bank_share,
            "extra_submitted": data.extra_submitted,
            "extra_approved": data.extra_approved,
            "extra_products": data.extra_products,
        },
    }


# -------------------- API --------------------


@router.get("/", response=StatusScreenSchema, auth=user_auth)
@handle_service_errors
def get_status(request):
    user = request.auth

    model_user = UserModels.objects.get(id=user.user_id)
    employee = model_user.employee
    config = get_active_rating_config()

    logger.info(
        "Calculating rating for employee %s (%s)",
        employee.id,
        employee.name,
    )

    validate_employee(employee)

    payload = build_go_request(employee, config)
    result = call_go_calculate(payload)

    update_employee(employee, result)

    return build_mobile_response(employee, result, config)


@router.post("/scenario", response=ScenarioScreenOutSchema, auth=user_auth)
@handle_service_errors
def get_status_scenario(request, data: ScenarioScreenInSchema):
    user = request.auth

    model_user = UserModels.objects.get(id=user.user_id)
    employee = model_user.employee
    config = get_active_rating_config()

    logger.info(
        "Calculating scenario for employee %s (%s)",
        employee.id,
        employee.name,
    )

    validate_employee(employee)

    go_input = build_go_request(employee, config)
    go_delta = build_go_scenario_delta(data)
    finance_rules = build_finance_rules(config)

    scenario_payload = {
        "input": go_input,
        "delta": go_delta,
    }

    finance_scenario_payload = {
        "input": go_input,
        "delta": go_delta,
        "rules": finance_rules,
    }

    scenario_result = call_go_scenario(scenario_payload)
    finance_result = call_go_finance_scenario(finance_scenario_payload)

    return build_scenario_mobile_response(
        data=data,
        scenario_result=scenario_result,
        finance_result=finance_result,
    )
    

def build_scenario_screen_response(scenario_result: dict, finance_result: dict) -> dict:
    scenario_level = scenario_result["scenario"]["level"]
    benefit = get_level_benefit_payload(scenario_level)

    return {
        "current_level": scenario_result["current"]["level"],
        "current_score": scenario_result["current"]["score"],
        "scenario_level": scenario_result["scenario"]["level"],
        "scenario_score": scenario_result["scenario"]["score"],
        "scenario_bonus": finance_result["scenario"]["bonus"],
        "income_growth_year": benefit["income_growth_year"],
        "mortgage_saving_year": benefit["mortgage_saving_year"],
    }
