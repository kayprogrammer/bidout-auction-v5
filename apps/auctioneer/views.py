from ninja.router import Router
from .schemas import (
    CreateListingResponseSchema,
    CreateListingSchema,
    ProfileResponseSchema,
    UpdateListingSchema,
    UpdateProfileResponseSchema,
    UpdateProfileSchema,
)
from apps.common.exceptions import RequestError
from apps.common.models import File
from apps.common.utils import AuthUser
from apps.listings.models import Category, Listing
from asgiref.sync import sync_to_async

from apps.listings.schemas import BidsResponseSchema, ListingsResponseSchema

auctioneer_router = Router(tags=["Auctioneer"], auth=AuthUser())


@auctioneer_router.get(
    "",
    summary="Get Profile",
    description="This endpoint gets the current user's profile.",
    response=ProfileResponseSchema,
)
async def retrieve_profile(request):
    user = await request.auth
    return {"message": "User details fetched!", "data": user}


@auctioneer_router.put(
    "",
    summary="Update Profile",
    description="This endpoint updates an authenticated user's profile. Note: use the returned upload_url to upload avatar to cloudinary",
    response=UpdateProfileResponseSchema,
)
async def update_profile(request, data: UpdateProfileSchema):
    user = await request.auth
    file_type = data.file_type
    data = data.dict()
    if file_type:
        # Create file object
        file = user.avatar
        if not file:
            file = await File.objects.acreate(resource_type=file_type)
        data.update({"avatar": file})
        data.pop("file_type")
    for attr, value in data.items():
        setattr(user, attr, value)
    await user.asave()
    return {"message": "User updated!", "data": user}


@auctioneer_router.get(
    "/listings/",
    summary="Retrieve all listings by the current user",
    description="This endpoint retrieves all listings by the current user",
    response=ListingsResponseSchema,
)
async def retrieve_listings(request, quantity: int = None):
    user = await request.auth
    listings = await sync_to_async(list)(
        Listing.objects.filter(auctioneer=user).select_related(
            "auctioneer", "auctioneer__avatar", "category", "image"
        )
    )
    if quantity:
        # Retrieve based on amount
        listings = listings[:quantity]

    return {"message": "Auctioneer Listings fetched", "data": listings}


@auctioneer_router.post(
    "/listings/",
    summary="Create a listing",
    description="This endpoint creates a new listing. Note: Use the returned file_upload_data to upload image to cloudinary",
    response={201: CreateListingResponseSchema},
)
async def create_listing(request, data: CreateListingSchema):
    client = await request.auth
    category = data.category

    if not category == "other":
        category = await Category.objects.get_or_none(slug=category)
        if not category:
            # Return a data validation error
            raise RequestError(
                err_msg="Invalid entry",
                data={"category": "Invalid category"},
                status_code=422,
            )
    else:
        category = None

    data = data.dict()
    data.update(
        {
            "auctioneer": client,
            "category": category,
        }
    )

    # Create file object
    file = await File.objects.acreate(resource_type=data["file_type"])
    data.update({"image": file})
    data.pop("file_type")
    listing = await Listing.objects.acreate(**data)

    return {
        "message": "Listing created successfully",
        "data": listing,
    }


@auctioneer_router.patch(
    "/listings/{slug}/",
    summary="Update a listing",
    description="This endpoint update a particular listing. Do note that only file type is optional.",
    response=CreateListingResponseSchema,
)
async def update_listing(request, slug: str, data: UpdateListingSchema):
    user = await request.auth
    category = data.category

    listing = await Listing.objects.select_related(
        "auctioneer", "auctioneer__avatar", "category", "image"
    ).get_or_none(slug=slug)
    if not listing:
        raise RequestError(err_msg="Listing does not exist!", status_code=404)

    if user != listing.auctioneer:
        raise RequestError(err_msg="This listing doesn't belong to you!")

    # Remove keys with values of None
    data = data.dict()
    data = {k: v for k, v in data.items() if v not in (None, "")}

    if category:
        if not category == "other":
            category = await Category.objects.get_or_none(slug=category)
            if not category:
                # Return a data validation error
                raise RequestError(
                    err_msg="Invalid entry",
                    data={"category": "Invalid category"},
                    status_code=422,
                )
        else:
            category = None

        data["category"] = category

    file_type = data.get("file_type")
    if file_type:
        file = listing.image
        if not file:
            file = await File.objects.acreate(resource_type=file_type)
        data.update({"image_id": file.id})
    data.pop("file_type", None)

    for attr, value in data.items():
        setattr(listing, attr, value)
    await listing.asave()
    return {"message": "Listing updated successfully", "data": listing}


@auctioneer_router.get(
    "/listings/{slug}/bids/",
    summary="Retrieve all bids in a listing (current user)",
    description="This endpoint retrieves all bids in a particular listing by the current user.",
    response=BidsResponseSchema,
)
async def retrieve_bids(request, slug: str):
    user = await request.auth
    # Get listing by slug
    listing = (
        await Listing.objects.select_related(
            "auctioneer", "auctioneer__avatar", "category", "image"
        )
        .prefetch_related("bids", "bids__user")
        .get_or_none(slug=slug)
    )
    if not listing:
        raise RequestError(err_msg="Listing does not exist!", status_code=404)

    # Ensure the current user is the listing's owner
    if user.id != listing.auctioneer_id:
        raise RequestError(err_msg="This listing doesn't belong to you!")

    bids = listing.bids.all()
    return {
        "message": "Listing Bids fetched",
        "data": {"listing": listing.name, "bids": list(bids)},
    }
