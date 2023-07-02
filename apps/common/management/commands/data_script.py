from django.conf import settings
from django.utils import timezone
from apps.accounts.models import User
from apps.general.models import SiteDetail, Review
from apps.listings.models import Category, Listing
from apps.common.models import File
from apps.common.file_processors import FileProcessor

from pathlib import Path
from .mappings import listing_mappings, category_mappings, file_mappings
from datetime import timedelta
from typing import List
from uuid import UUID
from asgiref.sync import sync_to_async
import os, random

CURRENT_DIR = Path(__file__).resolve().parent
test_images_directory = os.path.join(CURRENT_DIR, "images")


class CreateData(object):
    def __init__(self) -> None:
        pass

    async def initialize(self) -> None:
        await self.create_superuser()
        auctioneer = await self.create_auctioneer()
        reviewer = await self.create_reviewer()
        await self.create_sitedetail()
        await self.create_reviews(reviewer.id)
        category_ids = await self.create_categories()
        await self.create_listings(category_ids, auctioneer.id)

    async def create_superuser(self) -> User:
        superuser = await User.objects.get_or_none(email=settings.FIRST_SUPERUSER_EMAIL)
        user_dict = {
            "first_name": "Test",
            "last_name": "Admin",
            "email": settings.FIRST_SUPERUSER_EMAIL,
            "password": settings.FIRST_SUPERUSER_PASSWORD,
            "is_superuser": True,
            "is_staff": True,
            "is_email_verified": True,
        }
        if not superuser:
            superuser = await User.objects.create_user(**user_dict)
        return superuser

    async def create_auctioneer(self) -> User:
        auctioneer = await User.objects.get_or_none(
            email=settings.FIRST_AUCTIONEER_EMAIL
        )
        user_dict = {
            "first_name": "Test",
            "last_name": "Auctioneer",
            "email": settings.FIRST_AUCTIONEER_EMAIL,
            "password": settings.FIRST_AUCTIONEER_PASSWORD,
            "is_email_verified": True,
        }
        if not auctioneer:
            auctioneer = await User.objects.create_user(**user_dict)
        return auctioneer

    async def create_reviewer(self) -> User:
        reviewer = await User.objects.get_or_none(email=settings.FIRST_REVIEWER_EMAIL)
        user_dict = {
            "first_name": "Test",
            "last_name": "Reviewer",
            "email": settings.FIRST_REVIEWER_EMAIL,
            "password": settings.FIRST_REVIEWER_PASSWORD,
            "is_email_verified": True,
        }
        if not reviewer:
            reviewer = await User.objects.create_user(**user_dict)
        return reviewer

    async def create_sitedetail(self) -> SiteDetail:
        sitedetail, created = await SiteDetail.objects.aget_or_create()
        return sitedetail

    async def create_reviews(self, reviewer_id) -> None:
        review_mappings = self.review_mappings(reviewer_id)
        reviews_count = await Review.objects.filter(show=True).acount()
        if reviews_count < 1:
            reviews_to_create = [Review(**review) for review in review_mappings]
            await Review.objects.abulk_create(reviews_to_create)
        pass

    def review_mappings(self, reviewer_id) -> List[dict]:
        return [
            {
                "reviewer_id": reviewer_id,
                "text": "Maecenas vitae porttitor neque, ac porttitor nunc. Duis venenatis lacinia libero. Nam nec augue ut nunc vulputate tincidunt at suscipit nunc.",
                "show": True,
            },
            {
                "reviewer_id": reviewer_id,
                "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
                "show": True,
            },
            {
                "reviewer_id": reviewer_id,
                "text": "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident.",
                "show": True,
            },
        ]

    @sync_to_async
    def create_categories(self) -> List[UUID]:
        categories = Category.objects.all()
        if categories.count() < 1:
            categories_to_create = [
                Category(**category) for category in category_mappings
            ]
            categories = Category.objects.bulk_create(categories_to_create)
        return [category.id for category in categories]

    async def create_listings(self, category_ids, auctioneer_id) -> None:
        listings = Listing.objects.all()
        if (await listings.acount()) < 1:
            files_to_create = [File(**file) for file in file_mappings]
            files = await File.objects.abulk_create(files_to_create)
            updated_listing_mappings = []
            for idx, mapping in enumerate(listing_mappings):
                mapping.update(
                    {
                        "category_id": random.choice(category_ids),
                        "desc": "Korem ipsum dolor amet, consectetur adipiscing elit. Maece nas in pulvinar neque. Nulla finibus lobortis pulvinar. Donec a consectetur nulla.",
                        "auctioneer_id": auctioneer_id,
                        "closing_date": timezone.now() + timedelta(days=7 + idx),
                        "image_id": files[idx].id,
                    }
                )
                updated_listing_mappings.append(mapping)
            listings_to_create = [
                Listing(**listing) for listing in updated_listing_mappings
            ]
            await Listing.objects.abulk_create(listings_to_create)

            # Upload Images
            for idx, image_file in enumerate(os.listdir(test_images_directory)):
                image_path = os.path.join(test_images_directory, image_file)
                FileProcessor.upload_file(image_path, str(files[idx].id), "listings")
        pass
