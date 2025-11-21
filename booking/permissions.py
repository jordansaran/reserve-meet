from rest_framework.permissions import BasePermission


class IsManagerOrAdmin(BasePermission):
    """
    Permissão customizada que permite acesso apenas para usuários
    com role 'manager' ou 'admin', ou superusuários.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser or request.user.is_staff:
            return True

        return request.user.role in ['manager', 'admin']
