from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import UserRole


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restreint l'acces a une vue selon un ou plusieurs roles.

    Usage :
        class MaVue(RoleRequiredMixin, View):
            allowed_roles = [UserRole.COLLECTEUR]
    """

    allowed_roles: list[str] = []
    allow_superuser = True

    def test_func(self):
        user = self.request.user
        if self.allow_superuser and (user.is_superuser or user.is_staff):
            return True
        return getattr(user, "role", None) in self.allowed_roles

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Votre role ne vous autorise pas a acceder a cette page.")


class CollecteurRequiredMixin(RoleRequiredMixin):
    allowed_roles = [UserRole.COLLECTEUR]


class AdminRoleRequiredMixin(RoleRequiredMixin):
    allowed_roles = [UserRole.ADMIN]


class CommercantRequiredMixin(RoleRequiredMixin):
    allowed_roles = [UserRole.COMMERCANT]
