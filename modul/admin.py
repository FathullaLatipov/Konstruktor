from django.contrib import admin

from .models import Bot, ClientBotUser, User, UserTG


# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ['username', 'uid']
    list_filter = ['created_at']
    list_display = ['uid', 'username']
    ordering = ['-id']


@admin.register(UserTG)
class UserAdmin(admin.ModelAdmin):
    search_fields = ['username', 'uid']
    list_filter = ['created_at']
    list_display = ['uid', 'username']
    ordering = ['-id']


@admin.register(ClientBotUser)
class ClientBotUserAdmin(admin.ModelAdmin):
    search_fields = ['uid']
    list_display = ['uid', 'balance']
    ordering = ['-id']


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    search_fields = ['username']
    list_display = ['id', 'username', 'owner']
    ordering = ['-id']
