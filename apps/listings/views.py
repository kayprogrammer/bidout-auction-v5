from django.db.models import Prefetch, Q
from ninja.router import Router
from ninja.responses import Response

from apps.common.exceptions import RequestError
from apps.common.models import GuestUser
from apps.common.utils import (
    GuestClient,
    AuthUser,
    is_int,
)
from .schemas import (
    BidResponseSchema,
    BidsResponseSchema,
    CategoriesResponseSchema,
    CreateBidSchema,
    ListingsResponseSchema,
    ListingResponseSchema,
    ListingDetailDataSchema,
    AddOrRemoveWatchlistResponseSchema,
    AddOrRemoveWatchlistSchema,
)
from .models import Bid, Category, Listing, WatchList
from asgiref.sync import sync_to_async

listings_router = Router(tags=["Listings"])


@listings_router.get(
    "",
    summary="Retrieve all listings",
    description="This endpoint retrieves all listings",
    response=ListingsResponseSchema,
    auth=[AuthUser(), GuestClient()],
)
async def retrieve_listings(request, quantity: int = None):
    client = await request.auth
    listings = await sync_to_async(list)(
        Listing.objects.select_related(
            "auctioneer", "auctioneer__avatar", "category", "image"
        ).prefetch_related(
            Prefetch(
                "watchlists",
                queryset=WatchList.objects.filter(
                    Q(user_id=client.id if client else None)
                    | Q(guest_id=client.id if client else None)
                ),
                to_attr="watchlist",
            )
        )
    )
    if quantity:
        # Retrieve based on amount
        listings = listings[:quantity]
    return {"message": "Listings fetched", "data": listings}


@listings_router.get(
    "/detail/{slug}/",
    summary="Retrieve listing's detail",
    description="This endpoint retrieves detail of a listing",
    response=ListingResponseSchema,
)
async def retrieve_listing_detail(request, slug: str):
    listing = await Listing.objects.select_related(
        "auctioneer", "auctioneer__avatar", "category", "image"
    ).get_or_none(slug=slug)
    if not listing:
        raise RequestError(err_msg="Listing does not exist!", status_code=404)

    related_listings = (
        await sync_to_async(list)(
            Listing.objects.filter(category_id=listing.category_id)
            .exclude(id=listing.id)
            .select_related("auctioneer", "auctioneer__avatar", "category", "image")
        )
    )[:3]

    data = ListingDetailDataSchema(listing=listing, related_listings=related_listings)
    return {"message": "Listing details fetched", "data": data}


@listings_router.get(
    "/watchlist/",
    summary="Retrieve all listings by users watchlist",
    description="This endpoint retrieves all listings in user's watchlist",
    auth=[AuthUser(), GuestClient()],
    response=ListingsResponseSchema,
)
async def retrieve_watchlist(request):
    client = await request.auth
    watchlists = []
    if client:
        watchlists = await sync_to_async(list)(
            WatchList.objects.filter(
                Q(user_id=client.id) | Q(guest_id=client.id)
            ).select_related(
                "user",
                "guest",
                "listing",
                "listing__auctioneer",
                "listing__auctioneer__avatar",
                "listing__category",
                "listing__image",
            )
        )
    data = [
        {
            "auctioneer": watchlist.listing.auctioneer,
            "watchlist": True,
            "time_left_seconds": watchlist.listing.time_left_seconds,
            **watchlist.listing.dict(),
        }
        for watchlist in watchlists
    ]
    return {"message": "Watchlist Listings fetched", "data": data}


@listings_router.post(
    "/watchlist/",
    summary="Add or Remove listing from a users watchlist",
    description="""
    This endpoint adds or removes a listing from a user's watchlist, authenticated or not....
    As a guest, ensure to store guestuser_id in localstorage and keep passing it to header 'guestuserid' in subsequent requests
    """,
    response={201: AddOrRemoveWatchlistResponseSchema},
    auth=[AuthUser(), GuestClient()],
)
async def post(request, data: AddOrRemoveWatchlistSchema):
    client = await request.auth

    listing = await Listing.objects.get_or_none(slug=data.slug)
    if not listing:
        raise RequestError(err_msg="Listing does not exist!", status_code=404)

    if not client:
        client = await GuestUser.objects.acreate()

    resp_message = "Listing added to user watchlist"
    status_code = 201
    if hasattr(client, "email"):
        watchlist, created = await WatchList.objects.aget_or_create(
            listing_id=listing.id, user_id=client.id
        )
        if not created:
            await watchlist.adelete()
            resp_message = "Listing removed from user watchlist"
            status_code = 200
    else:
        watchlist, created = await WatchList.objects.aget_or_create(
            listing_id=listing.id, guest_id=client.id
        )
        if not created:
            await watchlist.adelete()
            resp_message = "Listing removed from user watchlist"
            status_code = 200

    guestuser_id = client.id if isinstance(client, GuestUser) else None
    return Response(
        {
            "message": resp_message,
            "data": {"guestuser_id": guestuser_id},
        },
        status=status_code,
    )


@listings_router.get(
    "/categories/",
    summary="Retrieve all categories",
    description="This endpoint retrieves all categories",
    response=CategoriesResponseSchema,
)
async def retrieve_categories(request):
    categories = await sync_to_async(list)(Category.objects.all())
    return {"message": "Categories fetched", "data": categories}


@listings_router.get(
    "/categories/{slug}/",
    summary="Retrieve all listings by category",
    description="This endpoint retrieves all listings in a particular category. Use slug 'other' for category other",
    auth=[AuthUser(), GuestClient()],
    response=ListingsResponseSchema,
)
async def retrieve_category_listings(request, slug: str):
    client = await request.auth

    # listings with category 'other' have category column as null
    category = None
    if slug != "other":
        category = await Category.objects.get_or_none(slug=slug)
        if not category:
            raise RequestError(err_msg="Invalid category", status_code=404)

    listings = await sync_to_async(list)(
        Listing.objects.filter(category=category)
        .select_related("auctioneer", "auctioneer__avatar", "category", "image")
        .prefetch_related(
            Prefetch(
                "watchlists",
                queryset=WatchList.objects.filter(
                    Q(user_id=client.id if client else None)
                    | Q(guest_id=client.id if client else None)
                ),
                to_attr="watchlist",
            )
        )
    )
    return {"message": "Category Listings fetched", "data": listings}


@listings_router.get(
    "/detail/{slug}/bids/",
    summary="Retrieve bids in a listing",
    description="This endpoint retrieves at most 3 bids from a particular listing.",
    response=BidsResponseSchema,
)
async def retrieve_listing_bids(request, slug: str):
    listing = (
        await Listing.objects.select_related(
            "auctioneer", "auctioneer__avatar", "category", "image"
        )
        .prefetch_related(
            Prefetch(
                "bids",
                queryset=Bid.objects.select_related("user", "user__avatar"),
                to_attr="all_bids",
            )
        )
        .get_or_none(slug=slug)
    )
    if not listing:
        raise RequestError(err_msg="Listing does not exist!", status_code=404)

    bids = listing.all_bids[:3]
    return {
        "message": "Listing Bids fetched",
        "data": {"listing": listing.name, "bids": bids},
    }


@listings_router.post(
    "/detail/{slug}/bids/",
    summary="Add a bid to a listing",
    description="This endpoint adds a bid to a particular listing.",
    response={201: BidResponseSchema},
    auth=AuthUser(),
)
async def create_bid(request, slug: str, data: CreateBidSchema):
    user = await request.auth

    listing = (
        await Listing.objects.select_related(
            "auctioneer", "auctioneer__avatar", "category", "image"
        )
        .prefetch_related("bids")
        .get_or_none(slug=slug)
    )
    if not listing:
        raise RequestError(err_msg="Listing does not exist!", status_code=404)

    amount = data.amount

    bids_count = listing.bids_count
    if user.id == listing.auctioneer_id:
        raise RequestError(err_msg="You cannot bid your own product!", status_code=403)
    elif not listing.active:
        raise RequestError(err_msg="This auction is closed!", status_code=410)
    elif listing.time_left < 1:
        raise RequestError(
            err_msg="This auction is expired and closed!", status_code=410
        )
    elif amount < listing.price:
        raise RequestError(err_msg="Bid amount cannot be less than the bidding price!")
    elif amount <= listing.highest_bid:
        raise RequestError(err_msg="Bid amount must be more than the highest bid!")

    bid = await Bid.objects.select_related("user", "user__avatar").get_or_none(
        user_id=user.id, listing_id=listing.id
    )
    if bid:
        # Update existing bid
        bid.amount = amount
        await bid.asave()
    else:
        # Create new bid
        bids_count += 1
        bid = await Bid.objects.acreate(user=user, listing=listing, amount=amount)
    listing.bids_count = bids_count
    listing.highest_bid = amount
    await listing.asave()
    return {"message": "Bid added to listing", "data": bid}
