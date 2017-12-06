from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from frekenbot.models import TelegramUser


class TelegramUserInline(admin.StackedInline):
    model = TelegramUser
    can_delete = False
    verbose_name_plural = 'telegram_users'


class UserAdmin(BaseUserAdmin):
    inlines = (TelegramUserInline, )


admin.site.unregister(User)
admin.site.register(User, UserAdmin)