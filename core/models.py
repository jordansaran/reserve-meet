from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db.models import (
    Model,
    BooleanField,
    DateTimeField,
    CharField,
    Manager,
    EmailField,
    ForeignKey,
    CASCADE,
    TextField,
    GenericIPAddressField,
    Index
)
from django.utils.translation import gettext_lazy as _
from core.choices import roles_choices
from core.managers import (
    ActiveManager,
    UserManager
)


class BaseModel(Model):
    is_active = BooleanField(
        _("Ativo"),
        default=True,
        blank=True,
        help_text="Indica se o registro está ativado"
    )
    created_at = DateTimeField(
        _("Data de criação"),
        auto_now_add=True,
        null=True,
        blank=True,
        help_text="Indicado quando o registro foi criado"
    )
    updated_at = DateTimeField(
        _("Data de alteração"),
        auto_now=True,
        null=True,
        blank=True,
        help_text="Indicado quando o registro foi alterado"
    )

    objects = ActiveManager()

    all_objects = Manager()

    class Meta:
        abstract = True


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    email = EmailField(
        _('E-mail'),
        unique=True,
    )
    username = CharField(
        _ ("Username"),
        max_length=150,
        unique=True
    )
    first_name = CharField(
        _("Nome"),
        max_length=150,
        blank=True
    )
    last_name = CharField(
        _("Sobrenome"),
        max_length=150,
        blank=True
    )
    phone = CharField(
        _("Telefone"),
        max_length=20,
        blank=True
    )
    role = CharField(
        _("Role"),
        max_length=20,
        choices=roles_choices,
        default='user'
    )
    is_staff = BooleanField(
        _("Staff"),
        default=False
    )
    is_superuser = BooleanField(
        _('Superuser'),
        default=False
    )
    date_joined = DateTimeField(
        _('Data de cadastro'),
        auto_now_add=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def __str__(self):
        return f"{self.id} - {self.email} - {self.role}"

    class Meta:
        verbose_name = _('Usuário')
        verbose_name_plural = _('Usuários')
        ordering = ['-created_at']


class UserSession(Model):
    """
    Modelo para rastrear sessões de usuários (logins)

    Armazena informações sobre cada login/dispositivo do usuário,
    incluindo IP, user agent, localização aproximada e quando foi usado.
    """
    user = ForeignKey(
        'User',
        on_delete=CASCADE,
        related_name='sessions',
        verbose_name=_('Usuário')
    )
    refresh_token_jti = CharField(
        _('Token JTI'),
        max_length=255,
        unique=True,
        help_text=_('Identificador único do refresh token (JTI)')
    )
    ip_address = GenericIPAddressField(
        _('Endereço IP'),
        null=True,
        blank=True,
        help_text=_('Endereço IP de onde foi feito o login')
    )
    user_agent = TextField(
        _('User Agent'),
        blank=True,
        help_text=_('Informações do navegador/dispositivo')
    )
    device_name = CharField(
        _('Nome do Dispositivo'),
        max_length=255,
        blank=True,
        help_text=_('Nome amigável do dispositivo (ex: Chrome no Windows)')
    )
    location = CharField(
        _('Localização'),
        max_length=255,
        blank=True,
        help_text=_('Localização aproximada (cidade, país)')
    )
    is_current = BooleanField(
        _('Sessão Atual'),
        default=False,
        help_text=_('Indica se é a sessão atual do usuário')
    )
    last_activity = DateTimeField(
        _('Última Atividade'),
        auto_now=True,
        help_text=_('Última vez que esta sessão foi usada')
    )
    created_at = DateTimeField(
        _('Data de Criação'),
        auto_now_add=True,
        help_text=_('Quando o login foi realizado')
    )
    expires_at = DateTimeField(
        _('Data de Expiração'),
        help_text=_('Quando o refresh token expira')
    )
    is_revoked = BooleanField(
        _('Revogado'),
        default=False,
        help_text=_('Se a sessão foi revogada/logout')
    )

    def __str__(self):
        return f"{self.user.email} - {self.device_name or 'Unknown'} - {self.created_at}"

    @property
    def is_active(self):
        """Verifica se a sessão ainda está ativa"""
        from django.utils import timezone
        return not self.is_revoked and self.expires_at > timezone.now()

    def revoke(self):
        """Revoga esta sessão"""
        self.is_revoked = True
        self.save()

    class Meta:
        verbose_name = _('Sessão de Usuário')
        verbose_name_plural = _('Sessões de Usuários')
        ordering = ['-created_at']
        indexes = [
            Index(fields=['user', 'is_revoked']),
            Index(fields=['refresh_token_jti']),
            Index(fields=['is_current']),
        ]
