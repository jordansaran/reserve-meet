from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _



class BookingStatus(TextChoices):
    PENDING = 'pending', _('Pendente')
    CONFIRMED = 'confirmed', _('Confirmada')
    CANCELLED = 'cancelled', _('Cancelada')
    COMPLETED = 'completed', _('Concluída')


STATE_CHOICES = [
    ("AC", _("Acre")),
    ("AL", _("Alagoas")),
    ("AM", _("Amazonas")),
    ("AP", _("Amapá")),
    ("BA", _("Bahia")),
    ("CE", _("Ceará")),
    ("DF", _("Distrito Federal")),
    ("ES", _("Espírito Santo")),
    ("GO", _("Goiás")),
    ("MA", _("Maranhão")),
    ("MG", _("Minas Gerais")),
    ("MS", _("Mato Grosso do Sul")),
    ("MT", _("Mato Grosso")),
    ("PA", _("Pará")),
    ("PB", _("Paraíba")),
    ("PE", _("Pernambuco")),
    ("PI", _("Piauí")),
    ("PR", _("Paraná")),
    ("RJ", _("Rio de Janeiro")),
    ("RN", _("Rio Grande do Norte")),
    ("RO", _("Rondônia")),
    ("RR", _("Roraima")),
    ("RS", _("Rio Grande do Sul")),
    ("SC", _("Santa Catarina")),
    ("SE", _("Sergipe")),
    ("SP", _("São Paulo")),
    ("TO", _("Tocantins")),
]
