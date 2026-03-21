import logging

from ninja.errors import HttpError
import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from ninja import Router

from core.api.v1.customers.handlers import user_auth
from core.api.v1.status.service import calculate_index, create_go_service_payload, get_level
from core.api.v1.status.shemas import (
    CalculateInSchema,
    GoServiceOutSchema,
)
from core.infrastructure.django_apps.customers.models import Employee, UserModels

GO_SERVICE_URL = getattr(settings, 'GO_SERVICE_URL', 'http://go-calc-service:8080')
GO_SERVICE_TIMEOUT = getattr(settings, 'GO_SERVICE_TIMEOUT', 10)
router = Router(tags=["Status"])


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



logger = logging.getLogger(__name__)

def calculate_conversion_percent(submitted: int, approved: int) -> float:
    if submitted == 0:
        return 0.0
    return (approved / submitted) * 100

# @router.get("/test", auth=user_auth, response=GoServiceOutSchema)
def build_go_payload(employee: Employee) -> dict:
    return {
        "fact_volume": employee.volume,
        "plan_volume": 15,  # или employee.volume_plan, если уже корректно заполнено
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
        "max_index": 120.0,
        "weights": {
            "volume": 0.3,
            "deals": 0.25,
            "bank_share": 0.2,
            "conversion": 0.25,
        },
        "thresholds": {
            "gold_from": 80.0,
            "black_from": 95.0,
        },
    }


@router.get("/test", response=GoServiceOutSchema)
def get_status_test(request, id: int):
    try:
        employee = get_object_or_404(Employee, user=id)

        logger.info("Calculating rating for employee %s (%s)", employee.id, employee.name)

        if employee.approved_requests > employee.submitted_requests:
            raise Exception(
                f"Invalid employee data: approved_requests ({employee.approved_requests}) "
                f"cannot exceed submitted_requests ({employee.submitted_requests})"
            )

        go_request_data = build_go_payload(employee)
        # logger.info("Go payload: %s", go_request_data.dict())
        go_response = requests.post(
            f"{GO_SERVICE_URL}/api/v1/calculate",
            json=go_request_data,
            timeout=GO_SERVICE_TIMEOUT,
        )
        print(go_response)
        if go_response.status_code != 200:
            error_msg = (
                f"Go service returned {go_response.status_code}: {go_response.text}"
            )
            logger.error(error_msg)
            raise Exception(error_msg)

        result = go_response.json()

        employee.points = result["score"]
        employee.level = result["level"]
        employee.save()

        logger.info(
            "Updated employee %s: score=%s, level=%s",
            employee.id,
            result["score"],
            result["level"],
        )

        return result

    except UserModels.DoesNotExist:
        error_msg = f"User with ID {id} not found"
        logger.error(error_msg)
        raise Exception(error_msg)

    except Employee.DoesNotExist:
        error_msg = f"Employee for user {id} not found"
        logger.error(error_msg)
        raise Exception(error_msg)

    except requests.exceptions.ConnectionError:
        error_msg = "Cannot connect to Go service. Check if service is running."
        logger.error(error_msg)
        raise Exception(error_msg)

    except requests.exceptions.Timeout:
        error_msg = "Go service timeout"
        logger.error(error_msg)
        raise Exception(error_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"Request error to Go service: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.exception(error_msg)
        raise Exception(error_msg)