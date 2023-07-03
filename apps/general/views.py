from ninja import Router

from .schemas import (
    ReviewsResponseSchema,
    SiteDetailResponseSchema,
    SubscriberResponseSchema,
    SubscriberSchema,
)
from .models import Review, SiteDetail, Subscriber
from asgiref.sync import sync_to_async

general_router = Router(tags=["General"])


@general_router.get(
    "/site-detail/",
    response=SiteDetailResponseSchema,
    summary="Retrieve site details",
    description="This endpoint retrieves few details of the site/application",
)
async def retrieve_site_details(request):
    sitedetail, created = await SiteDetail.objects.aget_or_create()
    return {"message": "Site Details fetched", "data": sitedetail}


@general_router.post(
    "/subscribe/",
    response={201: SubscriberResponseSchema},
    summary="Add a subscriber",
    description="This endpoint creates a newsletter subscriber in our application",
)
async def subscribe(request, data: SubscriberSchema):
    email = data.email
    await Subscriber.objects.aget_or_create(email=email)
    return {"message": "Subscription successful", "data": {"email": email}}


@general_router.get(
    "/reviews/",
    response=ReviewsResponseSchema,
    summary="Retrieve site reviews",
    description="This endpoint retrieves a few reviews of the application",
)
async def retrieve_reviews(request):
    reviews = (
        await sync_to_async(list)(
            Review.objects.filter(show=True).select_related("reviewer")
        )
    )[:3]
    return {"message": "Reviews fetched", "data": reviews}
