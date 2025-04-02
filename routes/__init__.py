# Import all routes to be used in the main app
from .landlord_routes import router as landlord_router
from .property_routes import router as property_router
from .room_routes import router as room_router
from .tenant_routes import router as tenant_router
from .payment_routes import router as payment_router
from .electricity_routes import router as electricity_router