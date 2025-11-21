from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import (
    ModelSerializer,
    CharField, Serializer
)
from django.utils.translation import gettext_lazy as _
from booking.models import (
    Room,
    Booking, Location, Resource
)


class RoomSerializer(ModelSerializer):
    all_bookings = SerializerMethodField()

    class Meta:
        model = Room
        fields = '__all__'

    def get_all_bookings(self, obj):
        return obj.bookings.count()


class BookingSerializer(ModelSerializer):
    status_display = CharField(source='get_status_display', read_only=True)
    manager_name = CharField(source='manager.username', read_only=True)
    room_name = CharField(source='room.name', read_only=True)
    confirmed_by_name = CharField(source='confirmed_by.username', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'manager',
            'manager_name',
            'room',
            'room_name',
            'date_booking',
            'start_datetime',
            'end_datetime',
            'has_coffee_break',
            'coffee_break_headcount',
            'status',
            'status_display',
            'confirmed_by',
            'confirmed_by_name',
            'confirmed_at',
            'cancelled_by',
            'cancelled_at',
            'cancellation_reason',
            'notes',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'confirmed_by',
            'confirmed_at',
            'cancelled_by',
            'cancelled_at',
            'created_at',
            'updated_at'
        ]

    def validate(self, attrs):
        """
        Valida se há conflito de horário com reservas existentes
        """
        room = attrs.get('room')
        start_datetime = attrs.get('start_datetime')
        end_datetime = attrs.get('end_datetime')

        # Para update, ignora a própria reserva
        instance_id = self.instance.id if self.instance else None

        # Verifica se há reservas conflitantes
        conflicting_bookings = Booking.objects.filter(
            room=room,
            start_datetime__lt=end_datetime,  # Começa antes de terminar
            end_datetime__gt=start_datetime,  # Termina depois de começar
            is_active=True
        ).exclude(
            status__in=['cancelled', 'completed']  # Ignora canceladas e concluídas
        )

        # Se for update, exclui a própria reserva
        if instance_id:
            conflicting_bookings = conflicting_bookings.exclude(id=instance_id)

        if conflicting_bookings.exists():
            # Pega os detalhes da primeira reserva conflitante
            conflict = conflicting_bookings.first()

            raise ValidationError({
                'non_field_errors': [
                    _(
                        f"Conflito de horário! A sala '{room.name}' já está reservada "
                        f"das {conflict.start_datetime.strftime('%H:%M')} "
                        f"às {conflict.end_datetime.strftime('%H:%M')} "
                        f"no dia {conflict.date_booking.strftime('%d/%m/%Y')}."
                    )
                ],
                'conflicting_booking_id': conflict.id,
                'conflicting_start': conflict.start_datetime.isoformat(),
                'conflicting_end': conflict.end_datetime.isoformat(),
                'conflicting_manager': conflict.manager.username
            })

        return attrs


class BookingListSerializer(ModelSerializer):

    status_display = CharField(source='get_status_display', read_only=True)
    room_name = CharField(source='room.name', read_only=True)
    room_capacity = SerializerMethodField()
    room_resources = SerializerMethodField()
    location = CharField(source='room.location.name', read_only=True)
    location_address = CharField(source='room.location.address', read_only=True)
    location_city = CharField(source='room.location.city', read_only=True)
    manager_name = SerializerMethodField()
    manager_email = CharField(source='manager.email', read_only=True)
    manager_phone = CharField(source='manager.phone', read_only=True)
    confirmed_by_name = SerializerMethodField()
    cancelled_by_name = SerializerMethodField()
    duration_minutes = SerializerMethodField()

    def get_room_capacity(self, obj):
        """Retorna a capacidade da sala"""
        return obj.room.capacity if obj.room else None

    def get_room_resources(self, obj):
        """Retorna lista de recursos disponíveis na sala"""
        if obj.room:
            return [resource.name for resource in obj.room.resources.all()]
        return []

    def get_manager_name(self, obj):
        """Retorna nome completo do manager"""
        if obj.manager:
            full_name = f"{obj.manager.first_name} {obj.manager.last_name}".strip()
            return full_name if full_name else obj.manager.username
        return None

    def get_confirmed_by_name(self, obj):
        """Retorna nome completo de quem confirmou"""
        if obj.confirmed_by:
            full_name = f"{obj.confirmed_by.first_name} {obj.confirmed_by.last_name}".strip()
            return full_name if full_name else obj.confirmed_by.username
        return None

    def get_cancelled_by_name(self, obj):
        """Retorna nome completo de quem cancelou"""
        if obj.cancelled_by:
            full_name = f"{obj.cancelled_by.first_name} {obj.cancelled_by.last_name}".strip()
            return full_name if full_name else obj.cancelled_by.username
        return None

    def get_duration_minutes(self, obj):
        """Calcula a duração da reunião em minutos"""
        if obj.start_datetime and obj.end_datetime:
            duration = obj.end_datetime - obj.start_datetime
            return int(duration.total_seconds() / 60)
        return None

    class Meta:
        model = Booking
        fields = [
            'id',
            'room',
            'room_name',
            'room_capacity',
            'room_resources',
            'location',
            'location_address',
            'location_city',
            'date_booking',
            'start_datetime',
            'end_datetime',
            'duration_minutes',
            'manager',
            'manager_name',
            'manager_email',
            'manager_phone',
            'has_coffee_break',
            'coffee_break_headcount',
            'status',
            'status_display',
            'is_active',
            'confirmed_by',
            'confirmed_by_name',
            'confirmed_at',
            'cancelled_by',
            'cancelled_by_name',
            'cancelled_at',
            'cancellation_reason',
            'notes'
        ]


class BookingListToUserSerializer(ModelSerializer):

    status_display = CharField(source='get_status_display', read_only=True)
    room_name = CharField(source='room.name', read_only=True)
    room_capacity = SerializerMethodField()
    room_resources = SerializerMethodField()
    location = CharField(source='room.location.name', read_only=True)
    location_address = CharField(source='room.location.address', read_only=True)
    location_city = CharField(source='room.location.city', read_only=True)
    manager_name = SerializerMethodField()
    manager_email = CharField(source='manager.email', read_only=True)
    manager_phone = CharField(source='manager.phone', read_only=True)
    confirmed_by_name = SerializerMethodField()
    cancelled_by_name = SerializerMethodField()
    duration_minutes = SerializerMethodField()

    def get_room_capacity(self, obj):
        """Retorna a capacidade da sala"""
        return obj.room.capacity if obj.room else None

    def get_room_resources(self, obj):
        """Retorna lista de recursos disponíveis na sala"""
        if obj.room:
            return [resource.name for resource in obj.room.resources.all()]
        return []

    def get_manager_name(self, obj):
        """Retorna nome completo do manager"""
        if obj.manager:
            full_name = f"{obj.manager.first_name} {obj.manager.last_name}".strip()
            return full_name if full_name else obj.manager.username
        return None

    def get_confirmed_by_name(self, obj):
        """Retorna nome completo de quem confirmou"""
        if obj.confirmed_by:
            full_name = f"{obj.confirmed_by.first_name} {obj.confirmed_by.last_name}".strip()
            return full_name if full_name else obj.confirmed_by.username
        return None

    def get_cancelled_by_name(self, obj):
        """Retorna nome completo de quem cancelou"""
        if obj.cancelled_by:
            full_name = f"{obj.cancelled_by.first_name} {obj.cancelled_by.last_name}".strip()
            return full_name if full_name else obj.cancelled_by.username
        return None

    def get_duration_minutes(self, obj):
        """Calcula a duração da reunião em minutos"""
        if obj.start_datetime and obj.end_datetime:
            duration = obj.end_datetime - obj.start_datetime
            return int(duration.total_seconds() / 60)
        return None

    class Meta:
        model = Booking
        fields = [
            'id',
            'room',
            'room_name',
            'room_capacity',
            'room_resources',
            'location',
            'location_address',
            'location_city',
            'date_booking',
            'start_datetime',
            'end_datetime',
            'duration_minutes',
            'manager',
            'manager_name',
            'manager_email',
            'manager_phone',
            'has_coffee_break',
            'coffee_break_headcount',
            'status',
            'status_display',
            'is_active',
            'confirmed_by',
            'confirmed_by_name',
            'confirmed_at',
            'cancelled_by',
            'cancelled_by_name',
            'cancelled_at',
            'cancellation_reason',
            'notes'
        ]


class BookingCancelSerializer(Serializer):
    reason = CharField(required=False, help_text=_("Motivo do cancelamento"))


class CheckAvailabilityInputSerializer(Serializer):
    """
    Serializer para validar entrada do check_availability
    """
    date = CharField(
        required=True,
        help_text=_("Data da reserva no formato YYYY-MM-DD")
    )
    start_time = CharField(
        required=True,
        help_text=_("Horário de início no formato HH:MM")
    )
    end_time = CharField(
        required=True,
        help_text=_("Horário de término no formato HH:MM")
    )

    def validate_date(self, value):
        """Valida formato da data"""
        from datetime import datetime
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return value
        except ValueError:
            raise ValidationError(_("Formato de data inválido. Use YYYY-MM-DD"))

    def validate_start_time(self, value):
        """Valida formato do horário de início"""
        import re
        if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', value):
            raise ValidationError(_("Formato inválido. Use HH:MM (ex: 09:00, 14:30)"))
        return value

    def validate_end_time(self, value):
        """Valida formato do horário de término"""
        import re
        if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', value):
            raise ValidationError(_("Formato inválido. Use HH:MM (ex: 09:00, 14:30)"))
        return value

    def validate(self, attrs):
        """Valida que end_time > start_time"""
        start_str = attrs.get('start_time')
        end_str = attrs.get('end_time')

        if start_str and end_str:
            start_hour, start_min = map(int, start_str.split(':'))
            end_hour, end_min = map(int, end_str.split(':'))

            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min

            if end_minutes <= start_minutes:
                raise ValidationError({
                    'end_time': _("Horário de término deve ser posterior ao horário de início")
                })

        return attrs


class ConflictingBookingSerializer(Serializer):
    """Serializer para informações de reserva conflitante"""
    id = CharField(read_only=True)
    start_datetime = CharField(read_only=True)
    end_datetime = CharField(read_only=True)
    manager = CharField(read_only=True)
    status = CharField(read_only=True)


class AlternativeTimeSerializer(Serializer):
    """Serializer para sugestões de horários alternativos"""
    start_time = CharField(read_only=True)
    end_time = CharField(read_only=True)


class CheckAvailabilityOutputSerializer(Serializer):
    """Serializer para resposta do check_availability"""
    available = CharField(read_only=True)
    room_id = CharField(read_only=True)
    room_name = CharField(read_only=True)
    requested_date = CharField(read_only=True)
    requested_start = CharField(read_only=True)
    requested_end = CharField(read_only=True)
    message = CharField(read_only=True, required=False)
    conflicting_bookings = ConflictingBookingSerializer(many=True, read_only=True, required=False)
    suggestions = AlternativeTimeSerializer(many=True, read_only=True, required=False)


class ResourceSerializer(ModelSerializer):

    class Meta:
        model = Resource
        fields = '__all__'


class LocationSerializer(ModelSerializer):

    class Meta:
        model = Location
        fields = '__all__'
