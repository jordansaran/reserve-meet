"""
Testes unitários para serializers
"""
import pytest
from datetime import datetime, timedelta
from django.utils import timezone

from booking.serializers import (
    LocationSerializer,
    ResourceSerializer,
    RoomSerializer,
    BookingSerializer,
    BookingListSerializer,
)
from booking.choices import BookingStatus
from tests.factories import (
    UserFactory,
    LocationFactory,
    ResourceFactory,
    RoomFactory,
    BookingFactory,
    ConfirmedBookingFactory,
)


@pytest.mark.django_db
@pytest.mark.unit
class TestLocationSerializer:
    """Testes para LocationSerializer"""

    def test_serialize_location(self):
        """Testa serialização de uma localização"""
        location = LocationFactory(
            name='Prédio A',
            city='São Paulo',
            state='SP'
        )
        serializer = LocationSerializer(location)
        data = serializer.data

        assert data['id'] == location.id
        assert data['name'] == 'Prédio A'
        assert data['city'] == 'São Paulo'
        assert data['state'] == 'SP'
        assert data['is_active'] is True

    def test_deserialize_location(self):
        """Testa deserialização e criação de localização"""
        data = {
            'name': 'Prédio B',
            'address': 'Rua Teste, 123',
            'city': 'Rio de Janeiro',
            'state': 'RJ',
            'cep': '12345-678',
            'description': 'Descrição do prédio'
        }
        serializer = LocationSerializer(data=data)
        assert serializer.is_valid()

        location = serializer.save()
        assert location.name == 'Prédio B'
        assert location.city == 'Rio de Janeiro'
        assert location.state == 'RJ'

    def test_invalid_location_missing_required_fields(self):
        """Testa validação com campos obrigatórios faltando"""
        data = {'name': 'Prédio C'}
        serializer = LocationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'address' in serializer.errors
        assert 'city' in serializer.errors


@pytest.mark.django_db
@pytest.mark.unit
class TestResourceSerializer:
    """Testes para ResourceSerializer"""

    def test_serialize_resource(self):
        """Testa serialização de um recurso"""
        resource = ResourceFactory(name='Projetor')
        serializer = ResourceSerializer(resource)
        data = serializer.data

        assert data['id'] == resource.id
        assert data['name'] == 'Projetor'
        assert data['is_active'] is True

    def test_deserialize_resource(self):
        """Testa deserialização e criação de recurso"""
        data = {
            'name': 'Ar Condicionado',
            'description': 'Sistema de ar condicionado'
        }
        serializer = ResourceSerializer(data=data)
        assert serializer.is_valid()

        resource = serializer.save()
        assert resource.name == 'Ar Condicionado'


@pytest.mark.django_db
@pytest.mark.unit
class TestRoomSerializer:
    """Testes para RoomSerializer"""

    def test_serialize_room(self, room):
        """Testa serialização de uma sala"""
        serializer = RoomSerializer(room)
        data = serializer.data

        assert data['id'] == room.id
        assert data['name'] == room.name
        assert data['capacity'] == room.capacity
        assert data['location'] == room.location.id
        assert 'all_bookings' in data

    def test_room_bookings_count(self, room):
        """Testa contagem de reservas na sala"""
        BookingFactory.create_batch(3, room=room)
        serializer = RoomSerializer(room)
        data = serializer.data

        assert data['all_bookings'] == 3

    def test_deserialize_room(self, location):
        """Testa deserialização e criação de sala"""
        data = {
            'name': 'Sala 201',
            'location': location.id,
            'capacity': 20,
        }
        serializer = RoomSerializer(data=data)
        assert serializer.is_valid()

        room = serializer.save()
        assert room.name == 'Sala 201'
        assert room.capacity == 20
        assert room.location == location

    def test_room_with_resources(self, location, multiple_resources):
        """Testa serialização de sala com recursos"""
        data = {
            'name': 'Sala 301',
            'location': location.id,
            'capacity': 15,
            'resources': [r.id for r in multiple_resources]
        }
        serializer = RoomSerializer(data=data)
        assert serializer.is_valid()

        room = serializer.save()
        assert room.resources.count() == len(multiple_resources)


@pytest.mark.django_db
@pytest.mark.unit
class TestBookingSerializer:
    """Testes para BookingSerializer"""

    def test_serialize_booking(self, booking):
        """Testa serialização de uma reserva"""
        serializer = BookingSerializer(booking)
        data = serializer.data

        assert data['id'] == booking.id
        assert data['manager'] == booking.manager.id
        assert data['manager_name'] == booking.manager.username
        assert data['room'] == booking.room.id
        assert data['room_name'] == booking.room.name
        assert data['status'] == booking.status
        assert 'status_display' in data

    def test_booking_status_display(self, booking):
        """Testa campo status_display"""
        serializer = BookingSerializer(booking)
        data = serializer.data

        assert data['status_display'] == booking.get_status_display()

    def test_booking_confirmed_fields(self, confirmed_booking):
        """Testa campos de confirmação em reserva confirmada"""
        serializer = BookingSerializer(confirmed_booking)
        data = serializer.data

        assert data['status'] == BookingStatus.CONFIRMED
        assert data['confirmed_by'] == confirmed_booking.confirmed_by.id
        assert data['confirmed_by_name'] == confirmed_booking.confirmed_by.username
        assert data['confirmed_at'] is not None

    def test_deserialize_booking(self, user, room):
        """Testa deserialização e criação de reserva"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)

        data = {
            'manager': user.id,
            'room': room.id,
            'date_booking': start.date(),
            'start_datetime': start,
            'end_datetime': end,
            'has_coffee_break': True,
            'coffee_break_headcount': 10,
            'notes': 'Reunião importante'
        }
        serializer = BookingSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        booking = serializer.save()
        assert booking.manager == user
        assert booking.room == room
        assert booking.has_coffee_break is True
        assert booking.coffee_break_headcount == 10

    def test_booking_read_only_fields(self, user, room):
        """Testa que campos read_only não podem ser escritos"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        another_user = UserFactory()

        data = {
            'manager': user.id,
            'room': room.id,
            'date_booking': start.date(),
            'start_datetime': start,
            'end_datetime': end,
            'confirmed_by': another_user.id,  # Campo read_only
            'confirmed_at': timezone.now(),   # Campo read_only
        }
        serializer = BookingSerializer(data=data)
        assert serializer.is_valid()

        booking = serializer.save()
        # Campos read_only devem ser None
        assert booking.confirmed_by is None
        assert booking.confirmed_at is None


@pytest.mark.django_db
@pytest.mark.unit
class TestBookingListSerializer:
    """Testes para BookingListSerializer"""

    def test_serialize_booking_list(self, booking):
        """Testa serialização resumida de reserva"""
        serializer = BookingListSerializer(booking)
        data = serializer.data

        assert data['id'] == booking.id
        assert data['room_name'] == booking.room.name
        assert data['location'] == booking.room.location.name
        assert 'manager' in data
        assert 'date_booking' in data
        assert 'start_datetime' in data
        assert 'end_datetime' in data

    def test_booking_list_has_limited_fields(self, booking):
        """Testa que BookingListSerializer tem campos limitados"""
        serializer = BookingListSerializer(booking)
        data = serializer.data

        # Não deve ter todos os campos do BookingSerializer
        assert 'notes' not in data
        assert 'status' not in data
        assert 'confirmed_by' not in data
        assert 'cancelled_by' not in data

    def test_serialize_multiple_bookings(self, multiple_bookings):
        """Testa serialização de múltiplas reservas"""
        serializer = BookingListSerializer(multiple_bookings, many=True)
        data = serializer.data

        assert len(data) == len(multiple_bookings)
        for item in data:
            assert 'room_name' in item
            assert 'location' in item
