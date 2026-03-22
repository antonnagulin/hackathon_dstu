import logging
from datetime import date as date_at

import requests
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from ninja import Router

from core.api.v1.customers.handlers import user_auth
from core.api.v1.status.exeptions import handle_service_errors
from core.api.v1.status.service import (
    calculate_conversion_percent,
    calculate_progress_percent,
)
from core.api.v1.status.shemas import (
    DailyResultsInSchema,
    EmployeeProfileSchema,
    GetDailyResultsOutSchema,
    LevelPrivilegesScreenSchema,
    MonthlyTasksScreenSchema,
    PersonalFinancialEffectSchema,
    PostDailyResultsOutSchema,
    RatingDetailsScreenSchema,
    ScenarioScreenInSchema,
    ScenarioScreenOutSchema,
    StatusScreenSchema,
)
from core.infrastructure.django_apps.customers.models import (
    Employee,
    EmployeeDailyResult,
    LevelBenefit,
    LevelPrivilege,
    MonthlyTask,
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


def get_active_rating_config() -> RatingConfig:
    return RatingConfig.objects.get(is_active=True)


# -------------------- GO REQUEST BUILDERS --------------------


def build_go_calculate_request(employee: Employee, config: RatingConfig) -> dict:
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
        "extra_submitted": 0,
        "extra_approved": 0,
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


def update_employee_rating(employee: Employee, result: dict):
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


def build_status_screen_response(
    employee: Employee,
    result: dict,
    config: RatingConfig,
) -> dict:
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


def build_scenario_screen_response(
    current_status_result: dict,
    scenario_result: dict,
    finance_result: dict,
) -> dict:
    current_next_level = current_status_result.get("next_level") or {}
    scenario_level = scenario_result["scenario"]["level"]

    benefit = LevelBenefit.objects.get(level=scenario_level, is_active=True)

    return {
        "current_status": {
            "level": current_status_result["level"],
            "points_to_next_level": float(current_next_level.get("missing_score") or 0),
        },
        "result": {
            "new_score": float(scenario_result["scenario"]["score"]),
            "new_level": scenario_level,
            "new_income": float(finance_result["scenario"]["bonus"]),
            "new_saving": float(benefit.mortgage_saving_year),
        },
    }

def build_rating_details_screen_response(result: dict) -> dict:
    breakdown = result.get("breakdown") or {}
    next_level_data = result.get("next_level") or {}

    items = [
        {
            "code": "volume",
            "title": "Объём",
            "points": float(breakdown.get("volume_contribution") or 0),
            "formula": "(факт объёма / план объёма) × 100, максимум 120",
            "how_to_improve": "Увеличить объём профинансированных сделок",
        },
        {
            "code": "deals",
            "title": "Сделки",
            "points": float(breakdown.get("deals_contribution") or 0),
            "formula": "(количество сделок / план по сделкам) × 100, максимум 120",
            "how_to_improve": "Увеличить число оформленных сделок",
        },
        {
            "code": "bank_share",
            "title": "Доля банка",
            "points": float(breakdown.get("share_contribution") or 0),
            "formula": "(фактическая доля / целевая доля) × 100, максимум 120",
            "how_to_improve": "Увеличить долю банка в портфеле",
        },
        {
            "code": "conversion",
            "title": "Конверсия",
            "points": float(breakdown.get("conv_contribution") or 0),
            "formula": "(одобрено / подано) × 100, максимум 120",
            "how_to_improve": "Повысить качество подаваемых заявок",
        },
    ]

    return {
        "level": result["level"],
        "score": float(result["score"]),
        "next_level": next_level_data.get("next_level"),
        "points_to_next_level": next_level_data.get("missing_score"),
        "items": items,
        # "cta": {
        #     "title": "Смоделировать рост",
        #     "action": "open_scenario_calculator",
        # },
    }


LEVEL_ORDER = {
    "Silver": 1,
    "Gold": 2,
    "Black": 3,
}

def calculate_program_duration_months(start_date):
    if not start_date:
        return 0

    today = timezone.localdate()
    months = (today.year - start_date.year) * 12 + (today.month - start_date.month)

    if today.day < start_date.day:
        months -= 1

    return max(months, 0)


def build_employee_profile_response(employee: Employee) -> dict:
    registered_at = getattr(employee, "created_at", None)
    program_registered_at = registered_at.date().isoformat() if registered_at else None

    return {
        "full_name": employee.name,
        "dealer_code": getattr(employee, "dealer_code", None),
        "position": getattr(employee, "position", None),
        "phone": getattr(employee.user, "phone_number", None),
        "email": getattr(employee, "email", None),
        "level": employee.level,
        "program_registered_at": program_registered_at,
        "sber_id": str(getattr(employee, "id", None)),
    }


def build_level_privileges_screen_response(current_level: str) -> dict:
    privileges = LevelPrivilege.objects.filter(is_active=True).order_by("unlock_level", "id")

    active = []
    locked = []

    current_rank = LEVEL_ORDER[current_level]

    for privilege in privileges:
        item = {
            "title": privilege.title,
            "description": privilege.description,
            "financial_effect_rub": privilege.financial_effect_rub,
            "status": "active" if current_rank >= LEVEL_ORDER[privilege.unlock_level] else "locked",
            "unlock_level": privilege.unlock_level,
        }

        if current_rank >= LEVEL_ORDER[privilege.unlock_level]:
            active.append(item)
        else:
            locked.append(item)

    return {
        "current_level": current_level,
        "active": active,
        "locked": locked,
    }
    

def build_personal_financial_effect_response(employee: Employee) -> dict:
    benefit = LevelBenefit.objects.get(level=employee.level, is_active=True)

    return {
        "level": employee.level,
        "bonus_income_year": benefit.bonus_income_year,
        "mortgage_saving_year": benefit.mortgage_saving_year,
        "cashback_year": benefit.cashback_year,
        "dms_cost_year": benefit.dms_cost_year,
        "total_benefit_year": (
            benefit.bonus_income_year
            + benefit.mortgage_saving_year
            + benefit.cashback_year
            + benefit.dms_cost_year
        ),
    }

def get_month_bounds(target_date: date_at):
    month_start = target_date.replace(day=1)

    if target_date.month == 12:
        next_month = target_date.replace(year=target_date.year + 1, month=1, day=1)
    else:
        next_month = target_date.replace(month=target_date.month + 1, day=1)

    return month_start, next_month


def recalculate_employee_from_daily_results(employee: Employee, target_date: date_at | None = None):
    target_date = target_date or timezone.localdate()
    month_start, next_month = get_month_bounds(target_date)

    aggregates = EmployeeDailyResult.objects.filter(
        employee=employee,
        date__gte=month_start,
        date__lt=next_month,
    ).aggregate(
        total_deals=Sum("deals_count"),
        total_volume=Sum("credit_volume"),
        total_extra_products=Sum("extra_products_count"),
    )

    employee.deals_count = aggregates["total_deals"] or 0
    employee.volume = aggregates["total_volume"] or 0

    if hasattr(employee, "extra_products_count"):
        employee.extra_products_count = aggregates["total_extra_products"] or 0

    employee.save()
    
    
def get_month_bounds(target_date: date_at):
    month_start = target_date.replace(day=1)

    if target_date.month == 12:
        next_month = target_date.replace(year=target_date.year + 1, month=1, day=1)
    else:
        next_month = target_date.replace(month=target_date.month + 1, day=1)

    return month_start, next_month



def get_employee_monthly_daily_aggregates(employee, target_date: date_at | None = None) -> dict:
    target_date = target_date or timezone.localdate()
    month_start, next_month = get_month_bounds(target_date)

    aggregates = EmployeeDailyResult.objects.filter(
        employee=employee,
        date__gte=month_start,
        date__lt=next_month,
    ).aggregate(
        total_deals=Sum("deals_count"),
        total_volume=Sum("credit_volume"),
        total_extra_products=Sum("extra_products_count"),
    )

    return {
        "deals": float(aggregates["total_deals"] or 0),
        "volume": float(aggregates["total_volume"] or 0),
        "extra_products": float(aggregates["total_extra_products"] or 0),
    }
    
def get_task_current_value(employee, task, monthly_aggregates: dict):
    if task.task_type == "deals":
        return monthly_aggregates["deals"]

    if task.task_type == "volume":
        return monthly_aggregates["volume"]

    if task.task_type == "extra_products":
        return monthly_aggregates["extra_products"]

    if task.task_type == "bank_share":
        return float(employee.bank_share)

    return 0.0


def calculate_task_progress_percent(current: float, target: float) -> float:
    if target <= 0:
        return 0.0
    return round(min((current / target) * 100, 100), 2)


def build_monthly_tasks_response(employee) -> dict:
    tasks = MonthlyTask.objects.filter(is_active=True).order_by("deadline", "id")
    monthly_aggregates = get_employee_monthly_daily_aggregates(employee)

    items = []

    for task in tasks:
        current_value = get_task_current_value(employee, task, monthly_aggregates)
        progress_percent = calculate_task_progress_percent(current_value, task.target_value)

        items.append({
            "title": task.title,
            "description": task.description,
            "progress_current": current_value,
            "progress_target": task.target_value,
            "progress_percent": progress_percent,
            "reward_points": task.reward_points,
            "deadline": task.deadline.isoformat(),
            "is_completed": current_value >= task.target_value,
        })

    return {
        "items": items,
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

    payload = build_go_calculate_request(employee, config)
    result = call_go_calculate(payload)

    update_employee_rating(employee, result)

    return build_status_screen_response(employee, result, config)


# @handle_service_errors
@router.post("/scenario", response=ScenarioScreenOutSchema, auth=user_auth)
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

    go_input = build_go_calculate_request(employee, config)
    go_delta = build_go_scenario_delta(data)
    finance_rules = build_finance_rules(config)

    current_status_result = call_go_calculate(go_input)

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

    return build_scenario_screen_response(
        current_status_result=current_status_result,
        scenario_result=scenario_result,
        finance_result=finance_result,
    )
    

@router.get("/details", response=RatingDetailsScreenSchema, auth=user_auth)
@handle_service_errors
def get_status_details(request):
    user = request.auth
    model_user = UserModels.objects.get(id=user.user_id)
    employee = model_user.employee
    config = get_active_rating_config()

    logger.info(
        "Calculating rating details for employee %s (%s)",
        employee.id,
        employee.name,
    )

    validate_employee(employee)

    payload = build_go_calculate_request(employee, config)
    result = call_go_calculate(payload)

    update_employee_rating(employee, result)

    return build_rating_details_screen_response(result)



@router.get("/privileges", response=LevelPrivilegesScreenSchema, auth=user_auth)
@handle_service_errors
def get_level_privileges(request):
    user = request.auth
    model_user = UserModels.objects.get(id=user.user_id)
    employee = model_user.employee

    logger.info(
        "Loading privileges for employee %s (%s)",
        employee.id,
        employee.name,
    )

    return build_level_privileges_screen_response(employee.level)



@router.post("/daily-results", response=PostDailyResultsOutSchema, auth=user_auth)
# @handle_service_errors
def save_daily_results(request, data: DailyResultsInSchema):
    user = request.auth
    model_user = UserModels.objects.get(id=user.user_id)
    employee = model_user.employee

    daily_result, _ = EmployeeDailyResult.objects.update_or_create(
        employee=employee,
        date=data.date,
        defaults={
            "deals_count": data.deals_count,
            "credit_volume": data.credit_volume,
            "extra_products_count": data.extra_products_count,
        },
    )

    recalculate_employee_from_daily_results(employee, target_date=daily_result.date)

    return {
        # "date": str(daily_result.date),
        # "deals_count": daily_result.deals_count,
        # "credit_volume": daily_result.credit_volume,
        # "extra_products_count": daily_result.extra_products_count,
        "saved": True,
    }

# @handle_service_errors    
@router.get("/daily-results", response=GetDailyResultsOutSchema, auth=user_auth)
def get_daily_results(request, date: str | None = None):
    user = request.auth
    model_user = UserModels.objects.get(id=user.user_id)
    employee = model_user.employee

    target_date = date or str(date_at.today())

    daily_result, _ = EmployeeDailyResult.objects.get_or_create(
        employee=employee,
        date=target_date,
        defaults={
            "deals_count": 0,
            "credit_volume": 0.0,
            "extra_products_count": 0,
        },
    )

    return {
        "date": str(daily_result.date),
        "deals_count": daily_result.deals_count,
        "credit_volume": daily_result.credit_volume,
        "extra_products_count": daily_result.extra_products_count,
        # "saved": True,
    }
    
    
@router.get("/profile", response=EmployeeProfileSchema, auth=user_auth)
@handle_service_errors
def get_employee_profile(request):
    user = request.auth
    model_user = UserModels.objects.get(id=user.user_id)
    employee = model_user.employee

    logger.info(
        "Loading profile for employee %s (%s)",
        employee.id,
        employee.name,
    )

    return build_employee_profile_response(employee)



@router.get("/financial-effect", response=PersonalFinancialEffectSchema, auth=user_auth)
@handle_service_errors
def get_personal_financial_effect(request):
    user = request.auth
    model_user = UserModels.objects.get(id=user.user_id)
    employee = model_user.employee

    logger.info(
        "Loading financial effect for employee %s (%s)",
        employee.id,
        employee.name,
    )

    return build_personal_financial_effect_response(employee)



@router.get("/monthly-tasks", response=MonthlyTasksScreenSchema, auth=user_auth)
@handle_service_errors
def get_monthly_tasks(request):
    user = request.auth
    model_user = UserModels.objects.get(id=user.user_id)
    employee = model_user.employee

    logger.info(
        "Loading monthly tasks for employee %s (%s)",
        employee.id,
        employee.name,
    )

    return build_monthly_tasks_response(employee)