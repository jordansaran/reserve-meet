from django.contrib.auth.models import User
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import (
    RangeOperators,
    DateTimeRangeField
)
from django.core.validators import MinValueValidator
from core.models import BaseModel
from django.db.models import (
    CharField,
    ForeignKey,
    CASCADE,
    PositiveIntegerField,
    UniqueConstraint,
    ManyToManyField,
    DateField,
    TimeField,
    Index,
    Func,
    F,
    BooleanField
)
from django.utils.translation import gettext_lazy as _


class Location(BaseModel):
    name = CharField(
        _("Nome"),
        max_length=100,
        blank=False,
        null=False,
        help_text="Nome da localizaçao, ex: Prédio A",
        unique=True
    ),
    description = CharField(
        _("Descrição"),
        max_length=512,
        blank=False,
        null=False,
        help_text="Descrição da localização: Ex: Predio A localizado próximoa a Rua Y"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Localização")
        verbose_name_plural = _("Localizações")

class Resource(BaseModel):

    name = CharField(
        _("Nome"),
        max_length=100,
        blank=False,
        null=False,
        help_text="Nome do objeto",
        unique=True
    ),
    description = CharField(
        _("Descrição"),
        max_length=512,
        blank=False,
        null=False,
        help_text="Descrição do objeto"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Recurso")
        verbose_name_plural = _("Recursos")


class Room(BaseModel):
    name = CharField(
        _("Nome"),
        max_length=100,
        blank=False,
        null=False,
        help_text="Nome da sala, ex: Sala 101"
    ),
    location = ForeignKey(
        Location,
        on_delete=CASCADE,
        related_name="rooms",
        help_text="Chave estrangeira da tabela Location"
    )
    capacity = PositiveIntegerField(
        _("Capacidade"),
        null=False,
        help_text="Capacidade de pessoas na sala, ex: 10",
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
        User,
        on_delete=CASCADE,
        related_name="bookings",
        help_text="Chave estrangeira da tabela User"
    )
    room = ForeignKey(
        Room,
        on_delete=CASCADE,
        related_name="bookings",
        help_text="Chave estrangeira da tabela Room"
    )
    date_booking = DateField(
        _("Data do reserva"),
        help_text="Data da reserva",
        null=False
    )
    start_time_booking = TimeField(
        _("Inicio da reserva"),
        help_text="Hora inicial da reserva",
        null=False
    )
    end_time_booking = TimeField(
        _("Fim da reserva"),
        help_text="Hora final da reserva",
        null=False
    )
    has_coffee_break = BooleanField(
        _("Terá para lanche + café?"),
        default=False,
        null=False,
        help_text="Indica se na reunião irá precisar de parada para coffe break"
    )
    coffee_break_headcount = PositiveIntegerField(
        _("Quantidade de pessoas para coffe break"),
        default=1,
        validators=[MinValueValidator(1)],
        null=False,
        help_text="Quantidade de pessoas para coffe break"
    )

    def __str__(self):
        return f"{self.room} - {_('Data')}: {self.date_booking} - {_('Hora')}: {self.start_time_booking} - {_('Fim')}: {self.end_time_booking}"

    class Meta:
        verbose_name = _("Reserva")
        verbose_name_plural = _("Reservas")
        ordering = ["date_booking", "start_time_booking", 'room']
        constraints = [
            ExclusionConstraint(
                name='withtout_overlaps_booking',
                expressions=[
                    ('room', RangeOperators.EQUAL),
                    ('date_booking', RangeOperators.EQUAL),
                    (
                        Func(
                            F('start_time_booking'),
                            F('end_time_booking'),
                            function='timerange',
                            output_field=DateTimeRangeField()
                        ),
                        RangeOperators.OVERLAPS
                    ),
                ],
            ),
        ]
        indexes = [
            Index(fields=['room', 'date_booking']),
        ]
