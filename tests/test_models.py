"""
Testes unitários para os modelos
"""
import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from core.models import User
from core.choices import UserRoles
from booking.models import Location, Resource, Room, Booking
from booking.choices import BookingStatus
from tests.factories import (
    UserFactory,
    AdminUserFactory,
    LocationFactory,
    ResourceFactory,
    RoomFactory,
    BookingFactory,
)


@pytest.mark.django_db
@pytest.mark.unit
class TestUserModel:
    """Testes para o modelo User"""

    def test_create_user(self):
        """Testa criação de usuário comum"""
        user = UserFactory()
        assert user.id is not None
        assert user.email is not None
        assert user.username is not None
        assert user.role == UserRoles.USER
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_admin_user(self):
        """Testa criação de usuário admin"""
        admin = AdminUserFactory()
        assert admin.role == UserRoles.ADMIN
        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_user_str_representation(self):
        """Testa representação string do usuário"""
        user = UserFactory(email='test@example.com')
        str_repr = str(user)
        assert user.email in str_repr
        assert user.role in str_repr

    def test_user_email_unique(self):
        """Testa que email deve ser único"""
        UserFactory(email='test@example.com')
        with pytest.raises(IntegrityError):
            UserFactory(email='test@example.com')

    def test_user_username_unique(self):
        """Testa que username deve ser único"""
        UserFactory(username='testuser')
        with pytest.raises(IntegrityError):
            UserFactory(username='testuser')

    def test_user_password_is_hashed(self):
        """Testa que a senha é armazenada como hash"""
        user = UserFactory(password='testpass123')
        assert user.password != 'testpass123'
        assert user.check_password('testpass123')

    def test_user_full_name(self):
        """Testa nome completo do usuário"""
        user = UserFactory(first_name='John', last_name='Doe')
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'


@pytest.mark.django_db
@pytest.mark.unit
class TestLocationModel:
    """Testes para o modelo Location"""

    def test_create_location(self):
        """Testa criação de localização"""
        location = LocationFactory()
        assert location.id is not None
        assert location.name is not None
        assert location.address is not None
        assert location.city is not None
        assert location.state is not None
        assert location.cep is not None
        assert location.is_active is True

    def test_location_str_representation(self):
        """Testa representação string da localização"""
        location = LocationFactory(name='Prédio A')
        assert str(location) == 'Prédio A'

    def test_location_name_unique(self):
        """Testa que nome da localização deve ser único"""
        LocationFactory(name='Prédio A')
        with pytest.raises(IntegrityError):
            LocationFactory(name='Prédio A')

    def test_location_state_uppercase(self):
        """Testa que estado é convertido para maiúsculo"""
        location = LocationFactory(state='sp')
        location.clean()
        assert location.state == 'SP'

    def test_location_has_rooms_relationship(self):
        """Testa relacionamento com salas"""
        location = LocationFactory()
        room = RoomFactory(location=location)
        assert room in location.rooms.all()
        assert location.rooms.count() == 1


@pytest.mark.django_db
@pytest.mark.unit
class TestResourceModel:
    """Testes para o modelo Resource"""

    def test_create_resource(self):
        """Testa criação de recurso"""
        resource = ResourceFactory()
        assert resource.id is not None
        assert resource.name is not None
        assert resource.description is not None
        assert resource.is_active is True

    def test_resource_str_representation(self):
        """Testa representação string do recurso"""
        resource = ResourceFactory(name='Projetor')
        assert str(resource) == 'Projetor'

    def test_resource_name_unique(self):
        """Testa que nome do recurso deve ser único"""
        ResourceFactory(name='Projetor')
        with pytest.raises(IntegrityError):
            ResourceFactory(name='Projetor')


@pytest.mark.django_db
@pytest.mark.unit
class TestRoomModel:
    """Testes para o modelo Room"""

    def test_create_room(self):
        """Testa criação de sala"""
        room = RoomFactory()
        assert room.id is not None
        assert room.name is not None
        assert room.location is not None
        assert room.capacity > 0
        assert room.is_active is True

    def test_room_str_representation(self):
        """Testa representação string da sala"""
        location = LocationFactory(name='Prédio A')
        room = RoomFactory(name='Sala 101', location=location, capacity=10)
        str_repr = str(room)
        assert 'Sala 101' in str_repr
        assert 'Prédio A' in str_repr
        assert '10' in str_repr

    def test_room_with_resources(self):
        """Testa sala com recursos"""
        resources = ResourceFactory.create_batch(3)
        room = RoomFactory(resources=resources)
        assert room.resources.count() == 3

    def test_room_unique_name_per_location(self):
        """Testa que nome da sala deve ser único por localização"""
        location = LocationFactory()
        RoomFactory(name='Sala 101', location=location)
        with pytest.raises(IntegrityError):
            RoomFactory(name='Sala 101', location=location)

    def test_room_same_name_different_location(self):
        """Testa que pode haver salas com mesmo nome em localizações diferentes"""
        location1 = LocationFactory()
        location2 = LocationFactory()
        room1 = RoomFactory(name='Sala 101', location=location1)
        room2 = RoomFactory(name='Sala 101', location=location2)
        assert room1.name == room2.name
        assert room1.location != room2.location

    def test_room_capacity_positive(self):
        """Testa que capacidade deve ser positiva"""
        room = RoomFactory(capacity=10)
        assert room.capacity == 10

    def test_room_delete_cascade(self):
        """Testa que deletar localização deleta as salas"""
        location = LocationFactory()
        room = RoomFactory(location=location)
        room_id = room.id
        location.delete()
        assert not Room.objects.filter(id=room_id).exists()


@pytest.mark.django_db
@pytest.mark.unit
class TestBookingModel:
    """Testes para o modelo Booking"""

    def test_create_booking(self):
        """Testa criação de reserva"""
        booking = BookingFactory()
        assert booking.id is not None
        assert booking.manager is not None
        assert booking.room is not None
        assert booking.date_booking is not None
        assert booking.start_datetime is not None
        assert booking.end_datetime is not None
        assert booking.status == BookingStatus.PENDING
        assert booking.is_active is True

    def test_booking_str_representation(self):
        """Testa representação string da reserva"""
        booking = BookingFactory()
        str_repr = str(booking)
        assert str(booking.room) in str_repr
        assert str(booking.date_booking) in str_repr

    def test_booking_default_status_pending(self):
        """Testa que status padrão é PENDING"""
        booking = BookingFactory()
        assert booking.status == BookingStatus.PENDING

    def test_booking_confirm_method(self):
        """Testa método de confirmar reserva"""
        user = UserFactory()
        booking = BookingFactory()
        booking.confirm(user)

        assert booking.status == BookingStatus.CONFIRMED
        assert booking.confirmed_by == user
        assert booking.confirmed_at is not None

    def test_booking_cancel_method(self):
        """Testa método de cancelar reserva"""
        user = UserFactory()
        booking = BookingFactory()
        reason = "Reunião adiada"
        booking.cancel(user, reason)

        assert booking.status == BookingStatus.CANCELLED
        assert booking.cancelled_by == user
        assert booking.cancelled_at is not None
        assert booking.cancellation_reason == reason

    def test_booking_complete_method(self):
        """Testa método de completar reserva"""
        booking = BookingFactory()
        booking.complete()

        assert booking.status == BookingStatus.COMPLETED

    def test_booking_is_confirmed_property(self):
        """Testa propriedade is_confirmed"""
        booking = BookingFactory()
        assert booking.is_confirmed is False

        booking.status = BookingStatus.CONFIRMED
        booking.save()
        assert booking.is_confirmed is True

    def test_booking_is_pending_property(self):
        """Testa propriedade is_pending"""
        booking = BookingFactory()
        assert booking.is_pending is True

        booking.status = BookingStatus.CONFIRMED
        booking.save()
        assert booking.is_pending is False

    def test_booking_is_cancelled_property(self):
        """Testa propriedade is_cancelled"""
        booking = BookingFactory()
        assert booking.is_cancelled is False

        booking.status = BookingStatus.CANCELLED
        booking.save()
        assert booking.is_cancelled is True

    def test_booking_coffee_break_default(self):
        """Testa valores padrão de coffee break"""
        booking = BookingFactory()
        assert booking.has_coffee_break is False
        assert booking.coffee_break_headcount == 1

    def test_booking_with_coffee_break(self):
        """Testa reserva com coffee break"""
        booking = BookingFactory(
            has_coffee_break=True,
            coffee_break_headcount=15
        )
        assert booking.has_coffee_break is True
        assert booking.coffee_break_headcount == 15

    def test_booking_end_after_start(self):
        """Testa que data fim é após data início"""
        booking = BookingFactory()
        assert booking.end_datetime > booking.start_datetime

    def test_booking_delete_cascade_user(self):
        """Testa que deletar usuário deleta as reservas"""
        user = UserFactory()
        booking = BookingFactory(manager=user)
        booking_id = booking.id
        user.delete()
        assert not Booking.objects.filter(id=booking_id).exists()

    def test_booking_delete_cascade_room(self):
        """Testa que deletar sala deleta as reservas"""
        room = RoomFactory()
        booking = BookingFactory(room=room)
        booking_id = booking.id
        room.delete()
        assert not Booking.objects.filter(id=booking_id).exists()
