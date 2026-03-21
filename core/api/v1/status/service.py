import logging

from core.infrastructure.django_apps.customers.models import Employee

logger = logging.getLogger(__name__)

def create_go_service_payload(raw: dict) -> dict:
    """
    Преобразует данные из camelCase (Python/Django) в snake_case (Go‑сервис).

    Args:
        raw (dict): входные данные в формате camelCase.

    Returns:
        dict: payload в формате snake_case для Go‑сервиса.
    """
    try:
        payload = {
            "fact_volume": raw["FactVolume"],
            "plan_volume": raw["PlanVolume"],
            "fact_deals": raw["FactDeals"],
            "plan_deals": raw["PlanDeals"],
            "fact_bank_share": raw["FactBankShare"],
            "target_bank_share": raw["TargetBankShare"],
            "submitted_apps": raw["SubmittedApps"],
            "approved_apps": raw["ApprovedApps"],
            "conversion_percent": raw["ConversionPercent"],
            "max_index": raw["MaxIndex"],
            "weights": {
                "volume": raw["Weights"]["Volume"],
                "deals": raw["Weights"]["Deals"],
                "bank_share": raw["Weights"]["BankShare"],
                "conversion": raw["Weights"]["Conversion"],
            },
            "thresholds": {
                "gold_from": raw["Thresholds"]["GoldFrom"],
                "black_from": raw["Thresholds"]["BlackFrom"],
            },
        }
        logger.debug("Successfully created payload for Go service")
        return payload
    except KeyError as e:
        error_msg = f"Missing key in raw data: {str(e)}"
        logger.error(error_msg)
        raise KeyError(error_msg) from e
    except Exception as e:
        error_msg = f"Error creating payload: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg) from e


def get_level(points: float) -> str:
    if points >= 90:
        return "Black"
    elif points >= 70:
        return "Gold"
    else:
        return "Silver"
    

def calculate_index(employee: Employee) -> float:
    """
    Рассчёт баллов по обновлённой формуле:
    0.35*объем + 0.25*количество + 0.25*доля + 0.15*конверсия
    """

    # 1. Объём сделок
    volume_index = min((employee.volume / employee.volume_plan) * 100, 120)

    # 2. Количество сделок
    deals_index = min((employee.deals_count / employee.deals_plan) * 100, 120)

    # 3. Доля банка
    if employee.bank_share_goal == 0:
        bank_index = 0
    else:
        bank_index = min((employee.bank_share / employee.bank_share_goal) * 100, 120)

    # 4. Конверсия
    if employee.submitted_requests == 0:
        conversion_index = 0
    else:
        conversion_index = min((employee.approved_requests / employee.submitted_requests) * 100, 100)

    # Итоговые баллы
    points = 0.35 * volume_index + 0.25 * deals_index + 0.25 * bank_index + 0.15 * conversion_index
    return round(points, 1)


def calculate_conversion_percent(submitted: int, approved: int) -> float:
    if submitted == 0:
        return 0.0
    return (approved / submitted) * 100


def calculate_progress_percent(score: float, level: str, gold_from: float, black_from: float) -> float:
    if level == "Silver":
        return round(min((score / gold_from) * 100, 100), 2)
    if level == "Gold":
        return round(min((score / black_from) * 100, 100), 2)
    return 100.0
