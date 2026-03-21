import logging

import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from ninja import Router

from core.api.v1.customers.handlers import user_auth
from core.api.v1.status.service import (
    calculate_conversion_percent,
    calculate_progress_percent,
)
from core.api.v1.status.shemas import (
    StatusScreenSchema,
)
from core.infrastructure.django_apps.customers.models import (
    Employee,
    LevelBenefit,
    RatingConfig,
    UserModels,
)

GO_SERVICE_URL = getattr(settings, 'GO_SERVICE_URL', 'http://go-calc-service:8080')
GO_SERVICE_TIMEOUT = getattr(settings, 'GO_SERVICE_TIMEOUT', 10)
router = Router(tags=["Status"])


logger = logging.getLogger(__name__)




def build_go_payload(employee: Employee) -> dict:
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



@router.get("/", response=StatusScreenSchema,  auth=user_auth)
def get_status(request):
    user = request.auth
    model_user = UserModels.objects.get(id=user.user_id)
    employee = model_user.employee
    try:
        config = RatingConfig.objects.get(is_active=True)

        logger.info("Calculating rating for employee %s (%s)", employee.id, employee.name)

        if employee.volume_plan <= 0:
            raise Exception("Invalid employee data: volume_plan must be greater than 0")
        if employee.deals_plan <= 0:
            raise Exception("Invalid employee data: deals_plan must be greater than 0")
        if employee.bank_share_goal <= 0:
            raise Exception("Invalid employee data: bank_share_goal must be greater than 0")
        if employee.approved_requests > employee.submitted_requests:
            raise Exception(
                f"Invalid employee data: approved_requests ({employee.approved_requests}) "
                f"cannot exceed submitted_requests ({employee.submitted_requests})"
            )

        go_request_data = {
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
                employee.approved_requests
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

        go_response = requests.post(
            f"{GO_SERVICE_URL}/api/v1/calculate",
            json=go_request_data,
            timeout=GO_SERVICE_TIMEOUT,
        )

        if go_response.status_code != 200:
            error_msg = (
                f"Go service returned {go_response.status_code}: "
                f"{go_response.text}"
            )
            logger.error(error_msg)
            raise Exception(error_msg)

        result = go_response.json()

        employee.points = result["score"]
        employee.level = result["level"]
        employee.save()

        next_level = result["next_level"].get("next_level")
        financial_forecast = None

        if next_level:
            benefit = LevelBenefit.objects.get(level=next_level, is_active=True)

            financial_forecast = {
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
        else:
            financial_forecast = {
                "next_level": None,
                "income_growth_year": 0,
                "mortgage_saving_year": 0,
                "other_benefit_year": 0,
                "total_benefit_year": 0,
                "title": "Максимальный уровень достигнут",
                "description": "Дополнительные привилегии уже активны",
            }

        mobile_response = {
            "employee_id": employee.id,
            "name": employee.name,
            "level": result["level"],
            "score": result["score"],
            "next_level": next_level,
            "points_to_next_level": result["next_level"].get("missing_score"),
            "progress_percent": calculate_progress_percent(
                score=result["score"],
                level=result["level"],
                gold_from=config.gold_from,
                black_from=config.black_from,
            ),
            "financial_forecast": financial_forecast,
        }

        logger.info(
            "Updated employee %s: score=%s, level=%s",
            employee.id,
            result["score"],
            result["level"],
        )

        return mobile_response

    except UserModels.DoesNotExist:
        error_msg = f"User with ID {id} not found"
        logger.error(error_msg)
        raise Exception(error_msg)

    except Employee.DoesNotExist:
        error_msg = f"Employee for user {id} not found"
        logger.error(error_msg)
        raise Exception(error_msg)

    except RatingConfig.DoesNotExist:
        error_msg = "Active rating config not found"
        logger.error(error_msg)
        raise Exception(error_msg)

    except LevelBenefit.DoesNotExist:
        error_msg = "Level benefit for next level not found"
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