from django.db.models import (
    Model,
    BooleanField,
    DateTimeField
)
from django.utils.translation import gettext_lazy as _


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

    class Meta:
        abstract = True
