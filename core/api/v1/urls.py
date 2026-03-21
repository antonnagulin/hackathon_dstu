from ninja import Router

from core.api.v1.customers.handlers import router as customer_router
from core.api.v1.status.handlers import router as status_router
from core.api.v1.status.test import router as test_router

router = Router(tags=["v1"])

router.add_router("customers/", customer_router)
router.add_router("status/", status_router)
router.add_router("test/", test_router)
# router.add_router("booking/", booking_router)
