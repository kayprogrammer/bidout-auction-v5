from django.utils import timezone
from django.test import TestCase
from django.test.client import AsyncClient
from apps.accounts.auth import Authentication
from apps.accounts.models import Jwt

from apps.common.utils import TestUtil
from apps.listings.models import Bid, Category
from unittest import mock
from datetime import timedelta


class TestAuctioneer(TestCase):
    profile_url = "/api/v5/auctioneer/"
    listings_url = "/api/v5/auctioneer/listings/"
    maxDiff = None

    def setUp(self):
        self.client = AsyncClient()
        self.content_type = "application/json"
        verified_user = TestUtil.verified_user()
        auth_token = TestUtil.jwt_obj(verified_user).access
        self.bearer = {"Authorization": f"Bearer {auth_token}"}
        self.verified_user = verified_user
        self.listing = TestUtil.create_listing(verified_user)["listing"]
        self.another_verified_user = TestUtil.another_verified_user()

    async def test_profile_view(self):
        verified_user = self.verified_user
        response = await self.client.get(
            self.profile_url, content_type=self.content_type, **self.bearer
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "User details fetched!",
                "data": {
                    "first_name": verified_user.first_name,
                    "last_name": verified_user.last_name,
                    "avatar": mock.ANY,
                },
            },
        )

    async def test_profile_update(self):
        user_dict = {
            "first_name": "VerifiedUser",
            "last_name": "Update",
            "file_type": "image/jpeg",
        }
        response = await self.client.put(
            self.profile_url, user_dict, content_type=self.content_type, **self.bearer
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "User updated!",
                "data": {
                    "first_name": "VerifiedUser",
                    "last_name": "Update",
                    "file_upload_data": mock.ANY,
                },
            },
        )

    async def test_auctioneer_retrieve_listings(self):
        # Verify that all listings by a particular auctioneer is fetched
        response = await self.client.get(
            self.listings_url, content_type=self.content_type, **self.bearer
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Auctioneer Listings fetched")
        data = result["data"]
        self.assertGreater(len(data), 0)
        self.assertTrue(any(isinstance(obj["name"], str) for obj in data))

    async def test_auctioneer_create_listings(self):
        # Create Category
        await Category.objects.acreate(name="Test Category")
        listing_dict = {
            "name": "Test Listing",
            "desc": "Test description",
            "category": "test-category",
            "price": 1000.00,
            "closing_date": timezone.now() + timedelta(days=1),
            "file_type": "image/jpeg",
        }

        # Verify that create listing succeeds with a valid category
        response = await self.client.post(
            self.listings_url,
            listing_dict,
            content_type=self.content_type,
            **self.bearer,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Listing created successfully",
                "data": {
                    "name": "Test Listing",
                    "auctioneer": mock.ANY,
                    "slug": "test-listing",
                    "desc": "Test description",
                    "category": "Test Category",
                    "price": mock.ANY,
                    "closing_date": mock.ANY,
                    "active": True,
                    "bids_count": 0,
                    "file_upload_data": mock.ANY,
                },
            },
        )

        # Verify that create listing failed with invalid category
        listing_dict.update({"category": "invalidcategory"})
        response = await self.client.post(
            self.listings_url,
            listing_dict,
            content_type=self.content_type,
            **self.bearer,
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Invalid entry",
                "data": {"category": "Invalid category"},
            },
        )

    async def test_auctioneer_update_listing(self):
        listing = self.listing

        listing_dict = {
            "name": "Test Listing Updated",
            "desc": "Test description Updated",
            "category": "invalidcategory",
            "price": 2000.00,
            "closing_date": timezone.now() + timedelta(days=1),
            "file_type": "image/png",
        }

        # Verify that update listing failed with invalid listing slug
        response = await self.client.put(
            f"{self.listings_url}invalid_slug/",
            listing_dict,
            content_type=self.content_type,
            **self.bearer,
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Listing does not exist!",
            },
        )

        # Verify that update listing failed with invalid category
        response = await self.client.put(
            f"{self.listings_url}{listing.slug}/",
            listing_dict,
            content_type=self.content_type,
            **self.bearer,
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Invalid entry",
                "data": {"category": "Invalid category"},
            },
        )

        # Verify that update listing succeeds with a valid category
        listing_dict.update({"category": "testcategory"})
        response = await self.client.put(
            f"{self.listings_url}{listing.slug}/",
            listing_dict,
            content_type=self.content_type,
            **self.bearer,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Listing updated successfully",
                "data": {
                    "name": "Test Listing Updated",
                    "auctioneer": mock.ANY,
                    "slug": "test-listing-updated",
                    "desc": "Test description Updated",
                    "category": "TestCategory",
                    "price": mock.ANY,
                    "closing_date": mock.ANY,
                    "active": True,
                    "bids_count": 0,
                    "file_upload_data": mock.ANY,
                },
            },
        )

        # You can also test for invalid users yourself.....

    async def test_auctioneer_listings_bids(self):
        listing = self.listing
        another_verified_user = self.another_verified_user

        # Create Bid
        await Bid.objects.acreate(
            user=another_verified_user, listing=listing, amount=5000.00
        )

        # Verify that auctioneer listing bids retrieval succeeds with a valid slug and owner
        response = await self.client.get(
            f"{self.listings_url}{listing.slug}/bids/",
            content_type=self.content_type,
            **self.bearer,
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Listing Bids fetched")
        data = result["data"]
        self.assertTrue(isinstance(data["listing"], str))

        # Verify that the auctioneer listing bids retrieval failed with invalid listing slug
        response = await self.client.get(
            f"{self.listings_url}invalid_slug/bids/",
            content_type=self.content_type,
            **self.bearer,
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Listing does not exist!",
            },
        )

        # Verify that the auctioneer listing bids retrieval failed with invalid owner
        access = Authentication.create_access_token(
            {"user_id": str(another_verified_user.id)}
        )
        refresh = Authentication.create_refresh_token()
        await Jwt.objects.acreate(
            user_id=another_verified_user.id, access=access, refresh=refresh
        )

        bearer = {"Authorization": f"Bearer {access}"}
        response = await self.client.get(
            f"{self.listings_url}{listing.slug}/bids/", **bearer
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "This listing doesn't belong to you!",
            },
        )
