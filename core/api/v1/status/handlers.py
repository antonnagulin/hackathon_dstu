from ninja import Router

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
        "points": points,
        "progress_percent": round(points / next_level_threshold * 100, 1),
        "points_to_next_level": max(next_level_threshold - points, 0),
    }