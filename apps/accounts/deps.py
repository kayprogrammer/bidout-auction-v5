from ninja.security import HttpBearer, APIKeyHeader

from apps.common.models import GuestUser

from .auth import Authentication


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


class ClientGuest(APIKeyHeader):
    param_name = "GuestUserId"

    async def authenticate(self, request, key):
        guest = await GuestUser.objects.get_or_none(id=key)
        return guest


class ClientUser(HttpBearer):
    async def authenticate(self, request, token):
        if token:
            user = await Authentication.decodeAuthorization(token)
            if not user:
                raise RequestError(
                    err_msg="Auth Token is Invalid or Expired!", status_code=401
                )
            return user
        return None
