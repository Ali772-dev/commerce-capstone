from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create/", views.create_listing, name="create"),
    path("listing/<int:listing_id>", views.listing, name="listing"),
    path("listing/<int:listing_id>/live-bids/", views.listing_live_bids, name="listing_live_bids"),
    path("watchlist/", views.watchlist, name="watchlist"),
    path("categories/", views.categories, name="categories"),
    
    # Profile & Social
    path("profile/", views.profile_view, name="my_profile"),
    path("profile/<str:username>/", views.profile_view, name="profile"),
    path("users/", views.users_search, name="users_search"),
    path("follow/<int:user_id>/", views.toggle_follow, name="toggle_follow"),
    
    # Notifications
    path("notifications/", views.notifications_view, name="notifications"),
    path("notifications/read/<int:notif_id>/", views.mark_notification_read, name="mark_notification_read"),
    path("notifications/read-all/", views.mark_all_notifications_read, name="mark_all_notifications_read"),

    # Wallet & Checkout
    path("wallet/", views.wallet_view, name="wallet"),
    path("checkout/<int:listing_id>/", views.checkout_view, name="checkout"),

    # Report & Bug reporting
    path("report/", views.report_issue, name="report_issue"),
    path("report/listing/<int:listing_id>/", views.report_issue, name="report_listing"),
    path("manage/reports/", views.admin_reports_view, name="admin_reports"),

    # Admin actions (FT-7)
    path("manage/toggle-user/<int:user_id>/", views.toggle_user_status, name="toggle_user_status"),
    path("manage/cancel-listing/<int:listing_id>/", views.cancel_listing, name="cancel_listing"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
