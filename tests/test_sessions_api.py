"""
Testes de integração para API de Sessões de Usuário
"""
import pytest
from django.urls import reverse
from rest_framework import status
from core.models import UserSession


@pytest.mark.django_db
@pytest.mark.integration
class TestLoginCreatesSession:
    """Testes para verificar que login cria sessão"""

    def test_login_creates_session(self, api_client, user):
        """Testa que login cria uma sessão automaticamente"""
        user.set_password('testpass123')
        user.save()

        # Login
        token_url = reverse('token_obtain_pair')
        response = api_client.post(
            token_url,
            {'email': user.email, 'password': 'testpass123'},
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK

        # Verificar que sessão foi criada
        sessions = UserSession.objects.filter(user=user)
        assert sessions.count() == 1

        session = sessions.first()
        assert session.user == user
        assert session.is_current is True
        assert session.is_revoked is False
        assert session.ip_address is not None
        assert session.device_name is not None

    def test_multiple_logins_create_multiple_sessions(self, api_client, user):
        """Testa que múltiplos logins criam múltiplas sessões"""
        user.set_password('testpass123')
        user.save()

        token_url = reverse('token_obtain_pair')
        credentials = {'email': user.email, 'password': 'testpass123'}

        # Primeiro login
        response1 = api_client.post(token_url, credentials, format='json')
        assert response1.status_code == status.HTTP_200_OK

        # Segundo login
        response2 = api_client.post(token_url, credentials, format='json')
        assert response2.status_code == status.HTTP_200_OK

        # Verificar que existem 2 sessões
        sessions = UserSession.objects.filter(user=user)
        assert sessions.count() == 2

        # Verificar que apenas a última é current
        current_sessions = sessions.filter(is_current=True)
        assert current_sessions.count() == 1


@pytest.mark.django_db
@pytest.mark.integration
class TestUserSessionsList:
    """Testes para listar sessões do usuário"""

    def test_list_user_sessions(self, authenticated_client, user):
        """Testa listar sessões do usuário autenticado"""
        # Fazer um login para criar sessão
        user.set_password('testpass123')
        user.save()

        # Criar algumas sessões manualmente para teste
        UserSession.objects.create(
            user=user,
            refresh_token_jti='test-jti-1',
            device_name='Chrome no Windows',
            ip_address='127.0.0.1',
            expires_at='2025-12-31 23:59:59'
        )
        UserSession.objects.create(
            user=user,
            refresh_token_jti='test-jti-2',
            device_name='Firefox no Linux',
            ip_address='192.168.1.1',
            expires_at='2025-12-31 23:59:59'
        )

        url = reverse('user-session-list')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2

    def test_list_sessions_requires_authentication(self, api_client):
        """Testa que listar sessões requer autenticação"""
        url = reverse('user-session-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_only_sees_own_sessions(self, authenticated_client, user):
        """Testa que usuário só vê suas próprias sessões"""
        from tests.factories import UserFactory

        # Criar sessão para outro usuário
        other_user = UserFactory()
        UserSession.objects.create(
            user=other_user,
            refresh_token_jti='other-jti',
            device_name='Other Device',
            ip_address='10.0.0.1',
            expires_at='2025-12-31 23:59:59'
        )

        # Criar sessão para o usuário autenticado
        UserSession.objects.create(
            user=user,
            refresh_token_jti='my-jti',
            device_name='My Device',
            ip_address='127.0.0.1',
            expires_at='2025-12-31 23:59:59'
        )

        url = reverse('user-session-list')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Deve retornar apenas a sessão do usuário autenticado
        assert all(item['device_name'] != 'Other Device' for item in response.data)


@pytest.mark.django_db
@pytest.mark.integration
class TestActiveSessionsFilter:
    """Testes para filtro de sessões ativas"""

    def test_list_only_active_sessions(self, authenticated_client, user):
        """Testa listar apenas sessões ativas"""
        from django.utils import timezone
        from datetime import timedelta

        # Sessão ativa (não expirada, não revogada)
        UserSession.objects.create(
            user=user,
            refresh_token_jti='active-jti',
            device_name='Active Device',
            ip_address='127.0.0.1',
            expires_at=timezone.now() + timedelta(days=1),
            is_revoked=False
        )

        # Sessão expirada
        UserSession.objects.create(
            user=user,
            refresh_token_jti='expired-jti',
            device_name='Expired Device',
            ip_address='127.0.0.2',
            expires_at=timezone.now() - timedelta(days=1),
            is_revoked=False
        )

        # Sessão revogada
        UserSession.objects.create(
            user=user,
            refresh_token_jti='revoked-jti',
            device_name='Revoked Device',
            ip_address='127.0.0.3',
            expires_at=timezone.now() + timedelta(days=1),
            is_revoked=True
        )

        url = reverse('user-session-active')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Deve retornar apenas a sessão ativa
        assert len([s for s in response.data if not s['is_active']]) == 0


@pytest.mark.django_db
@pytest.mark.integration
class TestRevokeSession:
    """Testes para revogar sessão específica"""

    def test_revoke_specific_session(self, authenticated_client, user):
        """Testa revogar uma sessão específica"""
        from django.utils import timezone
        from datetime import timedelta

        session = UserSession.objects.create(
            user=user,
            refresh_token_jti='test-jti',
            device_name='Test Device',
            ip_address='127.0.0.1',
            expires_at=timezone.now() + timedelta(days=1),
            is_revoked=False
        )

        url = reverse('user-session-revoke', kwargs={'pk': session.pk})
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data

        # Verificar que sessão foi revogada
        session.refresh_from_db()
        assert session.is_revoked is True

    def test_cannot_revoke_already_revoked_session(self, authenticated_client, user):
        """Testa que não pode revogar sessão já revogada"""
        from django.utils import timezone
        from datetime import timedelta

        session = UserSession.objects.create(
            user=user,
            refresh_token_jti='test-jti',
            device_name='Test Device',
            ip_address='127.0.0.1',
            expires_at=timezone.now() + timedelta(days=1),
            is_revoked=True  # Já revogada
        )

        url = reverse('user-session-revoke', kwargs={'pk': session.pk})
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_revoke_session_requires_authentication(self, api_client, user):
        """Testa que revogar sessão requer autenticação"""
        from django.utils import timezone
        from datetime import timedelta

        session = UserSession.objects.create(
            user=user,
            refresh_token_jti='test-jti',
            device_name='Test Device',
            ip_address='127.0.0.1',
            expires_at=timezone.now() + timedelta(days=1)
        )

        url = reverse('user-session-revoke', kwargs={'pk': session.pk})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
@pytest.mark.integration
class TestCurrentSession:
    """Testes para sessão atual"""

    def test_get_current_session(self, authenticated_client, user):
        """Testa obter sessão atual do usuário"""
        from django.utils import timezone
        from datetime import timedelta

        # Criar sessão atual
        UserSession.objects.create(
            user=user,
            refresh_token_jti='current-jti',
            device_name='Current Device',
            ip_address='127.0.0.1',
            expires_at=timezone.now() + timedelta(days=1),
            is_current=True
        )

        # Criar sessão não-current
        UserSession.objects.create(
            user=user,
            refresh_token_jti='old-jti',
            device_name='Old Device',
            ip_address='127.0.0.2',
            expires_at=timezone.now() + timedelta(days=1),
            is_current=False
        )

        url = reverse('user-session-current')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_current'] is True
        assert response.data['device_name'] == 'Current Device'
