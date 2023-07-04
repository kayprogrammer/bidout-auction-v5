from django.utils import timezone
from ninja.security import HttpBearer, APIKeyHeader
from apps.accounts.auth import Authentication
from apps.accounts.models import User, Jwt
from apps.listings.models import Category, Listing
from apps.common.models import File, GuestUser
from apps.common.exceptions import RequestError

from datetime import timedelta
from uuid import UUID


class AuthUser(HttpBearer):
    async def authenticate(self, request, token):
        if not token:
            raise RequestError(err_msg="Auth Bearer not provided!", status_code=401)

        user = await Authentication.decodeAuthorization(token)
        if not user:
            raise RequestError(
                err_msg="Auth Token is Invalid or Expired!", status_code=401
            )
        return user


class GuestClient(APIKeyHeader):
    param_name = "GuestUserId"

    async def authenticate(self, request, key):
        guest = await GuestUser.objects.get_or_none(id=is_uuid(key))
        return guest


def is_uuid(value):
    try:
        return str(UUID(value))
    except:
        return None


def is_int(value):
    if not value:
        return None
    try:
        return int(value)
    except:
        raise RequestError(err_msg="Invalid Quantity params", status_code=422)


# Test Utils
class TestUtil:
    def new_user():
        user_dict = {
            "first_name": "Test",
            "last_name": "Name",
            "email": "test@example.com",
        }
        user = User(**user_dict)
        user.set_password("testpassword")
        user.save()
        return user

    def verified_user():
        user_dict = {
            "first_name": "Test",
            "last_name": "Verified",
            "email": "testverifieduser@example.com",
            "is_email_verified": True,
        }
        user = User(**user_dict)
        user.set_password("testpassword")
        user.save()
        return user

    def another_verified_user():
        create_user_dict = {
            "first_name": "AnotherTest",
            "last_name": "UserVerified",
            "email": "anothertestverifieduser@example.com",
            "is_email_verified": True,
        }
        user = User(**create_user_dict)
        user.set_password("anothertestverifieduser123")
        user.save()
        return user

    def jwt_obj(verified_user):
        access = Authentication.create_access_token({"user_id": str(verified_user.id)})
        refresh = Authentication.create_refresh_token()
        jwt = Jwt.objects.create(
            user_id=verified_user.id, access=access, refresh=refresh
        )
        return jwt

    def create_listing(verified_user):
        # Create Category
        category = Category.objects.create(name="TestCategory")

        # Create File
        file = File.objects.create(resource_type="image/jpeg")

        # Create Listing
        listing_dict = {
            "auctioneer_id": verified_user.id,
            "name": "New Listing",
            "desc": "New description",
            "category": category,
            "price": 1000.00,
            "closing_date": timezone.now() + timedelta(days=1),
            "image_id": file.id,
        }
        listing = Listing.objects.create(**listing_dict)
        return {"user": verified_user, "listing": listing, "category": category}
