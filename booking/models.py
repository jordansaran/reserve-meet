from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import (
    RangeOperators,
    DateTimeRangeField
)
from django.core.validators import MinValueValidator
from booking.choices import BookingStatus
from booking.validators import (
    cep_validator,
    validate_brazilian_state
)
from core.models import BaseModel
from django.db.models import (
    CharField,
    ForeignKey,
    CASCADE,
    PositiveIntegerField,
    UniqueConstraint,
    ManyToManyField,
    DateField,
    DateTimeField,
    Index,
    Func,
    F,
    BooleanField,
    SET_NULL,
    TextField,
    Q
)
from django.utils.translation import gettext_lazy as _


class Location(BaseModel):
    name = CharField(
        _("Nome"),
        max_length=100,
        blank=False,
        null=False,
        help_text=_("Nome da localizaçao, ex: Prédio A"),
        unique=True
    )
    address = CharField(
        max_length=100,
        blank=False,
        null=False,
        help_text=_("Endereço da localização, ex: Rua XYZ")
    )
    city = CharField(
        max_length=100,
        blank=False,
        help_text=_("Cidade")
    )
    state = CharField(
        max_length=2,
        blank=False,
        help_text=_("Estado (sigla com 2 letras, ex: SP)"),
        validators=[validate_brazilian_state]
    )
    cep = CharField(
        max_length=9,
        blank=False,
        help_text=_("CEP no formato: XXXXX-XXX"),
        validators=[cep_validator]
    )
    description = CharField(
        _("Descrição"),
        max_length=512,
        blank=False,
        null=False,
        help_text=_("Descrição da localização: Ex: Predio A localizado próximoa a Rua Y")
    )

    def clean(self):
        """
        Cleans and normalizes the state attribute.

        This method ensures that the `state` attribute, if set, is converted
        to uppercase format. This behavior ensures uniformity in text
        representation for the state attribute.

        Raises:
            Propagates any exceptions raised by the parent class's `clean` method.
        """
        super().clean()
        if self.state:
            self.state = self.state.upper()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Localização")
        verbose_name_plural = _("Localizações")
        ordering = ["name"]


class Resource(BaseModel):

    name = CharField(
        _("Nome"),
        max_length=100,
        blank=False,
        null=False,
        help_text=_("Nome do objeto"),
        unique=True
    )
    description = CharField(
        _("Descrição"),
        max_length=512,
        blank=False,
        null=False,
        help_text=_("Descrição do objeto")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Recurso")
        verbose_name_plural = _("Recursos")
        ordering = ["name"]


class Room(BaseModel):
    name = CharField(
        _("Nome"),
        max_length=100,
        blank=False,
        null=False,
        help_text=_("Nome da sala, ex: Sala 101")
    )
    location = ForeignKey(
        Location,
        on_delete=CASCADE,
        related_name="rooms",
        help_text=_("Chave estrangeira da tabela Location")
    )
    capacity = PositiveIntegerField(
        _("Capacidade"),
        null=False,
        help_text=_("Capacidade de pessoas na sala, ex: 10"),
        validators=[MinValueValidator(1)]
    )
    resources = ManyToManyField(
        Resource,
        related_name="rooms",
        blank=True,
    )

    def __str__(self):
        return f"{self.name} - {self.location} - {_('Capacidade')}: {self.capacity}"

    class Meta:
        verbose_name = _("Sala")
        verbose_name_plural = _("Salas")
        constraints = [
            UniqueConstraint(
                fields=["name", "location"],
                name="unique_room_name_per_location",
            )
        ]


class Booking(BaseModel):
    manager = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        related_name="bookings",
        help_text=_("Chave estrangeira da tabela User")
    )
    room = ForeignKey(
        Room,
        on_delete=CASCADE,
        related_name="bookings",
        help_text=_("Chave estrangeira da tabela Room")
    )
    date_booking = DateField(
        _("Data do reserva"),
        help_text=_("Data da reserva"),
        null=False
    )
    start_datetime = DateTimeField(
        _("Inicio da reserva"),
        help_text=_("Hora inicial da reserva"),
        null=False
    )
    end_datetime = DateTimeField(
        _("Fim da reserva"),
        help_text=_("Hora final da reserva"),
        null=False
    )
    has_coffee_break = BooleanField(
        _("Terá para lanche + café?"),
        default=False,
        null=False,
        help_text=_("Indica se na reunião irá precisar de parada para coffe break")
    )
    coffee_break_headcount = PositiveIntegerField(
        _("Quantidade de pessoas para coffe break"),
        default=1,
        validators=[MinValueValidator(1)],
        null=False,
        help_text=_("Quantidade de pessoas para coffe break")
    )
    status = CharField(
        _("Status"),
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
        help_text=_("Status da reserva")
    )
    confirmed_by = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=SET_NULL,
        related_name="confirmed_bookings",
        null=True,
        blank=True,
        help_text=_("Usuário que confirmou a reserva")
    )
    confirmed_at = DateTimeField(
        _("Data/Hora de confirmação"),
        null=True,
        blank=True,
        help_text=_("Quando a reserva foi confirmada")
    )
    cancelled_by = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=SET_NULL,
        related_name="cancelled_bookings",
        null=True,
        blank=True,
        help_text=_("Usuário que cancelou a reserva")
    )
    cancelled_at = DateTimeField(
        _("Data/Hora de cancelamento"),
        null=True,
        blank=True,
        help_text=_("Quando a reserva foi cancelada")
    )
    cancellation_reason = TextField(
        _("Motivo do cancelamento"),
        blank=True,
        null=True,
        help_text=_("Motivo pelo qual a reserva foi cancelada")
    )
    notes = TextField(
        _("Observações"),
        blank=True,
        null=True,
        help_text=_("Observações gerais sobre a reserva")
    )

    def __str__(self):
        return f"{self.room} - {_('Data')}: {self.date_booking} - {_('Status')}: {self.get_status_display()}"

    def confirm(self, user):
        """Confirma a reserva"""
        from django.utils import timezone
        self.status = BookingStatus.CONFIRMED
        self.confirmed_by = user
        self.confirmed_at = timezone.now()
        self.save()

    def cancel(self, user, reason=None):
        """Cancela a reserva"""
        from django.utils import timezone
        self.status = BookingStatus.CANCELLED
        self.cancelled_by = user
        self.cancelled_at = timezone.now()
        if reason:
            self.cancellation_reason = reason
        self.save()

    def complete(self):
        """Marca a reserva como concluída"""
        self.status = BookingStatus.COMPLETED
        self.save()

    @property
    def is_confirmed(self):
        return self.status == BookingStatus.CONFIRMED

    @property
    def is_pending(self):
        return self.status == BookingStatus.PENDING

    @property
    def is_cancelled(self):
        return self.status == BookingStatus.CANCELLED

    class Meta:
        verbose_name = _("Reserva")
        verbose_name_plural = _("Reservas")
        ordering = ["date_booking", "start_datetime", 'room']
        constraints = [
            ExclusionConstraint(
                name='without_overlaps_booking',
                expressions=[
                    ('room', RangeOperators.EQUAL),
                    (
                        Func(
                            F('start_datetime'),
                            F('end_datetime'),
                            function='tstzrange',
                            output_field=DateTimeRangeField()
                        ),
                        RangeOperators.OVERLAPS
                    ),
                ],
                condition=(
                    ~Q(status__in=[BookingStatus.CANCELLED, BookingStatus.COMPLETED]) &
                    Q(is_active=True)
                )
            ),
        ]
        indexes = [
            Index(fields=['room', 'date_booking']),
            Index(fields=['status', 'date_booking']),
            Index(fields=['manager', 'status']),
        ]
