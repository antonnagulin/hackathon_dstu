import requests
from django.shortcuts import get_object_or_404
from ninja import Router, Schema

from core.api.v1.customers.handlers import user_auth
from core.infrastructure.django_apps.customers.models import Employee, UserModels

router = Router(tags=["Status"])

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


@router.get("/profile", auth=user_auth)
def get_prof(request):
    return "Hello world"


@router.get("/", auth=user_auth)
def get_status(request):
    user = request.auth
    model_user = UserModels.objects.get(id=user.user_id)
    emp = model_user.employee

    points = calculate_index(emp)
    level = get_level(points)

    if level == "Silver":
        next_level_threshold = 70
    elif level == "Gold":
        next_level_threshold = 90
    else:
        next_level_threshold = 100

    return {
        "level": level,
        "points": int(points),
        "progress_percent": round(points / next_level_threshold * 100, 1),
        "points_to_next_level": int(max(next_level_threshold - points, 0)),
    }


@router.post("/simulate")
def simulate(
        request,
        data_volume: int,
        data_deals_count: int,
        data_bank_share: int,
        data_approved_requests: int,
        data_submitted_requests: int
    ):
    """
    data = {
        "volume": 12,
        "deals_count": 14,
        "bank_share": 55,
        "approved_requests": 28,
        "submitted_requests": 35
    }
    """
    class TempEmployee:
        volume = data_volume
        deals_count = data_deals_count
        bank_share = data_bank_share
        bank_share_goal = 50
        approved_requests = data_approved_requests
        submitted_requests = data_submitted_requests

        volume_plan = 10
        deals_plan = 10

    temp_emp = TempEmployee()
    points = calculate_index(temp_emp)
    level = get_level(points)

    return {
        "simulated_points": points,
        "simulated_level": level
    }


class CalculateRequest(Schema):
    FactVolume: float
    PlanVolume: float
    FactDeals: int
    PlanDeals: int
    FactBankShare: float
    TargetBankShare: float
    SubmittedApps: int
    ApprovedApps: int
    ConversionPercent: float
    MaxIndex: float
    Weights: dict
    Thresholds: dict

class GoServiceResponse(Schema):
    Score: float
    Level: str
    Breakdown: dict
    NextLevel: dict


@router.get("/test", auth=user_auth, response=GoServiceResponse)
def get_status_test(request):
    user = request.auth
    model_user = UserModels.objects.get(id=user.user_id)
    employee = model_user.employee

    # 2. Конвертируем данные сотрудника в формат для Go‑сервиса
    go_request_data = CalculateRequest(
        FactVolume=employee.volume,
        PlanVolume=employee.volume_plan,
        FactDeals=employee.deals_count,
        PlanDeals=employee.deals_plan,
        FactBankShare=employee.bank_share,
        TargetBankShare=employee.bank_share_goal,
        SubmittedApps=employee.submitted_requests,
        ApprovedApps=employee.approved_requests,
        ConversionPercent=calculate_conversion_percent(
            employee.submitted_requests,
            employee.approved_requests
        ),
        MaxIndex=1.5,  # фиксированное значение или из настроек
        Weights={
            "Volume": 0.3,
            "Deals": 0.25,
            "BankShare": 0.2,
            "Conversion": 0.25
        },
        Thresholds={
            "GoldFrom": 80.0,
            "BlackFrom": 95.0
        }
    )

    # 3. Отправляем запрос в Go‑сервис
    try:
        go_response = requests.post(
            "http://go-calc-service:8080/api/v1/calculate",
            json=go_request_data.dict(),
            timeout=10
        )

        if go_response.status_code == 200:
            result = go_response.json()

            # 4. Обновляем данные сотрудника в базе
            employee.points = result["Score"]
            employee.level = result["Level"]
            employee.save()

            return result
        else:
            raise Exception(f"Go service returned {go_response.status_code}: {go_response.text}")

    except requests.exceptions.RequestException as e:
        raise Exception(f"Connection error to Go service: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing employee calculation: {str(e)}")

def calculate_conversion_percent(submitted: int, approved: int) -> float:
    """Рассчитывает процент конверсии."""
    if submitted == 0:
        return 0.0
    return (approved / submitted) * 100