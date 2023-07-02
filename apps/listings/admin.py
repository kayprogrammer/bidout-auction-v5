from django.contrib import admin
from apps.listings.models import Bid, Category, Listing, WatchList


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    list_filter = ("name",)


class ListingAdmin(admin.ModelAdmin):
    list_display = (
        "auctioneer",
        "name",
        "category",
        "price",
        "bids_count",
        "highest_bid",
        "closing_date",
    )
    list_filter = (
        "auctioneer",
        "name",
        "category",
        "price",
        "bids_count",
        "highest_bid",
        "closing_date",
    )


class BidAdmin(admin.ModelAdmin):
    list_display = ("user", "listing", "amount")
    list_filter = ("user", "listing", "amount")


class WatchListAdmin(admin.ModelAdmin):
    list_display = ("user", "listing", "guest")
    list_filter = ("user", "listing", "guest")


admin.site.register(Category, CategoryAdmin)
admin.site.register(Listing, ListingAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(WatchList, WatchListAdmin)
