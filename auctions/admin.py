from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Listing, ProductImage, Bid, AuctionResult, Notification, Comment, Watchlist, Follow, Report


class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'raw_password', 'role', 'status', 'deposit_balance', 'reputation_score', 'phone', 'is_staff')
    list_filter = ('role', 'status', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'phone', 'raw_password')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Capstone Məlumatları', {'fields': ('phone', 'role', 'status', 'raw_password', 'deposit_balance', 'reputation_score')}),
    )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'category', 'starting_bid', 'min_increment', 'current_bid', 'is_active', 'end_time', 'winner')
    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('title', 'description', 'creator__username', 'seller_name')
    inlines = [ProductImageInline]


class BidAdmin(admin.ModelAdmin):
    list_display = ('listing', 'bidder', 'amount', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('listing__title', 'bidder__username')


class AuctionResultAdmin(admin.ModelAdmin):
    list_display = ('listing', 'winning_bid', 'closed_at')
    list_filter = ('closed_at',)
    search_fields = ('listing__title', 'winning_bid__bidder__username')


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')


class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'reporter', 'listing', 'status', 'created_at')
    list_filter = ('status', 'report_type', 'created_at')
    search_fields = ('title', 'description', 'reporter__username', 'reporter_email', 'listing__title')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Şikayət / Xəta Məlumatları', {'fields': ('title', 'report_type', 'description', 'screenshot', 'listing')}),
        ('Bildirən Şəxs', {'fields': ('reporter', 'reporter_email')}),
        ('İdarəetmə və Nəticə', {'fields': ('status', 'admin_notes', 'created_at', 'updated_at')}),
    )


admin.site.register(User, UserAdmin)
admin.site.register(Listing, ListingAdmin)
admin.site.register(ProductImage)
admin.site.register(Bid, BidAdmin)
admin.site.register(AuctionResult, AuctionResultAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Comment)
admin.site.register(Watchlist)
admin.site.register(Follow)
admin.site.register(Report, ReportAdmin)
