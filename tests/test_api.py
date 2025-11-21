"""
Testes de integração para API endpoints
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework import status

from booking.models import Location, Resource, Room, Booking
from booking.choices import BookingStatus
from tests.factories import (
    UserFactory,
    AdminUserFactory,
    ManagerUserFactory,
    LocationFactory,
    ResourceFactory,
    RoomFactory,
    BookingFactory,
    ConfirmedBookingFactory,
)


@pytest.mark.django_db
@pytest.mark.integration
class TestLocationAPI:
    """Testes para API de Localizações"""

    def test_list_locations_requires_admin(self, api_client, location):
        """Testa que listar localizações requer autenticação de admin"""
        url = reverse('location-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_locations_authenticated_user_forbidden(
        self, authenticated_client, location
    ):
        """Testa que usuário comum não pode listar localizações"""
        url = reverse('location-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_locations_as_admin(self, admin_client, multiple_locations):
        """Testa listar localizações como admin"""
        url = reverse('location-list')
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= len(multiple_locations)

    def test_create_location_as_admin(self, admin_client):
        """Testa criar localização como admin"""
        url = reverse('location-list')
        data = {
            'name': 'Prédio Novo',
            'address': 'Rua Nova, 123',
            'city': 'São Paulo',
            'state': 'SP',
            'cep': '12345-678',
            'description': 'Nova localização'
        }
        response = admin_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Prédio Novo'

    def test_retrieve_location_as_admin(self, admin_client, location):
        """Testa recuperar detalhes de localização"""
        url = reverse('location-detail', kwargs={'pk': location.pk})
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == location.id
        assert response.data['name'] == location.name

    def test_update_location_as_admin(self, admin_client, location):
        """Testa atualizar localização"""
        url = reverse('location-detail', kwargs={'pk': location.pk})
        data = {'name': 'Prédio Atualizado'}
        response = admin_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Prédio Atualizado'

    def test_delete_location_as_admin(self, admin_client, location):
        """Testa deletar localização"""
        url = reverse('location-detail', kwargs={'pk': location.pk})
        response = admin_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Location.objects.filter(pk=location.pk).exists()


@pytest.mark.django_db
@pytest.mark.integration
class TestResourceAPI:
    """Testes para API de Recursos"""

    def test_list_resources_requires_admin(self, api_client, resource):
        """Testa que listar recursos requer admin"""
        url = reverse('resource-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_resources_as_admin(self, admin_client, multiple_resources):
        """Testa listar recursos como admin"""
        url = reverse('resource-list')
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= len(multiple_resources)

    def test_create_resource_as_admin(self, admin_client):
        """Testa criar recurso como admin"""
        url = reverse('resource-list')
        data = {
            'name': 'Novo Projetor',
            'description': 'Projetor de última geração'
        }
        response = admin_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Novo Projetor'

    def test_search_resources(self, admin_client):
        """Testa busca de recursos"""
        ResourceFactory(name='Projetor HD')
        ResourceFactory(name='Ar Condicionado')
        url = reverse('resource-list') + '?search=Projetor'
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert 'Projetor' in response.data[0]['name']


@pytest.mark.django_db
@pytest.mark.integration
class TestRoomAPI:
    """Testes para API de Salas"""

    def test_list_rooms_requires_admin(self, api_client, room):
        """Testa que listar salas requer admin"""
        url = reverse('room-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_rooms_as_admin(self, admin_client, multiple_rooms):
        """Testa listar salas como admin"""
        url = reverse('room-list')
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= len(multiple_rooms)

    def test_create_room_as_admin(self, admin_client, location):
        """Testa criar sala como admin"""
        url = reverse('room-list')
        data = {
            'name': 'Sala Nova',
            'location': location.id,
            'capacity': 20
        }
        response = admin_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Sala Nova'
        assert response.data['capacity'] == 20

    def test_create_room_with_resources(
        self, admin_client, location, multiple_resources
    ):
        """Testa criar sala com recursos"""
        url = reverse('room-list')
        data = {
            'name': 'Sala Completa',
            'location': location.id,
            'capacity': 30,
            'resources': [r.id for r in multiple_resources]
        }
        response = admin_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data['resources']) == len(multiple_resources)

    def test_room_bookings_count(self, admin_client, room):
        """Testa contagem de reservas na sala"""
        BookingFactory.create_batch(3, room=room)
        url = reverse('room-detail', kwargs={'pk': room.pk})
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['all_bookings'] == 3

    def test_search_rooms(self, admin_client, location):
        """Testa busca de salas"""
        RoomFactory(name='Sala Executiva', location=location)
        RoomFactory(name='Sala Reunião', location=location)
        url = reverse('room-list') + '?search=Executiva'
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert 'Executiva' in response.data[0]['name']


@pytest.mark.django_db
@pytest.mark.integration
class TestBookingAPI:
    """Testes para API de Reservas"""

    def test_list_bookings_requires_authentication(self, api_client, booking):
        """Testa que listar reservas requer autenticação"""
        url = reverse('booking-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_bookings_as_user(self, authenticated_client, user, room):
        """Testa que usuário vê apenas suas próprias reservas"""
        # Criar reservas do próprio usuário
        BookingFactory.create_batch(3, manager=user, room=room)
        # Criar reserva de outro usuário
        other_user = UserFactory()
        BookingFactory(manager=other_user, room=room)

        url = reverse('booking-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3  # Apenas as do usuário

    def test_list_bookings_as_admin_sees_all(self, admin_client, room):
        """Testa que admin vê todas as reservas"""
        user1 = UserFactory()
        user2 = UserFactory()
        BookingFactory.create_batch(2, manager=user1, room=room)
        BookingFactory.create_batch(2, manager=user2, room=room)

        url = reverse('booking-list')
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 4

    def test_create_booking(self, authenticated_client, user, room):
        """Testa criar reserva"""
        url = reverse('booking-list')
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)

        data = {
            'manager': user.id,
            'room': room.id,
            'date_booking': start.date().isoformat(),
            'start_datetime': start.isoformat(),
            'end_datetime': end.isoformat(),
            'has_coffee_break': True,
            'coffee_break_headcount': 15,
            'notes': 'Reunião importante'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == BookingStatus.PENDING
        assert response.data['has_coffee_break'] is True

    def test_retrieve_booking(self, authenticated_client, booking):
        """Testa recuperar detalhes de reserva"""
        url = reverse('booking-detail', kwargs={'pk': booking.pk})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == booking.id

    def test_update_booking(self, authenticated_client, booking):
        """Testa atualizar reserva"""
        url = reverse('booking-detail', kwargs={'pk': booking.pk})
        data = {'notes': 'Notas atualizadas'}
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['notes'] == 'Notas atualizadas'

    def test_delete_booking(self, authenticated_client, booking):
        """Testa deletar reserva"""
        url = reverse('booking-detail', kwargs={'pk': booking.pk})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_confirm_booking(self, manager_client, manager_user, user, room):
        """Testa confirmar reserva"""
        booking = BookingFactory(manager=user, room=room, status=BookingStatus.PENDING)
        url = reverse('booking-confirm', kwargs={'pk': booking.pk})
        response = manager_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == BookingStatus.CONFIRMED
        assert response.data['confirmed_by'] == manager_user.id

    def test_confirm_already_confirmed_booking_fails(
        self, manager_client, confirmed_booking
    ):
        """Testa que não pode confirmar reserva já confirmada"""
        url = reverse('booking-confirm', kwargs={'pk': confirmed_booking.pk})
        response = manager_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cancel_booking(self, authenticated_client, booking):
        """Testa cancelar reserva"""
        url = reverse('booking-cancel', kwargs={'pk': booking.pk})
        data = {'reason': 'Reunião adiada'}
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == BookingStatus.CANCELLED
        assert response.data['cancellation_reason'] == 'Reunião adiada'

    def test_cancel_already_cancelled_booking_fails(
        self, authenticated_client, cancelled_booking
    ):
        """Testa que não pode cancelar reserva já cancelada"""
        url = reverse('booking-cancel', kwargs={'pk': cancelled_booking.pk})
        data = {'reason': 'Teste'}
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_pending_bookings(self, authenticated_client, user, room):
        """Testa listar reservas pendentes"""
        BookingFactory.create_batch(2, manager=user, room=room, status=BookingStatus.PENDING)
        ConfirmedBookingFactory(manager=user, room=room)

        url = reverse('booking-pending')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Deve retornar apenas as pendentes do usuário
        for item in response.data:
            assert item['status'] == BookingStatus.PENDING

    def test_filter_bookings_by_room(self, authenticated_client, user):
        """Testa filtrar reservas por sala"""
        room1 = RoomFactory()
        room2 = RoomFactory()
        BookingFactory.create_batch(2, manager=user, room=room1)
        BookingFactory(manager=user, room=room2)

        url = reverse('booking-list') + f'?room={room1.id}'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_filter_bookings_by_date(self, authenticated_client, user, room):
        """Testa filtrar reservas por data"""
        target_date = timezone.now().date() + timedelta(days=5)
        booking = BookingFactory(manager=user, room=room, date_booking=target_date)

        url = reverse('booking-list') + f'?date_booking={target_date.isoformat()}'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert response.data[0]['date_booking'] == target_date.isoformat()

    def test_ordering_bookings(self, authenticated_client, user, room):
        """Testa ordenação de reservas"""
        url = reverse('booking-list') + '?ordering=date_booking'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Verificar se está ordenado
        if len(response.data) > 1:
            dates = [item['date_booking'] for item in response.data]
            assert dates == sorted(dates)


@pytest.mark.django_db
@pytest.mark.integration
class TestBookingConflict:
    """Testes para conflitos de reservas"""

    def test_cannot_create_overlapping_bookings(
        self, authenticated_client, user, room
    ):
        """Testa que não pode criar reservas sobrepostas"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)

        # Primeira reserva
        BookingFactory(
            manager=user,
            room=room,
            date_booking=start.date(),
            start_datetime=start,
            end_datetime=end
        )

        # Tentar criar reserva sobreposta
        url = reverse('booking-list')
        overlap_start = start + timedelta(hours=1)
        overlap_end = overlap_start + timedelta(hours=2)

        data = {
            'manager': user.id,
            'room': room.id,
            'date_booking': start.date().isoformat(),
            'start_datetime': overlap_start.isoformat(),
            'end_datetime': overlap_end.isoformat(),
        }
        response = authenticated_client.post(url, data, format='json')
        # Deve falhar devido ao ExclusionConstraint
        assert response.status_code == status.HTTP_400_BAD_REQUEST
