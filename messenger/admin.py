from django.contrib import admin

from messenger.models import Subscriber


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "first_name", "last_name", "middle_name", "owner", "comment")
    list_filter = ("last_name", "email")
    search_fields = ("email", "first_name", "last_name", "middle_name", "owner", "comment")
