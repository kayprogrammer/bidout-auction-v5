from ninja import Router
from apps.common.utils import AuthUser, GuestClient, is_uuid

from apps.common.schemas import ResponseSchema
from .schemas import (
    LoginUserSchema,
    RefreshTokensSchema,
    RegisterResponseSchema,
    RegisterUserSchema,
    RequestOtpSchema,
    SetNewPasswordSchema,
    TokensResponseSchema,
    VerifyOtpSchema,
)

from .auth import Authentication
from .emails import Util

from .models import Jwt, Otp, User
from apps.common.models import GuestUser
from apps.listings.models import WatchList

from apps.common.exceptions import RequestError
from asgiref.sync import sync_to_async

auth_router = Router(tags=["Auth"])


@auth_router.post(
    "/register/",
    summary="Register a new user",
    description="This endpoint registers new users into our application",
    response={201: RegisterResponseSchema},
)
async def register(request, data: RegisterUserSchema):
    # Check for existing user
    existing_user = await User.objects.get_or_none(email=data.email)
    if existing_user:
        raise RequestError(
            err_msg="Invalid Entry",
            status_code=422,
            data={"email": "Email already registered!"},
        )

    # Create user
    user = await User.objects.create_user(**data.dict())

    # Send verification email
    await Util.send_activation_otp(user)

    return {
        "message": "Registration successful",
        "data": {"email": data.email},
    }


@auth_router.post(
    "/verify-email/",
    summary="Verify a user's email",
    description="This endpoint verifies a user's email",
    response=ResponseSchema,
)
async def verify_email(request, data: VerifyOtpSchema):
    email = data.email
    otp_code = data.otp

    user = await User.objects.get_or_none(email=email)

    if not user:
        raise RequestError(err_msg="Incorrect Email", status_code=404)

    if user.is_email_verified:
        return {"message": "Email already verified"}

    otp = await Otp.objects.get_or_none(user=user)
    if not otp or otp.code != otp_code:
        raise RequestError(err_msg="Incorrect Otp", status_code=404)
    if otp.check_expiration():
        raise RequestError(err_msg="Expired Otp")

    user.is_email_verified = True
    await user.asave()
    await otp.adelete()

    # Send welcome email
    Util.welcome_email(user)
    return {
        "message": "Account verification successful",
    }


@auth_router.post(
    "/resend-verification-email/",
    summary="Resend Verification Email",
    description="This endpoint resends new otp to the user's email",
    response=ResponseSchema,
)
async def resend_verification_email(request, data: RequestOtpSchema):
    email = data.email
    user = await User.objects.get_or_none(email=email)
    if not user:
        raise RequestError(err_msg="Incorrect Email", status_code=404)
    if user.is_email_verified:
        return {"message": "Email already verified"}

    # Send verification email
    await Util.send_activation_otp(user)
    return {"message": "Verification email sent"}


@auth_router.post(
    "/send-password-reset-otp/",
    summary="Send Password Reset Otp",
    description="This endpoint sends new password reset otp to the user's email",
    response=ResponseSchema,
)
async def send_password_reset_otp(request, data: RequestOtpSchema):
    email = data.email

    user = await User.objects.get_or_none(email=email)
    if not user:
        raise RequestError(err_msg="Incorrect Email", status_code=404)

    # Send password reset email
    await Util.send_password_change_otp(user)
    return {"message": "Password otp sent"}


@auth_router.post(
    "/set-new-password/",
    summary="Set New Password",
    description="This endpoint verifies the password reset otp",
    response=ResponseSchema,
)
async def set_new_password(request, data: SetNewPasswordSchema):
    email = data.email
    code = data.otp
    password = data.password

    user = await User.objects.get_or_none(email=email)
    if not user:
        raise RequestError(err_msg="Incorrect Email", status_code=404)

    otp = await Otp.objects.get_or_none(user=user)
    if not otp or otp.code != code:
        raise RequestError(err_msg="Incorrect Otp", status_code=404)

    if otp.check_expiration():
        raise RequestError(err_msg="Expired Otp")

    user.set_password(password)
    await user.asave()

    # Send password reset success email
    Util.password_reset_confirmation(user)
    return {"message": "Password reset successful"}


@auth_router.post(
    "/login/",
    summary="Login a user",
    description="This endpoint generates new access and refresh tokens for authentication",
    response={201: TokensResponseSchema},
    auth=GuestClient(),
)
async def login(request, data: LoginUserSchema):
    email = data.email
    password = data.password

    user = await User.objects.get_or_none(email=email)
    if not user or not user.check_password(password):
        raise RequestError(err_msg="Invalid credentials", status_code=401)

    if not user.is_email_verified:
        raise RequestError(err_msg="Verify your email first", status_code=401)
    await Jwt.objects.filter(user_id=user.id).adelete()

    # Create tokens and store in jwt model
    access = Authentication.create_access_token({"user_id": str(user.id)})
    refresh = Authentication.create_refresh_token()
    await Jwt.objects.acreate(user_id=user.id, access=access, refresh=refresh)

    # Move all guest user watchlists to the authenticated user watchlists
    guest_id = is_uuid((await request.auth))
    if guest_id:
        guest_user_watchlists_ids = await sync_to_async(list)(
            WatchList.objects.filter(guest_id=guest_id)
            .exclude(
                listing_id__in=WatchList.objects.filter(user=user)
                .select_related("user", "guest")
                .values_list("listing_id", flat=True)
            )
            .select_related("user", "listing")
            .values_list("listing_id", flat=True)
        )
        if len(guest_user_watchlists_ids) > 0:
            data_to_create = [
                WatchList(user_id=user.id, listing_id=listing_id)
                for listing_id in guest_user_watchlists_ids
            ]
            await WatchList.objects.abulk_create(data_to_create)
            await GuestUser.objects.filter(id=guest_id).adelete()

    return {
        "message": "Login successful",
        "data": {"access": access, "refresh": refresh},
    }


@auth_router.post(
    "/refresh/",
    summary="Refresh tokens",
    description="This endpoint refresh tokens by generating new access and refresh tokens for a user",
    response={201: TokensResponseSchema},
)
async def refresh(request, data: RefreshTokensSchema):
    token = data.refresh
    jwt = await Jwt.objects.get_or_none(refresh=token)

    if not jwt:
        raise RequestError(err_msg="Refresh token does not exist", status_code=404)
    if not Authentication.decode_jwt(token):
        raise RequestError(
            err_msg="Refresh token is invalid or expired", status_code=401
        )

    access = Authentication.create_access_token({"user_id": str(jwt.user_id)})
    refresh = Authentication.create_refresh_token()

    jwt.access = access
    jwt.refresh = refresh
    await jwt.asave()

    return {
        "message": "Tokens refresh successful",
        "data": {"access": access, "refresh": refresh},
    }


@auth_router.get(
    "/logout/",
    summary="Logout a user",
    description="This endpoint logs a user out from our application",
    response=ResponseSchema,
    auth=AuthUser(),
)
async def logout(request):
    await Jwt.objects.filter(user_id=(await request.auth).id).adelete()
    return {"message": "Logout successful"}
