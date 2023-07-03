from django.conf import settings
from ninja import NinjaAPI
from apps.general.views import general_router


api = NinjaAPI(
    title=settings.SITE_NAME,
    description="A simple bidding API built with Django Ninja Rest Framework",
    version="5.0.0",
    docs_url="/",
    # openapi_extra={
    #     "security": [{"BearerToken": [], "GuestUserID": []}],
    #     "components": {
    #         "securitySchemes": {
    #             "BearerToken": {"type": "http", "scheme": "bearer"},
    #             "GuestUserID": {
    #                 "type": "apiKey",
    #                 "in": "header",
    #                 "name": "guestUserID",
    #                 "description": "For guest watchlists. Get ID from '/api/v3/listings/watchlist' POST endpoint",
    #             },
    #         }
    #     },
    # },
)

api.add_router("/api/v5/general/", general_router)
