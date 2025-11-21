from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class UserRoles(TextChoices):
    ADMIN = 'admin', _('Administrador')
    MANAGER = 'manager', _('Gerente')
    USER = 'user', _('Usuário')


roles_choices = UserRoles.choices
