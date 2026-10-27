from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "phone",
        "full_name",
        "role",
        "status",
        "is_active",
        "is_staff",
    )
    list_filter = ("role", "status", "is_active", "is_staff")
    search_fields = ("username", "phone", "full_name", "email")
    readonly_fields = ("created_at", "modified_at", "last_login")
    exclude = ("password",)

    def get_queryset(self, request):
        return User.all_objects.all()
