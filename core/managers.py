from django.contrib.auth.base_user import BaseUserManager
from django.db.models import Manager
from django.utils.translation import gettext_lazy as _


class ActiveManager(Manager):
    """
    Manager class to retrieve only active records.

    This manager is intended to filter querysets by the 'is_active' attribute.
    It overrides the default queryset retrieval method to include only records
    where 'is_active' is set to True.
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class UserManager(BaseUserManager):

    def _create_user(self, email, password, username=None, **extra_fields):
        """
        Create and save a user with the given cpf and password.
        """
        if not email:
            raise ValueError('O email é obrigatório')

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, username=None, **extra_fields):
        extra_fields.setdefault('role', 'user')
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, username, **extra_fields)

    def create_superuser(self, email, password, username=None, **extra_fields) -> "User":
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('role') not in ('admin', 'manager', 'user'):
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self._create_user(email, password, username, **extra_fields)
