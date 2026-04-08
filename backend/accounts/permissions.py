from django.core.exceptions import PermissionDenied


class RoleAccessMixin:
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        if self.allowed_roles and getattr(user, "role", None) not in self.allowed_roles:
            raise PermissionDenied("Brak uprawnień do tego widoku.")
        return super().dispatch(request, *args, **kwargs)
