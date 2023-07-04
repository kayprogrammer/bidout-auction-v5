from django.test import TestCase
from django.test.client import AsyncClient

from apps.accounts.auth import Authentication
from apps.accounts.models import Jwt

from apps.common.utils import TestUtil
from unittest import mock

from apps.listings.models import Bid, WatchList


class TestListings(TestCase):
    listings_url = "/api/v5/listings/"
    listing_detail_url = "/api/v5/listings/detail/"
    watchlist_url = "/api/v5/listings/watchlist/"
    categories_url = "/api/v5/listings/categories/"
    maxDiff = None

    def setUp(self):
        self.client = AsyncClient()
        self.content_type = "application/json"
        verified_user = TestUtil.verified_user()
        self.verified_user = verified_user
        self.listing = TestUtil.create_listing(verified_user)["listing"]
        self.auth_token = TestUtil.jwt_obj(verified_user).access
        self.another_verified_user = TestUtil.another_verified_user()

    async def test_retrieve_all_listings(self):
        # Verify that all listings are retrieved successfully
        response = await self.client.get(
            self.listings_url, content_type=self.content_type
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Listings fetched")
        data = result["data"]
        self.assertGreater(len(data), 0)
        self.assertTrue(any(isinstance(obj["name"], str) for obj in data))

    async def test_retrieve_particular_listng(self):
        listing = self.listing
        # Verify that a particular listing retrieval fails with an invalid slug
        response = await self.client.get(
            f"{self.listing_detail_url}invalid_slug/", content_type=self.content_type
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Listing does not exist!",
            },
        )

        # Verify that a particular listing is retrieved successfully
        response = await self.client.get(
            f"{self.listing_detail_url}{listing.slug}/", content_type=self.content_type
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Listing details fetched",
                "data": {
                    "listing": {
                        "auctioneer": mock.ANY,
                        "name": listing.name,
                        "slug": listing.slug,
                        "desc": listing.desc,
                        "category": "TestCategory",
                        "price": mock.ANY,
                        "closing_date": mock.ANY,
                        "active": True,
                        "bids_count": 0,
                        "highest_bid": "0.00",
                        "time_left_seconds": mock.ANY,
                        "image": mock.ANY,
                        "watchlist": None,
                    },
                    "related_listings": [],
                },
            },
        )

    async def test_get_user_watchlists_listng(self):
        listing = self.listing
        user_id = self.verified_user.id

        await WatchList.objects.acreate(user_id=user_id, listing_id=listing.id)
        bearer = {"Authorization": f"Bearer {self.auth_token}"}

        response = await self.client.get(
            self.watchlist_url, content_type=self.content_type, **bearer
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Watchlist Listings fetched")
        data = result["data"]
        self.assertGreater(len(data), 0)
        self.assertTrue(any(isinstance(obj["name"], str) for obj in data))

    async def test_create_or_remove_user_watchlists_listng(self):
        listing = self.listing

        # Verify that the endpoint fails with an invalid slug
        bearer = {"Authorization": f"Bearer {self.auth_token}"}
        response = await self.client.post(
            self.watchlist_url,
            {"slug": "invalid_slug"},
            content_type=self.content_type,
            **bearer,
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Listing does not exist!",
            },
        )

        # Verify that the watchlist was created successfully
        response = await self.client.post(
            self.watchlist_url,
            {"slug": listing.slug},
            content_type=self.content_type,
            **bearer,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Listing added to user watchlist",
                "data": {"guestuser_id": None},
            },
        )

    async def test_retrieve_all_categories(self):
        # Verify that all categories are retrieved successfully
        response = await self.client.get(
            self.categories_url, content_type=self.content_type
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Categories fetched")
        data = result["data"]
        self.assertGreater(len(data), 0)
        self.assertTrue(any(isinstance(obj["name"], str) for obj in data))

    async def test_retrieve_all_listings_by_category(self):
        slug = self.listing.category.slug

        # Verify that listings by an invalid category slug fails
        response = await self.client.get(
            f"{self.categories_url}invalid_category_slug/",
            content_type=self.content_type,
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(), {"status": "failure", "message": "Invalid category"}
        )

        # Verify that all listings by a valid category slug are retrieved successfully
        response = await self.client.get(
            f"{self.categories_url}{slug}/", content_type=self.content_type
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Category Listings fetched")
        data = result["data"]
        self.assertGreater(len(data), 0)
        self.assertTrue(any(isinstance(obj["name"], str) for obj in data))

    async def test_retrieve_listing_bids(self):
        listing = self.listing
        another_verified_user = self.another_verified_user
        await Bid.objects.acreate(
            user=another_verified_user, listing=listing, amount=10000.00
        )

        # Verify that listings by an invalid listing slug fails
        response = await self.client.get(
            f"{self.listing_detail_url}invalid_category_slug/bids/",
            content_type=self.content_type,
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Listing does not exist!",
            },
        )

        # Verify that all listings by a valid listing slug are retrieved successfully
        response = await self.client.get(
            f"{self.listing_detail_url}{listing.slug}/bids/",
            content_type=self.content_type,
        )
        self.assertEqual(response.status_code, 200)

        result = response.json()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Listing Bids fetched")
        data = result["data"]
        self.assertTrue(isinstance(data["listing"], str))

    async def test_create_bid(self):
        listing = self.listing

        # Verify that the endpoint fails with an invalid slug
        bearer = {"Authorization": f"Bearer {self.auth_token}"}
        response = await self.client.post(
            f"{self.listing_detail_url}invalid_category_slug/bids/",
            {"amount": 10000},
            content_type=self.content_type,
            **bearer,
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Listing does not exist!",
            },
        )

        # Verify that the endpoint fails with an invalid user
        response = await self.client.post(
            f"{self.listing_detail_url}{listing.slug}/bids/",
            {"amount": 10000},
            content_type=self.content_type,
            **bearer,
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "You cannot bid your own product!",
            },
        )

        # Update headers with another user's token
        another_verified_user = self.another_verified_user
        access = Authentication.create_access_token(
            {"user_id": str(another_verified_user.id)}
        )
        refresh = Authentication.create_refresh_token()
        await Jwt.objects.acreate(
            user_id=another_verified_user.id, access=access, refresh=refresh
        )
        bearer["Authorization"] = f"Bearer {access}"

        # Verify that the endpoint fails with a lesser bidding price
        response = await self.client.post(
            f"{self.listing_detail_url}{listing.slug}/bids/",
            {"amount": 100},
            content_type=self.content_type,
            **bearer,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Bid amount cannot be less than the bidding price!",
            },
        )

        # Verify that the bid was created successfully
        response = await self.client.post(
            f"{self.listing_detail_url}{listing.slug}/bids/",
            {"amount": 10000},
            content_type=self.content_type,
            **bearer,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Bid added to listing",
                "data": {
                    "user": mock.ANY,
                    "amount": "10000",
                },
            },
        )

        # You can also test for other error responses.....
