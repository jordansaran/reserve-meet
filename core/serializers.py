from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from core.choices import UserRoles


User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['role'] = user.role # type: ignore
        token['email'] = user.email # type: ignore
        token['username'] = user.username

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }

        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer para registro de novos usuários"""

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8,
        help_text=_('Senha deve ter no mínimo 8 caracteres')
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text=_('Confirmação da senha')
    )

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'phone',
            'password',
            'password_confirm',
        ]
        read_only_fields = ['id']

    def validate_email(self, value):
        """Valida que o email é único"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                _('Já existe um usuário com este email.')
            )
        return value.lower()

    def validate_username(self, value):
        """Valida que o username é único"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                _('Já existe um usuário com este username.')
            )
        return value

    def validate(self, attrs):
        """Valida que as senhas coincidem"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': _('As senhas não coincidem.')
            })
        return attrs

    def create(self, validated_data):
        """Cria o usuário com senha criptografada e role 'user'"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        # Força role como 'user' para registro público
        validated_data['role'] = UserRoles.USER
        validated_data['is_staff'] = False
        validated_data['is_superuser'] = False

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer para listagem e detalhamento de usuários"""

    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'phone',
            'role',
            'role_display',
            'is_active',
            'date_joined',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'role',
            'is_active',
            'date_joined',
            'created_at',
            'updated_at',
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de perfil do usuário"""

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'phone',
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para mudança de senha"""

    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate_old_password(self, value):
        """Valida que a senha antiga está correta"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_('Senha atual incorreta.'))
        return value

    def validate(self, attrs):
        """Valida que as senhas novas coincidem"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': _('As senhas não coincidem.')
            })
        return attrs

    def save(self, **kwargs):
        """Atualiza a senha do usuário"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer para sessões de usuário"""

    is_active = serializers.BooleanField(read_only=True)
    device_type = serializers.SerializerMethodField()

    class Meta:
        from core.models import UserSession
        model = UserSession
        fields = [
            'id',
            'device_name',
            'ip_address',
            'location',
            'is_current',
            'is_active',
            'device_type',
            'created_at',
            'last_activity',
            'expires_at',
        ]
        read_only_fields = fields

    def get_device_type(self, obj):
        """Extrai tipo de dispositivo do user_agent"""
        from core.utils import parse_user_agent
        if obj.user_agent:
            device_info = parse_user_agent(obj.user_agent)
            return device_info.get('device_type', 'Unknown')
        return 'Unknown'
