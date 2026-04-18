from rest_framework import permissions

from accounts.models import UserRole


class IsCollecteur(permissions.BasePermission):
    """Autorise les utilisateurs ayant le role COLLECTEUR (ou ADMIN)."""

    message = "Seuls les collecteurs peuvent effectuer cette action."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "role", None) in {UserRole.COLLECTEUR, UserRole.ADMIN}
        )


class IsAdminRole(permissions.BasePermission):
    """Autorise uniquement les utilisateurs ayant le role ADMIN."""

    message = "Action reservee aux administrateurs."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or getattr(user, "role", None) == UserRole.ADMIN)
        )
