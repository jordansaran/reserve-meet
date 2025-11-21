from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import (
    SearchFilter,
    OrderingFilter
)
from rest_framework.permissions import (
    IsAdminUser,
    IsAuthenticated
)
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_200_OK
)
from drf_yasg.utils import swagger_auto_schema
from rest_framework.viewsets import ModelViewSet
from booking.choices import BookingStatus
from booking.filters import BookingFilterSet
from booking.models import (
    Room,
    Booking,
    Resource,
    Location
)
from booking.permissions import IsManagerOrAdmin
from booking.serializers import (
    RoomSerializer,
    BookingSerializer,
    BookingListSerializer,
    ResourceSerializer,
    LocationSerializer,
    BookingCancelSerializer,
    CheckAvailabilityInputSerializer,
    CheckAvailabilityOutputSerializer
)


class RoomViewSet(ModelViewSet):
    """
    ViewSet para gerenciamento de salas.

    Permissões:
    - Leitura (list, retrieve): Usuários autenticados (user, manager, admin)
    - Escrita (create, update, delete): Apenas admins
    """
    queryset = Room.objects.select_related('location')
    serializer_class = RoomSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'location__name']
    ordering_fields = ['name', 'location__name', 'capacity']
    ordering = ['name']

    def get_permissions(self):
        """
        Usuários autenticados podem listar/visualizar salas.
        Apenas admins podem criar/editar/deletar.
        """
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        elif self.action == 'stats':
            return [IsManagerOrAdmin()]
        return [IsAdminUser()]

    @swagger_auto_schema(
        operation_description="Retorna informações completas da mídia para a tela de recorte de notícia",
        responses={200: CheckAvailabilityOutputSerializer()}
    )
    @action(
        detail=True,
        methods=['get'],
        serializer_class=CheckAvailabilityOutputSerializer,
        permission_classes=[IsAuthenticated]
    )
    def check_availability(self, request, pk=None):
        """
        Verifica a disponibilidade de uma sala em um período específico.

        Query params:
        - date: Data da reserva (YYYY-MM-DD)
        - start_time: Horário de início (HH:MM)
        - end_time: Horário de término (HH:MM)

        Retorna:
        - available: True se a sala está disponível
        - conflicting_bookings: Lista de reservas conflitantes (se houver)
        - suggestions: Sugestões de horários alternativos (se houver conflito)
        """
        from datetime import datetime, time
        from django.utils import timezone

        room = self.get_object()

        input_serializer = CheckAvailabilityInputSerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data
        date_str = validated_data['date']
        start_time_str = validated_data['start_time']
        end_time_str = validated_data['end_time']

        date_booking = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_hour, start_minute = map(int, start_time_str.split(':'))
        end_hour, end_minute = map(int, end_time_str.split(':'))

        start_datetime = timezone.make_aware(
            datetime.combine(date_booking, time(start_hour, start_minute))
        )
        end_datetime = timezone.make_aware(
            datetime.combine(date_booking, time(end_hour, end_minute))
        )

        # Busca reservas conflitantes
        conflicting_bookings = Booking.objects.filter(
            room=room,
            start_datetime__lt=end_datetime,
            end_datetime__gt=start_datetime,
            is_active=True
        ).exclude(
            status__in=[BookingStatus.CANCELLED, BookingStatus.COMPLETED]
        ).select_related('manager')

        if conflicting_bookings.exists():
            conflicts_data = [{
                'id': str(booking.id),
                'start_datetime': booking.start_datetime.isoformat(),
                'end_datetime': booking.end_datetime.isoformat(),
                'manager': booking.manager.username,
                'status': booking.status
            } for booking in conflicting_bookings]

            # Sugestões de horários alternativos na mesma sala
            suggestions = self._get_alternative_times(
                room, date_booking, start_datetime, end_datetime
            )

            output_data = {
                'available': False,
                'room_id': str(room.id),
                'room_name': room.name,
                'requested_date': date_str,
                'requested_start': start_time_str,
                'requested_end': end_time_str,
                'conflicting_bookings': conflicts_data,
                'suggestions': suggestions
            }

            output_serializer = CheckAvailabilityOutputSerializer(output_data)
            return Response(output_serializer.data)

        output_data = {
            'available': True,
            'room_id': str(room.id),
            'room_name': room.name,
            'requested_date': date_str,
            'requested_start': start_time_str,
            'requested_end': end_time_str,
            'message': 'Sala disponível no horário solicitado!'
        }

        output_serializer = CheckAvailabilityOutputSerializer(output_data)
        return Response(output_serializer.data)

    def _get_alternative_times(self, room, date, requested_start, requested_end):
        """
        Sugere horários alternativos na mesma sala e data
        """
        from django.utils import timezone
        from datetime import datetime, time, timedelta

        # Horário comercial: 08:00 às 18:00
        day_start = timezone.make_aware(datetime.combine(date, time(8, 0)))
        day_end = timezone.make_aware(datetime.combine(date, time(18, 0)))

        # Duração solicitada
        duration = requested_end - requested_start

        # Busca todas as reservas do dia nesta sala
        bookings = Booking.objects.filter(
            room=room,
            date_booking=date,
            is_active=True
        ).exclude(
            status__in=[BookingStatus.CANCELLED, BookingStatus.COMPLETED]
        ).order_by('start_datetime')

        suggestions = []
        current_time = day_start

        for booking in bookings:
            # Verifica se há espaço antes desta reserva
            if current_time + duration <= booking.start_datetime:
                suggestions.append({
                    'start_time': current_time.strftime('%H:%M'),
                    'end_time': (current_time + duration).strftime('%H:%M')
                })

            current_time = max(current_time, booking.end_datetime)

        # Verifica se há espaço depois da última reserva
        if current_time + duration <= day_end:
            suggestions.append({
                'start_time': current_time.strftime('%H:%M'),
                'end_time': (current_time + duration).strftime('%H:%M')
            })

        return suggestions[:3]  # Retorna até 3 sugestões

    @action(detail=False, methods=['get'], permission_classes=[IsManagerOrAdmin])
    def stats(self, request):
        """
        Retorna estatísticas globais de salas do sistema.

        Permissão: Apenas managers e admins

        Retorna:
        - total_rooms: Quantidade total de salas ativas
        - available_rooms: Quantidade de salas sem reservas ativas no momento
        - occupied_rooms: Quantidade de salas com reservas ativas agora
        - by_location: Lista com estatísticas por localização
        """
        from django.utils import timezone
        from django.db.models import Count, Q

        now = timezone.now()

        # Total de salas ativas
        total_rooms = Room.objects.filter(is_active=True).count()

        # Salas com reservas ativas no momento atual
        # (reservas confirmadas que estão acontecendo agora)
        occupied_rooms = Room.objects.filter(
            is_active=True,
            bookings__status=BookingStatus.CONFIRMED,
            bookings__start_datetime__lte=now,
            bookings__end_datetime__gte=now
        ).distinct().count()

        # Salas disponíveis
        available_rooms = total_rooms - occupied_rooms

        # Estatísticas por localização
        locations_stats = []
        locations = Location.objects.filter(is_active=True).prefetch_related('rooms')

        for location in locations:
            location_total = location.rooms.filter(is_active=True).count()

            location_occupied = location.rooms.filter(
                is_active=True,
                bookings__status=BookingStatus.CONFIRMED,
                bookings__start_datetime__lte=now,
                bookings__end_datetime__gte=now
            ).distinct().count()

            location_available = location_total - location_occupied

            locations_stats.append({
                'location_id': location.id,
                'location_name': location.name,
                'total_rooms': location_total,
                'available_rooms': location_available,
                'occupied_rooms': location_occupied
            })

        return Response({
            'total_rooms': total_rooms,
            'available_rooms': available_rooms,
            'occupied_rooms': occupied_rooms,
            'by_location': locations_stats,
            'timestamp': now.isoformat()
        }, status=HTTP_200_OK)


class BookingViewSet(ModelViewSet):
    """
    ViewSet para gerenciamento de reservas.

    Permissões:
    - Usuários autenticados podem criar e visualizar suas próprias reservas
    - Superusuários podem visualizar todas as reservas

    Filtros disponíveis:
    - status: Filtra por status (pending, confirmed, cancelled, completed)
    - room: Filtra por ID da sala
    - location: Filtra por ID da localização
    - date_booking: Filtra por data exata
    - date_from: Filtra reservas a partir de uma data
    - date_to: Filtra reservas até uma data
    - manager: Filtra por ID do usuário
    - search: Busca em sala, localização e nome do manager
    """

    queryset = Booking.objects.select_related(
        'room',
        'room__location',
        'manager',
        'confirmed_by',
        'cancelled_by'
    ).prefetch_related('room__resources').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = BookingFilterSet
    ordering_fields = ['date_booking', 'start_datetime', 'end_datetime', 'status']
    ordering = ['date_booking', 'start_datetime']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()

        user = self.request.user
        if user.is_superuser or user.is_staff:
            return self.queryset
        return self.queryset.filter(manager=user)

    def get_serializer_class(self):
        if self.action == 'list':
            if self.request.user.is_superuser or self.request.user.is_staff:
                return BookingListSerializer
        elif self.action == 'cancel':
            return BookingCancelSerializer
        return BookingSerializer

    def paginate_queryset(self, queryset):
        """
        Sobrescreve o método de paginação para retornar None
        quando o queryset está vazio, evitando erro de "Página inválida"
        """
        if not queryset.exists():
            return None
        return super().paginate_queryset(queryset)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def availability(self, request):
        return Room.objects.filter(bookings__isnull=True)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAdminUser]
    )
    def confirm(self, request, pk=None):
        """Confirma uma reserva"""
        booking = self.get_object()

        if booking.status != BookingStatus.PENDING:
            return Response(
                {'detail': 'Apenas reservas pendentes podem ser confirmadas.'},
                status=HTTP_400_BAD_REQUEST
            )

        booking.confirm(request.user)

        return Response(status=HTTP_200_OK)

    @action(
        detail=True,
        methods=['post'],
        serializer_class=BookingCancelSerializer,
        permission_classes=[IsAdminUser]
    )
    def cancel(self, request, pk=None):
        """

        """
        booking = self.get_object()

        if booking.status == BookingStatus.CANCELLED:
            return Response(
                {'detail': 'Esta reserva já está cancelada.'},
                status=HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get('reason')
        booking.cancel(request.user, reason)

        return Response({}, status=HTTP_200_OK)

    @action(
        detail=False,
        methods=['get']
    )
    def pending(self, request):
        """Lista reservas pendentes"""
        queryset = self.get_queryset()
        bookings = queryset.filter(status=BookingStatus.PENDING)
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)


class ResourceViewSet(ModelViewSet):
    """
    ViewSet para gerenciamento de recursos.

    Permissões:
    - Leitura (list, retrieve): Usuários autenticados (user, manager, admin)
    - Escrita (create, update, delete): Apenas admins
    """
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

    def get_permissions(self):
        """
        Usuários autenticados podem listar/visualizar recursos.
        Apenas admins podem criar/editar/deletar.
        """
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]


class LocationViewSet(ModelViewSet):
    """
    ViewSet para gerenciamento de localizações.

    Permissões:
    - Leitura (list, retrieve): Usuários autenticados (user, manager, admin)
    - Escrita (create, update, delete): Apenas admins
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

    def get_permissions(self):
        """
        Usuários autenticados podem listar/visualizar localizações.
        Apenas admins podem criar/editar/deletar.
        """
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    @action(detail=True, methods=['get'], permission_classes=[IsManagerOrAdmin])
    def rooms_stats(self, request, pk=None):
        """
        Retorna estatísticas de salas para uma localização específica.

        Permissão: Apenas managers e admins

        Retorna:
        - total_rooms: Quantidade total de salas na localização
        - available_rooms: Quantidade de salas sem reservas ativas no momento
        - occupied_rooms: Quantidade de salas com reservas ativas
        """
        from django.utils import timezone

        location = self.get_object()
        now = timezone.now()

        # Total de salas ativas na localização
        total_rooms = location.rooms.filter(is_active=True).count()

        # Salas com reservas ativas no momento atual
        # (reservas confirmadas que estão acontecendo agora)
        occupied_rooms = location.rooms.filter(
            is_active=True,
            bookings__status=BookingStatus.CONFIRMED,
            bookings__start_datetime__lte=now,
            bookings__end_datetime__gte=now
        ).distinct().count()

        # Salas disponíveis (sem reservas ativas no momento)
        available_rooms = total_rooms - occupied_rooms

        return Response({
            'location_id': location.id,
            'location_name': location.name,
            'total_rooms': total_rooms,
            'available_rooms': available_rooms,
            'occupied_rooms': occupied_rooms,
            'timestamp': now.isoformat()
        }, status=HTTP_200_OK)