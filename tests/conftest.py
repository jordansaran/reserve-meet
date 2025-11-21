"""
Fixtures compartilhadas para todos os testes
"""
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from tests.factories import (
    UserFactory,
    AdminUserFactory,
    ManagerUserFactory,
    LocationFactory,
    ResourceFactory,
    RoomFactory,
    BookingFactory,
    ConfirmedBookingFactory,
    CancelledBookingFactory,
)


User = get_user_model()


@pytest.fixture
def api_client():
    """Cliente da API REST sem autenticação"""
    return APIClient()


@pytest.fixture
def user(db):
    """Usuário comum"""
    return UserFactory()


@pytest.fixture
def admin_user(db):
    """Usuário administrador"""
    return AdminUserFactory()


@pytest.fixture
def manager_user(db):
    """Usuário gerente"""
    return ManagerUserFactory()


@pytest.fixture
def authenticated_client(db, user):
    """Cliente autenticado com usuário comum"""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin_client(db, admin_user):
    """Cliente autenticado como admin"""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def manager_client(db, manager_user):
    """Cliente autenticado como gerente"""
    client = APIClient()
    client.force_authenticate(user=manager_user)
    return client


@pytest.fixture
def location(db):
    """Localização básica"""
    return LocationFactory()


@pytest.fixture
def multiple_locations(db):
    """Múltiplas localizações"""
    return LocationFactory.create_batch(3)


@pytest.fixture
def resource(db):
    """Recurso básico"""
    return ResourceFactory()


@pytest.fixture
def multiple_resources(db):
    """Múltiplos recursos"""
    return ResourceFactory.create_batch(5)


@pytest.fixture
def room(db, location):
    """Sala básica"""
    return RoomFactory(location=location)


@pytest.fixture
def room_with_resources(db, location, multiple_resources):
    """Sala com recursos"""
    return RoomFactory(location=location, resources=multiple_resources)


@pytest.fixture
def multiple_rooms(db, location):
    """Múltiplas salas na mesma localização"""
    return RoomFactory.create_batch(3, location=location)


@pytest.fixture
def booking(db, user, room):
    """Reserva básica"""
    return BookingFactory(manager=user, room=room)


@pytest.fixture
def confirmed_booking(db, user, room, manager_user):
    """Reserva confirmada"""
    return ConfirmedBookingFactory(
        manager=user,
        room=room,
        confirmed_by=manager_user
    )


@pytest.fixture
def cancelled_booking(db, user, room):
    """Reserva cancelada"""
    return CancelledBookingFactory(
        manager=user,
        room=room,
        cancelled_by=user
    )


@pytest.fixture
def multiple_bookings(db, user, room):
    """Múltiplas reservas"""
    return BookingFactory.create_batch(5, manager=user, room=room)
