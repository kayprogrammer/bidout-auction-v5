from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator
from apps.accounts.models import User
from apps.common.models import BaseModel, File, GuestUser
from autoslug import AutoSlugField
from apps.common.file_processors import FileProcessor
from decimal import Decimal


class Category(BaseModel):
    name = models.CharField(max_length=30, unique=True)
    slug = AutoSlugField(populate_from="name", unique=True, always_update=True)

    def __str__(self):
        return self.name

    def clean(self):
        if self.name == "Other":
            raise ValidationError("Name must not be 'Other'")

    class Meta:
        verbose_name_plural = "Categories"


class Listing(BaseModel):
    auctioneer = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=70)
    slug = AutoSlugField(populate_from="name", unique=True, always_update=True)
    desc = models.TextField()

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)

    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    highest_bid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bids_count = models.IntegerField(default=0)
    closing_date = models.DateTimeField(null=True)
    active = models.BooleanField(default=True)

    image = models.ForeignKey(File, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    @property
    def time_left_seconds(self):
        remaining_time = self.closing_date - timezone.now()
        remaining_seconds = remaining_time.total_seconds()
        return remaining_seconds

    @property
    def time_left(self):
        if not self.active:
            return 0
        return self.time_left_seconds


class Bid(BaseModel):
    user = models.ForeignKey(User, related_name="bids", on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, related_name="bids", on_delete=models.CASCADE)

    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )

    def __str__(self):
        return f"{self.listing.name} - ${self.amount}"

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "listing"],
                name="unique_user_listing_bid",
            ),
            models.UniqueConstraint(
                fields=["listing", "amount"],
                name="unique_listing_amount_bid",
            ),
        ]


class WatchList(BaseModel):
    user = models.ForeignKey(
        User, related_name="watchlists", on_delete=models.CASCADE, null=True
    )
    listing = models.ForeignKey(
        Listing, related_name="watchlists", on_delete=models.CASCADE
    )
    guest = models.ForeignKey(
        GuestUser, related_name="watchlists", on_delete=models.CASCADE, null=True
    )

    def __str__(self):
        if self.user:
            return f"{self.listing.name} - {self.user.full_name}"
        return f"{self.listing.name} - {self.guest_id}"

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "listing"],
                name="unique_user_listing_watchlists",
            ),
            models.UniqueConstraint(
                fields=["guest", "listing"],
                name="unique_guest_listing_watchlists",
            ),
        ]
