# import logging
# from functools import wraps

# from django.http import JsonResponse
# from ninja import HttpError
# import requests

# from core.infrastructure.django_apps.customers.models import (
#     Employee,
#     LevelBenefit,
#     RatingConfig,
#     UserModels,
# )

# logger = logging.getLogger(__name__)

# def handle_service_errors(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         try:
#             return func(*args, **kwargs)
#         except UserModels.DoesNotExist:
#             error_msg = f"User with ID {kwargs.get('id')} not found"
#             logger.error(error_msg)
#             raise HttpError(404, {"error": error_msg})
#         except Employee.DoesNotExist:
#             error_msg = f"Employee for user {kwargs.get('id')} not found"
#             logger.error(error_msg)
#             raise HttpError(404, {"error": error_msg})
#         except RatingConfig.DoesNotExist:
#             error_msg = "Active rating config not found"
#             logger.error(error_msg)
#             raise HttpError(500, {"error": error_msg})
#         except LevelBenefit.DoesNotExist:
#             error_msg = "Level benefit for next level not found"
#             logger.warning(error_msg)  # Предупреждение, а не критическая ошибка
#             # Продолжаем выполнение с пустым financial_forecast
#             return _create_response_with_empty_forecast(args[1], kwargs['id'])
#         except requests.exceptions.ConnectionError:
#             error_msg = "Cannot connect to Go service. Check if service is running."
#             logger.critical(error_msg)
#             raise HttpError(503, {"error": error_msg})
#         except requests.exceptions.Timeout:
#             error_msg = "Go service timeout"
#             logger.warning(error_msg)
#             raise HttpError(504, {"error": error_msg})
#         except requests.exceptions.RequestException as e:
#             error_msg = f"Request error to Go service: {str(e)}"
#             logger.error(error_msg)
#             raise HttpError(500, {"error": error_msg})
#         except Exception as e:
#             error_msg = f"Unexpected error: {str(e)}"
#             logger.exception(error_msg)
#             raise HttpError(500, {"error": error_msg})
#     return wrapper
