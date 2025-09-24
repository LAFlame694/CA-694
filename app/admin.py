from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Chama, Member, Contribution

# Register your models here.
class CustomUserAdmin(UserAdmin):
    # fields to display in admin list view
    list_display = (
        'username', 
        'email', 
        'phone_number', 
        'is_staff', 
        'is_active'
    )

    # fields that can be searched
    search_fields = ('username', 'email', 'phone_number')

    # fieldsets to control form layout
    fieldsets = (
        (None, {'fields': ('username', 'email', 'phone_number', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Chama)
admin.site.register(Member)
admin.site.register(Contribution)