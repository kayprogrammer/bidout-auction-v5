from django.conf import settings
from ninja import NinjaAPI
from ninja.responses import Response
from ninja.errors import ValidationError, AuthenticationError
from apps.common.exceptions import RequestError, request_errors, validation_errors
from apps.general.views import general_router
from apps.accounts.views import auth_router
from apps.listings.views import listings_router
from apps.auctioneer.views import auctioneer_router

api = NinjaAPI(
    title=settings.SITE_NAME,
    description="A simple bidding API built with Django Ninja Rest Framework",
    version="5.0.0",
    docs_url="/",
)

api.add_router("/api/v5/general/", general_router)
api.add_router("/api/v5/auth/", auth_router)
api.add_router("/api/v5/listings/", listings_router)
api.add_router("/api/v5/auctioneer/", auctioneer_router)


@api.exception_handler(ValidationError)
def validation_exc_handler(request, exc):
    return validation_errors(exc)


@api.exception_handler(RequestError)
def request_exc_handler(request, exc):
    return request_errors(exc)


@api.exception_handler(AuthenticationError)
def request_exc_handler(request, exc):
    return Response({"status": "failure", "message": "Unauthourized User"}, status=401)
