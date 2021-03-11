from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext as _

from core import models

class UserAdmin(BaseUserAdmin):
    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        # None is the title of the section
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('name',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        (_('Important dates'), {'fields': ('last_login',)})
    )

    # Fields to display in add user page of admin screen
    # Read django admin documentation for more details
    add_fieldsets = (
        (None, {'classes': ('wide', )}, {'fields': ('email', 'password1', 'password2')})
    )

# Registering UserAdmin for admin
admin.site.register(models.User, UserAdmin)
admin.site.register(models.Integration)
admin.site.register(models.Account)