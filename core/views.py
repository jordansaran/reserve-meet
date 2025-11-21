from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from core.serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    UserSessionSerializer,
)


User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            from core.utils import get_device_info, get_location_from_ip, send_login_notification_email
            from core.models import UserSession
            from datetime import datetime

            # Obter usuário
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.user

            # Capturar info do dispositivo
            device_info = get_device_info(request)
            location = get_location_from_ip(device_info['ip_address'])

            # Extrair JTI do refresh token
            refresh = RefreshToken(response.data['refresh'])
            jti = str(refresh.get('jti'))
            exp_timestamp = refresh.get('exp')
            expires_at = datetime.fromtimestamp(exp_timestamp)

            # Criar sessão
            UserSession.objects.create(
                user=user,
                refresh_token_jti=jti,
                ip_address=device_info['ip_address'],
                user_agent=device_info['user_agent'],
                device_name=device_info['device_name'],
                location=location,
                is_current=True,
                expires_at=expires_at
            )

            # Marcar outras sessões como não-current
            UserSession.objects.filter(user=user).exclude(refresh_token_jti=jti).update(is_current=False)

            # Enviar notificação por email (assíncrono para não bloquear)
            try:
                send_login_notification_email(user, device_info, device_info['ip_address'], location)
            except Exception:
                pass  # Não quebra o login se email falhar

        return response


class UserViewSet(ModelViewSet):
    """
    ViewSet para gerenciamento de usuários

    Endpoints disponíveis:
    - POST /api/users/register/ - Registro público de novos usuários (AllowAny)
    - GET /api/users/me/ - Perfil do usuário autenticado
    - PATCH /api/users/me/ - Atualizar perfil do usuário autenticado
    - POST /api/users/change-password/ - Mudar senha do usuário autenticado
    - GET /api/users/ - Listar usuários (apenas admin)
    - GET /api/users/{id}/ - Detalhes de usuário (apenas admin)
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Define permissões por action"""
        if self.action == 'register':
            return [AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        """Retorna o serializer apropriado para cada action"""
        if self.action == 'register':
            return UserRegistrationSerializer
        elif self.action in ['update', 'partial_update', 'me']:
            return UserUpdateSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        return UserSerializer

    def get_queryset(self):
        """Usuários comuns só veem a si mesmos, admins veem todos"""
        # Retorna queryset vazio durante geração do schema do Swagger
        if getattr(self, 'swagger_fake_view', False):
            return self.queryset.none()

        if self.request.user.is_superuser or self.request.user.is_staff:
            return self.queryset.exclude(id=self.request.user.id)
        return self.queryset.filter(id=self.request.user.id)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        Registra um novo usuário com role 'user'

        Endpoint público que permite qualquer pessoa criar uma conta.
        O usuário criado sempre terá role='user'.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                'message': 'Usuário criado com sucesso!',
                'user': UserSerializer(user).data
            },
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """
        GET: Retorna o perfil do usuário autenticado
        PATCH: Atualiza o perfil do usuário autenticado
        """
        user = request.user

        if request.method == 'GET':
            serializer = UserSerializer(user)
            return Response(serializer.data)

        # PATCH
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                'message': 'Perfil atualizado com sucesso!',
                'user': UserSerializer(user).data
            }
        )

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """
        Altera a senha do usuário autenticado

        Requer:
        - old_password: senha atual
        - new_password: nova senha
        - new_password_confirm: confirmação da nova senha
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {'message': 'Senha alterada com sucesso!'},
            status=status.HTTP_200_OK
        )


class LogoutView(APIView):
    """
    Faz logout do usuário adicionando o refresh token à blacklist

    POST /api/logout/
    Body: {"refresh": "seu_refresh_token"}

    Isso invalida o refresh token, impedindo que seja usado novamente.
    O access token continuará válido até expirar (máximo 15 minutos).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token é obrigatório.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {'message': 'Logout realizado com sucesso!'},
                status=status.HTTP_205_RESET_CONTENT
            )
        except TokenError as e:
            return Response(
                {'error': f'Token inválido ou já foi usado: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Erro ao realizar logout: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserSessionViewSet(ReadOnlyModelViewSet):
    """
    ViewSet para gerenciar sessões ativas do usuário

    Endpoints disponíveis:
    - GET /api/users/sessions/ - Listar todas as sessões
    - GET /api/users/sessions/active/ - Listar apenas sessões ativas
    - GET /api/users/sessions/{id}/ - Detalhes de uma sessão
    - DELETE /api/users/sessions/{id}/revoke/ - Revogar sessão específica
    """
    serializer_class = UserSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Usuário vê apenas suas próprias sessões"""
        from core.models import UserSession

        # Retorna queryset vazio durante geração do schema do Swagger
        if getattr(self, 'swagger_fake_view', False):
            return UserSession.objects.none()

        return UserSession.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    @action(detail=True, methods=['delete'])
    def revoke(self, request, pk=None):
        """Revoga uma sessão específica e adiciona token à blacklist"""
        session = self.get_object()

        if session.is_revoked:
            return Response(
                {'error': 'Esta sessão já foi revogada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Adicionar token à blacklist
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

            outstanding = OutstandingToken.objects.filter(
                jti=session.refresh_token_jti
            ).first()

            if outstanding:
                RefreshToken(str(outstanding.token)).blacklist()
        except Exception as e:
            # Log mas não falha
            print(f"Erro ao adicionar token à blacklist: {e}")

        # Marcar sessão como revogada
        session.revoke()

        return Response(
            {'message': 'Sessão revogada com sucesso!'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Lista apenas sessões ativas (não revogadas e não expiradas)"""
        from django.utils import timezone

        active_sessions = self.get_queryset().filter(
            is_revoked=False,
            expires_at__gt=timezone.now()
        )

        serializer = self.get_serializer(active_sessions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Retorna a sessão atual do usuário"""
        current_session = self.get_queryset().filter(is_current=True).first()

        if not current_session:
            return Response(
                {'error': 'Sessão atual não encontrada.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(current_session)
        return Response(serializer.data)


class LogoutAllView(APIView):
    """
    Faz logout de todas as sessões do usuário

    POST /api/logout-all/

    Invalida todos os refresh tokens do usuário autenticado.
    Isso força o usuário a fazer login novamente em todos os dispositivos.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from rest_framework_simplejwt.token_blacklist.models import (
                OutstandingToken
            )

            # Busca todos os tokens do usuário
            tokens = OutstandingToken.objects.filter(user=request.user)

            # Adiciona cada token à blacklist
            blacklisted_count = 0
            for token in tokens:
                try:
                    RefreshToken(str(token.token)).blacklist()
                    blacklisted_count += 1
                except TokenError:
                    # Token já estava na blacklist ou expirado
                    continue

            return Response(
                {
                    'message': 'Logout realizado em todos os dispositivos!',
                    'tokens_invalidados': blacklisted_count
                },
                status=status.HTTP_205_RESET_CONTENT
            )
        except Exception as e:
            return Response(
                {'error': f'Erro ao realizar logout: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
