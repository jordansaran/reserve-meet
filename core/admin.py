from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from core.models import User, UserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'role', 'is_active', 'is_staff', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Informações Pessoais'), {
            'fields': ('username', 'first_name', 'last_name', 'phone')
        }),
        (_('Permissões'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups',
                       'user_permissions')
        }),
        (_('Datas Importantes'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role', 'is_staff'),
        }),
    )

    readonly_fields = ['last_login', 'date_joined', 'created_at', 'updated_at']
    filter_horizontal = ['groups', 'user_permissions']


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'device_name',
        'ip_address',
        'location',
        'is_current',
        'is_active_display',
        'is_revoked',
        'created_at'
    ]
    list_filter = ['is_revoked', 'is_current', 'created_at']
    search_fields = ['user__email', 'user__username', 'ip_address', 'device_name']
    readonly_fields = [
        'user',
        'refresh_token_jti',
        'ip_address',
        'user_agent',
        'device_name',
        'location',
        'created_at',
        'last_activity',
        'expires_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def is_active_display(self, obj):
        """Mostra se a sessão está ativa com ícone"""
        return obj.is_active
    is_active_display.boolean = True
    is_active_display.short_description = 'Ativo'

    def has_add_permission(self, request):
        """Não permite criar sessões manualmente"""
        return False

    def has_change_permission(self, request, obj=None):
        """Permite apenas revogar (via actions)"""
        return False

    actions = ['revoke_sessions']

    def revoke_sessions(self, request, queryset):
        """Action para revogar múltiplas sessões"""
        revoked_count = 0
        for session in queryset.filter(is_revoked=False):
            session.revoke()
            revoked_count += 1

        self.message_user(
            request,
            f'{revoked_count} sessão(ões) revogada(s) com sucesso.'
        )
    revoke_sessions.short_description = 'Revogar sessões selecionadas'
