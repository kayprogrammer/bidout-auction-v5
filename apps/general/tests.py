from django.test import TestCase
from django.test.client import AsyncClient

from apps.general.models import Review
from apps.common.utils import TestUtil
from unittest import mock


class TestGeneral(TestCase):
    sitedetail_url = "/api/v5/general/site-detail/"
    subscriber_url = "/api/v5/general/subscribe/"
    reviews_url = "/api/v5/general/reviews/"

    def setUp(self):
        self.client = AsyncClient()
        verified_user = TestUtil.verified_user()
        review_dict = {
            "reviewer_id": verified_user.id,
            "show": True,
            "text": "This is a nice new platform",
        }
        review = Review.objects.create(**review_dict)
        self.review = review
        self.headers = {"CONTENT_TYPE": "application/json"}

    async def test_retrieve_sitedetail(self):
        response = await self.client.get(self.sitedetail_url)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Site Details fetched")
        keys = ["name", "email", "phone", "address", "fb", "tw", "wh", "ig"]
        self.assertTrue(all(item in result["data"] for item in keys))

    async def test_subscribe(self):
        # Check response validity
        response = await self.client.post(
            self.subscriber_url,
            {"email": "test_subscriber@example.com"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Subscription successful",
                "data": {"email": "test_subscriber@example.com"},
            },
        )

    async def test_retrieve_reviews(self):
        # Check response validity
        response = await self.client.get(self.reviews_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Reviews fetched",
                "data": [{"reviewer": mock.ANY, "text": "This is a nice new platform"}],
            },
        )
