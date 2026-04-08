from django.db.models import Count
from rest_framework.generics import ListAPIView
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User

from .models import ProductionRecord, ReportingPeriod, RnDRecord
from .serializers import ProductionRecordSerializer, ReportingPeriodSerializer, RnDRecordSerializer


def get_active_period():
    return ReportingPeriod.objects.filter(is_active=True).first() or ReportingPeriod.objects.order_by("-year", "-week").first()


class RolePermission(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return getattr(user, "role", None) in self.allowed_roles


class DashboardRolePermission(RolePermission):
    allowed_roles = (User.Role.ADMIN, User.Role.MANAGEMENT, User.Role.PROD_EDITOR, User.Role.RND_EDITOR)


class ProductionRolePermission(RolePermission):
    allowed_roles = (User.Role.ADMIN, User.Role.MANAGEMENT, User.Role.PROD_EDITOR)


class RnDRolePermission(RolePermission):
    allowed_roles = (User.Role.ADMIN, User.Role.MANAGEMENT, User.Role.RND_EDITOR)


class DashboardSummaryApiView(APIView):
    permission_classes = [IsAuthenticated, DashboardRolePermission]

    def get(self, request):
        period = get_active_period()
        prod = ProductionRecord.objects.filter(period=period) if period else ProductionRecord.objects.none()
        rnd = RnDRecord.objects.filter(period=period) if period else RnDRecord.objects.none()
        return Response(
            {
                "period": ReportingPeriodSerializer(period).data if period else None,
                "production_count": prod.count(),
                "rnd_count": rnd.count(),
                "production_statuses": list(prod.values("status").annotate(total=Count("id")).order_by("status")),
                "rnd_statuses": list(rnd.values("status").annotate(total=Count("id")).order_by("status")),
            }
        )


class ProductionRecordListApiView(ListAPIView):
    permission_classes = [IsAuthenticated, ProductionRolePermission]
    serializer_class = ProductionRecordSerializer

    def get_queryset(self):
        period = get_active_period()
        queryset = ProductionRecord.objects.filter(period=period) if period else ProductionRecord.objects.none()
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by("order_number")


class RnDRecordListApiView(ListAPIView):
    permission_classes = [IsAuthenticated, RnDRolePermission]
    serializer_class = RnDRecordSerializer

    def get_queryset(self):
        period = get_active_period()
        queryset = RnDRecord.objects.filter(period=period) if period else RnDRecord.objects.none()
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by("code")
