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
from core.api.v1.status.shemas import StatusScreenSchema
from core.infrastructure.django_apps.customers.models import (
    Employee,
    LevelBenefit,
    RatingConfig,
    UserModels,
)

GO_SERVICE_URL = getattr(settings, "GO_SERVICE_URL", "http://go-calc-service:8080")
GO_SERVICE_TIMEOUT = getattr(settings, "GO_SERVICE_TIMEOUT", 10)

router = Router(tags=["Status"])
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


# -------------------- GO REQUEST --------------------

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


# -------------------- GO CALL --------------------

def call_go_service(payload: dict) -> dict:
    response = requests.post(
        f"{GO_SERVICE_URL}/api/v1/calculate",
        json=payload,
        timeout=GO_SERVICE_TIMEOUT,
    )

    # бросит HTTPError -> поймает декоратор
    response.raise_for_status()

    return response.json()


# -------------------- DOMAIN LOGIC --------------------

def update_employee(employee: Employee, result: dict):
    employee.points = result["score"]
    employee.level = result["level"]
    employee.save(update_fields=["points", "level"])


def build_financial_forecast(next_level: str | None):
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


def build_mobile_response(employee: Employee, result: dict, config: RatingConfig):
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


# -------------------- API --------------------

# @handle_service_errors
@router.get("/", response=StatusScreenSchema, auth=user_auth)
def get_status(request):
    user = request.auth

    model_user = UserModels.objects.get(id=user.user_id)
    employee = model_user.employee
    config = RatingConfig.objects.get(is_active=True)

    logger.info(
        "Calculating rating for employee %s (%s)",
        employee.id,
        employee.name,
    )

    validate_employee(employee)

    payload = build_go_request(employee, config)
    result = call_go_service(payload)

    update_employee(employee, result)

    return build_mobile_response(employee, result, config)