from django_filters import FilterSet, CharFilter, DateFilter, NumberFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from booking.choices import BookingStatus
from booking.models import Booking


class BookingFilterSet(FilterSet):
    """
    FilterSet customizado para filtrar reservas.

    Filtros disponíveis:
    - status: Filtra por status exato (pending, confirmed, cancelled, completed)
    - room: Filtra por ID da sala
    - location: Filtra por ID da localização
    - date_booking: Filtra por data exata da reserva
    - date_from: Filtra reservas a partir de uma data
    - date_to: Filtra reservas até uma data
    - manager: Filtra por ID do usuário que criou a reserva
    - search: Busca em múltiplos campos (nome da sala, localização, nome do manager)
    """

    # Filtro de status específicos
    status = CharFilter(
        field_name='status',
        lookup_expr='exact',
        help_text='Filtra por status: pending, confirmed, cancelled, completed'
    )

    # Filtro por sala
    room = NumberFilter(
        field_name='room',
        lookup_expr='exact',
        help_text='Filtra por ID da sala'
    )

    # Filtro por localização (através da sala)
    location = NumberFilter(
        field_name='room__location',
        lookup_expr='exact',
        help_text='Filtra por ID da localização'
    )

    # Filtro por data exata
    date_booking = DateFilter(
        field_name='date_booking',
        lookup_expr='exact',
        help_text='Filtra por data exata da reserva (formato: YYYY-MM-DD)'
    )

    # Filtro de intervalo de datas
    date_from = DateFilter(
        field_name='date_booking',
        lookup_expr='gte',
        help_text='Filtra reservas a partir desta data (formato: YYYY-MM-DD)'
    )

    date_to = DateFilter(
        field_name='date_booking',
        lookup_expr='lte',
        help_text='Filtra reservas até esta data (formato: YYYY-MM-DD)'
    )

    # Filtro por manager
    manager = NumberFilter(
        field_name='manager',
        lookup_expr='exact',
        help_text='Filtra por ID do usuário que criou a reserva'
    )

    # Filtro de busca geral
    search = CharFilter(
        method='filter_search',
        help_text='Busca em nome da sala, localização e nome do manager'
    )

    def filter_search(self, queryset, name, value):
        """
        Método customizado para buscar em múltiplos campos.
        Busca por:
        - Nome da sala
        - Nome da localização
        - Nome do manager (username)
        - Nome do manager (first_name e last_name)
        """
        return queryset.filter(
            Q(room__name__icontains=value) |
            Q(room__location__name__icontains=value) |
            Q(manager__username__icontains=value) |
            Q(manager__first_name__icontains=value) |
            Q(manager__last_name__icontains=value)
        )

    class Meta:
        model = Booking
        fields = [
            'status',
            'room',
            'location',
            'date_booking',
            'date_from',
            'date_to',
            'manager',
            'search'
        ]
