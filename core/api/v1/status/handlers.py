import logging

import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from ninja import Router

from core.api.v1.customers.handlers import user_auth
from core.api.v1.status.service import calculate_index, get_level
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


# @router.get("/test", auth=user_auth, response=GoServiceOutSchema)
@router.get("/test", response=GoServiceOutSchema)
def get_status_test(request ,id: int):
    # user = request.auth

    try:
        # model_user = UserModels.objects.get(id=user.user_id)
        employee = get_object_or_404(Employee, user=id)

        logger.info(f"Calculating rating for employee {employee.id} ({employee.name})")


        go_request_data = CalculateInSchema(
            FactVolume=employee.volume,
            PlanVolume=15,
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
            MaxIndex=120.0,  
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

        print(go_request_data.dict())
        go_response = requests.post(
            f"{GO_SERVICE_URL}/api/v1/calculate",
            json=go_request_data.dict(),
            timeout=GO_SERVICE_TIMEOUT
        )

        if go_response.status_code == 200:
            result = go_response.json()

            employee.points = result["Score"]
            employee.level = result["Level"]
            employee.save()

            logger.info(
                f"Updated employee {employee.id}: "
                f"Score={result['Score']}, Level={result['Level']}"
            )

            return result

        else:
            error_msg = (
                f"Go service returned {go_response.status_code}: "
                f"{go_response.text}"
            )
            logger.error(error_msg)
            raise Exception(error_msg)

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



def calculate_conversion_percent(submitted: int, approved: int) -> float:
    """Рассчитывает процент конверсии."""
    if submitted == 0:
        return 0.0
    return (approved / submitted) * 100
