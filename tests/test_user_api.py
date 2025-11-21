"""
Testes de integração para API de Usuários
"""
import pytest
from django.urls import reverse
from rest_framework import status

from core.models import User
from core.choices import UserRoles
from tests.factories import UserFactory


@pytest.mark.django_db
@pytest.mark.integration
class TestUserRegistrationAPI:
    """Testes para endpoint de registro de usuário"""

    def test_register_new_user(self, api_client):
        """Testa registro de novo usuário sem autenticação"""
        url = reverse('user-register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'phone': '11999999999',
            'password': 'securepass123',
            'password_confirm': 'securepass123'
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert response.data['user']['email'] == 'newuser@example.com'
        assert response.data['user']['role'] == UserRoles.USER
        assert 'password' not in response.data['user']

        # Verificar que usuário foi criado no banco
        user = User.objects.get(email='newuser@example.com')
        assert user.username == 'newuser'
        assert user.role == UserRoles.USER
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.check_password('securepass123')

    def test_register_user_password_mismatch(self, api_client):
        """Testa que registro falha quando senhas não coincidem"""
        url = reverse('user-register')
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'password123',
            'password_confirm': 'different123'
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data

    def test_register_user_duplicate_email(self, api_client):
        """Testa que não permite email duplicado"""
        UserFactory(email='existing@example.com')

        url = reverse('user-register')
        data = {
            'email': 'existing@example.com',
            'username': 'newuser',
            'password': 'password123',
            'password_confirm': 'password123'
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_register_user_duplicate_username(self, api_client):
        """Testa que não permite username duplicado"""
        UserFactory(username='existinguser')

        url = reverse('user-register')
        data = {
            'email': 'new@example.com',
            'username': 'existinguser',
            'password': 'password123',
            'password_confirm': 'password123'
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data

    def test_register_user_short_password(self, api_client):
        """Testa que senha deve ter no mínimo 8 caracteres"""
        url = reverse('user-register')
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'short',
            'password_confirm': 'short'
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_register_user_missing_required_fields(self, api_client):
        """Testa que campos obrigatórios são validados"""
        url = reverse('user-register')
        data = {
            'password': 'password123',
            'password_confirm': 'password123'
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data
        assert 'username' in response.data

    def test_register_forces_user_role(self, api_client):
        """Testa que role é sempre 'user' mesmo se tentar passar outro"""
        url = reverse('user-register')
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'password123',
            'password_confirm': 'password123',
            'role': 'admin',  # Tentando passar admin
            'is_staff': True,
            'is_superuser': True
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email='test@example.com')
        assert user.role == UserRoles.USER  # Forçado para user
        assert user.is_staff is False
        assert user.is_superuser is False


@pytest.mark.django_db
@pytest.mark.integration
class TestUserProfileAPI:
    """Testes para endpoints de perfil do usuário"""

    def test_get_my_profile(self, authenticated_client, user):
        """Testa obter perfil do usuário autenticado"""
        url = reverse('user-me')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == user.id
        assert response.data['email'] == user.email
        assert response.data['username'] == user.username

    def test_get_profile_requires_authentication(self, api_client):
        """Testa que obter perfil requer autenticação"""
        url = reverse('user-me')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_my_profile(self, authenticated_client, user):
        """Testa atualizar perfil do usuário autenticado"""
        url = reverse('user-me')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '11987654321'
        }
        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['user']['first_name'] == 'Updated'
        assert response.data['user']['last_name'] == 'Name'

        # Verificar no banco
        user.refresh_from_db()
        assert user.first_name == 'Updated'
        assert user.last_name == 'Name'

    def test_cannot_update_role_via_profile(self, authenticated_client, user):
        """Testa que não pode alterar role via atualização de perfil"""
        url = reverse('user-me')
        data = {
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True
        }
        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK

        # Role não deve ter mudado
        user.refresh_from_db()
        assert user.role == UserRoles.USER
        assert user.is_staff is False


@pytest.mark.django_db
@pytest.mark.integration
class TestChangePasswordAPI:
    """Testes para endpoint de mudança de senha"""

    def test_change_password(self, authenticated_client, user):
        """Testa mudança de senha com sucesso"""
        # Definir senha conhecida
        user.set_password('oldpassword123')
        user.save()

        url = reverse('user-change-password')
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }
        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data

        # Verificar que senha mudou
        user.refresh_from_db()
        assert user.check_password('newpassword123')
        assert not user.check_password('oldpassword123')

    def test_change_password_wrong_old_password(self, authenticated_client, user):
        """Testa que falha se senha antiga estiver incorreta"""
        user.set_password('correctpassword')
        user.save()

        url = reverse('user-change-password')
        data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }
        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'old_password' in response.data

    def test_change_password_mismatch(self, authenticated_client, user):
        """Testa que falha se senhas novas não coincidem"""
        user.set_password('oldpassword123')
        user.save()

        url = reverse('user-change-password')
        data = {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'different123'
        }
        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'new_password_confirm' in response.data

    def test_change_password_requires_authentication(self, api_client):
        """Testa que mudança de senha requer autenticação"""
        url = reverse('user-change-password')
        data = {
            'old_password': 'old',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
@pytest.mark.integration
class TestUserListAPI:
    """Testes para listagem de usuários"""

    def test_list_users_as_admin(self, admin_client):
        """Testa que admin pode listar todos os usuários"""
        UserFactory.create_batch(3)

        url = reverse('user-list')
        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 4  # 3 criados + 1 admin

    def test_list_users_as_regular_user(self, authenticated_client, user):
        """Testa que usuário comum só vê a si mesmo"""
        UserFactory.create_batch(3)

        url = reverse('user-list')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['id'] == user.id

    def test_list_users_requires_authentication(self, api_client):
        """Testa que listar usuários requer autenticação"""
        url = reverse('user-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_user_detail_as_admin(self, admin_client):
        """Testa que admin pode ver detalhes de qualquer usuário"""
        user = UserFactory()
        url = reverse('user-detail', kwargs={'pk': user.pk})
        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == user.id

    def test_get_user_detail_as_regular_user_own(self, authenticated_client, user):
        """Testa que usuário pode ver seus próprios detalhes"""
        url = reverse('user-detail', kwargs={'pk': user.pk})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == user.id

    def test_get_user_detail_as_regular_user_other(self, authenticated_client):
        """Testa que usuário não pode ver detalhes de outros"""
        other_user = UserFactory()
        url = reverse('user-detail', kwargs={'pk': other_user.pk})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
@pytest.mark.integration
class TestUserFlowIntegration:
    """Testes de fluxo completo de usuário"""

    def test_complete_user_flow(self, api_client):
        """Testa fluxo completo: registro -> login -> atualizar perfil -> mudar senha"""

        # 1. Registro
        register_url = reverse('user-register')
        register_data = {
            'email': 'flowtest@example.com',
            'username': 'flowtest',
            'first_name': 'Flow',
            'last_name': 'Test',
            'password': 'initialpass123',
            'password_confirm': 'initialpass123'
        }
        response = api_client.post(register_url, register_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        user_id = response.data['user']['id']

        # 2. Login
        token_url = reverse('token_obtain_pair')
        token_data = {
            'email': 'flowtest@example.com',
            'password': 'initialpass123'
        }
        response = api_client.post(token_url, token_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        access_token = response.data['access']

        # Criar cliente autenticado
        from rest_framework.test import APIClient
        authenticated_client = APIClient()
        authenticated_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # 3. Obter perfil
        me_url = reverse('user-me')
        response = authenticated_client.get(me_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'flowtest@example.com'

        # 4. Atualizar perfil
        update_data = {'first_name': 'Updated', 'phone': '11999999999'}
        response = authenticated_client.patch(me_url, update_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user']['first_name'] == 'Updated'

        # 5. Mudar senha
        change_password_url = reverse('user-change-password')
        password_data = {
            'old_password': 'initialpass123',
            'new_password': 'newpass123456',
            'new_password_confirm': 'newpass123456'
        }
        response = authenticated_client.post(
            change_password_url, password_data, format='json'
        )
        assert response.status_code == status.HTTP_200_OK

        # 6. Testar login com nova senha
        token_data['password'] = 'newpass123456'
        response = api_client.post(token_url, token_data, format='json')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
@pytest.mark.integration
class TestLogoutAPI:
    """Testes para endpoints de logout"""

    def test_logout_successfully(self, api_client, user):
        """Testa logout com sucesso"""
        # 1. Fazer login para obter tokens
        user.set_password('testpass123')
        user.save()

        token_url = reverse('token_obtain_pair')
        response = api_client.post(
            token_url,
            {'email': user.email, 'password': 'testpass123'},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        refresh_token = response.data['refresh']
        access_token = response.data['access']

        # 2. Fazer logout
        from rest_framework.test import APIClient
        authenticated_client = APIClient()
        authenticated_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        logout_url = reverse('logout')
        response = authenticated_client.post(
            logout_url,
            {'refresh': refresh_token},
            format='json'
        )
        assert response.status_code == status.HTTP_205_RESET_CONTENT
        assert 'message' in response.data

        # 3. Tentar usar o refresh token (deve falhar)
        refresh_url = reverse('token_refresh')
        response = api_client.post(
            refresh_url,
            {'refresh': refresh_token},
            format='json'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_without_refresh_token(self, authenticated_client):
        """Testa logout sem fornecer refresh token"""
        logout_url = reverse('logout')
        response = authenticated_client.post(logout_url, {}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_logout_with_invalid_token(self, authenticated_client):
        """Testa logout com token inválido"""
        logout_url = reverse('logout')
        response = authenticated_client.post(
            logout_url,
            {'refresh': 'token_invalido'},
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_logout_requires_authentication(self, api_client):
        """Testa que logout requer autenticação"""
        logout_url = reverse('logout')
        response = api_client.post(
            logout_url,
            {'refresh': 'some_token'},
            format='json'
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_already_blacklisted_token(self, api_client, user):
        """Testa logout com token já na blacklist"""
        # 1. Login
        user.set_password('testpass123')
        user.save()

        token_url = reverse('token_obtain_pair')
        response = api_client.post(
            token_url,
            {'email': user.email, 'password': 'testpass123'},
            format='json'
        )
        refresh_token = response.data['refresh']
        access_token = response.data['access']

        # 2. Primeiro logout
        from rest_framework.test import APIClient
        authenticated_client = APIClient()
        authenticated_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        logout_url = reverse('logout')
        response = authenticated_client.post(
            logout_url,
            {'refresh': refresh_token},
            format='json'
        )
        assert response.status_code == status.HTTP_205_RESET_CONTENT

        # 3. Tentar fazer logout novamente com o mesmo token
        response = authenticated_client.post(
            logout_url,
            {'refresh': refresh_token},
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.integration
class TestLogoutAllAPI:
    """Testes para logout em todos os dispositivos"""

    def test_logout_all_successfully(self, api_client, user):
        """Testa logout de todos os dispositivos"""
        user.set_password('testpass123')
        user.save()

        # 1. Fazer login em múltiplos "dispositivos" (obter múltiplos tokens)
        token_url = reverse('token_obtain_pair')
        credentials = {'email': user.email, 'password': 'testpass123'}

        # Dispositivo 1
        response1 = api_client.post(token_url, credentials, format='json')
        token1 = response1.data['access']
        refresh1 = response1.data['refresh']

        # Dispositivo 2
        response2 = api_client.post(token_url, credentials, format='json')
        token2 = response2.data['access']
        refresh2 = response2.data['refresh']

        # 2. Fazer logout de todos os dispositivos
        from rest_framework.test import APIClient
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token1}')

        logout_all_url = reverse('logout_all')
        response = client.post(logout_all_url)

        assert response.status_code == status.HTTP_205_RESET_CONTENT
        assert 'message' in response.data
        assert 'tokens_invalidados' in response.data

        # 3. Tentar usar ambos os refresh tokens (ambos devem falhar)
        refresh_url = reverse('token_refresh')

        response = api_client.post(
            refresh_url,
            {'refresh': refresh1},
            format='json'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = api_client.post(
            refresh_url,
            {'refresh': refresh2},
            format='json'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_all_requires_authentication(self, api_client):
        """Testa que logout-all requer autenticação"""
        logout_all_url = reverse('logout_all')
        response = api_client.post(logout_all_url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_all_with_no_tokens(self, authenticated_client):
        """Testa logout-all quando usuário não tem tokens ativos"""
        logout_all_url = reverse('logout_all')
        response = authenticated_client.post(logout_all_url)

        # Deve retornar sucesso mesmo sem tokens
        assert response.status_code == status.HTTP_205_RESET_CONTENT
