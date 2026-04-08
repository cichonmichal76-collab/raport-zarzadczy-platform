from collections import defaultdict

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count
from django.views.generic import TemplateView

from accounts.models import User
from accounts.permissions import RoleAccessMixin

from .models import ProductionRecord, ReportingPeriod, RnDRecord


BI_DASHBOARDS = {
    "zarzad": {
        "key": "zarzad",
        "label": "Zarzad",
        "title": "Przeglad zarzadu",
        "description": "Najwazniejsze KPI, realizacja produkcji, obciazenie maszyn oraz wyjatki wymagajace decyzji.",
        "embed_url": "/grafana/d/raport-zarzadczy-zarzad/raport-zarzadczy-zarzad?orgId=1&kiosk",
        "dashboard_url": "/grafana/d/raport-zarzadczy-zarzad/raport-zarzadczy-zarzad?orgId=1",
    },
    "produkcja": {
        "key": "produkcja",
        "label": "Produkcja",
        "title": "Przeglad produkcji",
        "description": "Realizacja planu, grupy produktowe, maszyny i zlecenia wymagajace interwencji na produkcji.",
        "embed_url": "/grafana/d/raport-zarzadczy-produkcja/raport-zarzadczy-produkcja?orgId=1&kiosk",
        "dashboard_url": "/grafana/d/raport-zarzadczy-produkcja/raport-zarzadczy-produkcja?orgId=1",
    },
    "br": {
        "key": "br",
        "label": "B+R",
        "title": "Przeglad B+R",
        "description": "Statusy projektow, poziomy TRL, typy prac oraz blokery i tematy wymagajace decyzji.",
        "embed_url": "/grafana/d/raport-zarzadczy-br/raport-zarzadczy-br?orgId=1&kiosk",
        "dashboard_url": "/grafana/d/raport-zarzadczy-br/raport-zarzadczy-br?orgId=1",
    },
}


def _parse_hours(value):
    if not value:
        return 0.0
    text = str(value).strip()
    if ":" in text:
        try:
            hours, minutes = text.split(":", 1)
            return int(hours) + int(minutes) / 60
        except ValueError:
            return 0.0
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return 0.0


def _round_hours(value):
    return round(value, 2)


def _exception_bucket(record):
    haystack = " ".join(
        [
            str(record.current_state or ""),
            str(record.problem or ""),
            str(record.solution or ""),
        ]
    ).lower()
    workers = str(record.workers or "").strip()

    if not workers or workers == "–":
        return "Brak operatora"
    if any(token in haystack for token in ["rewiz", "norm", "norma", "normatyw"]):
        return "Rewizja normy"
    if any(token in haystack for token in ["plan", "harmonogram", "kolejk", "zaplan"]):
        return "Bledne planowanie"
    if any(token in haystack for token in ["technolog", "ustaw", "przezbroj", "proces"]):
        return "Problemy technologiczne"
    if record.problem:
        return "Komentarze i odchylenia"
    return None


class ActivePeriodMixin:
    def get_active_period(self):
        return ReportingPeriod.objects.filter(is_active=True).first() or ReportingPeriod.objects.order_by("-year", "-week").first()


class PaginationMixin:
    paginate_by = 10

    def paginate_queryset(self, request, queryset, page_param="page", per_page=None):
        paginator = Paginator(queryset, per_page or self.paginate_by)
        page_obj = paginator.get_page(request.GET.get(page_param))
        return page_obj


class DashboardView(LoginRequiredMixin, RoleAccessMixin, ActivePeriodMixin, TemplateView):
    template_name = "reports/dashboard.html"
    allowed_roles = (User.Role.ADMIN, User.Role.MANAGEMENT, User.Role.PROD_EDITOR, User.Role.RND_EDITOR)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        period = self.get_active_period()
        prod = list(ProductionRecord.objects.filter(period=period).order_by("order_number")) if period else []
        rnd = RnDRecord.objects.filter(period=period) if period else RnDRecord.objects.none()

        total_orders = len(prod)
        completed_orders = sum(1 for item in prod if item.status == "Gotowe")
        completed_units = sum(item.completed_units for item in prod)
        planned_units = sum(item.planned_units for item in prod)
        actual_hours = sum(_parse_hours(item.work_time) for item in prod)
        norm_hours = sum(_parse_hours(item.norm_time) for item in prod)
        time_delta = actual_hours - norm_hours

        status_counts = defaultdict(int)
        group_completed = defaultdict(int)
        group_planned = defaultdict(int)
        machine_actual = defaultdict(float)
        machine_norm = defaultdict(float)
        exceptions = defaultdict(list)

        for item in prod:
            status_counts[item.status or "Nieznany"] += 1
            group_key = item.product_group or "Bez grupy"
            group_completed[group_key] += item.completed_units
            group_planned[group_key] += item.planned_units

            machine_key = item.machine or "Nieprzypisana"
            machine_actual[machine_key] += _parse_hours(item.work_time)
            machine_norm[machine_key] += _parse_hours(item.norm_time)

            bucket = _exception_bucket(item)
            if bucket:
                detail = item.problem or item.current_state or item.solution or "Wymaga sprawdzenia."
                exceptions[bucket].append(
                    {
                        "order_number": item.order_number,
                        "product": item.product,
                        "detail": detail,
                    }
                )

        production_statuses = [{"status": key, "total": value} for key, value in sorted(status_counts.items())]
        product_group_rows = [
            {
                "group": key,
                "completed": group_completed[key],
                "planned": group_planned[key],
            }
            for key in sorted(group_completed.keys() | group_planned.keys())
        ]
        machine_rows = [
            {
                "machine": key,
                "actual": _round_hours(machine_actual[key]),
                "norm": _round_hours(machine_norm[key]),
            }
            for key in sorted(machine_actual.keys() | machine_norm.keys())
        ]

        exception_groups = []
        for title in [
            "Komentarze i odchylenia",
            "Rewizja normy",
            "Brak operatora",
            "Bledne planowanie",
            "Problemy technologiczne",
        ]:
            items = exceptions.get(title, [])
            exception_groups.append({"title": title, "count": len(items), "items": items[:5]})

        ctx.update(
            {
                "period": period,
                "production_count": total_orders,
                "rnd_count": rnd.count(),
                "production_statuses": production_statuses,
                "rnd_statuses": list(rnd.values("status").annotate(total=Count("id")).order_by("status")),
                "rnd_items": rnd[:8],
                "production_items": prod[:8],
                "kpi_total_orders": total_orders,
                "kpi_ready_pct": round((completed_orders / total_orders) * 100, 1) if total_orders else 0,
                "kpi_completed_units": completed_units,
                "kpi_actual_hours": _round_hours(actual_hours),
                "kpi_norm_hours": _round_hours(norm_hours),
                "kpi_time_delta": _round_hours(time_delta),
                "kpi_execution_pct": round((completed_units / planned_units) * 100, 1) if planned_units else 0,
                "product_group_rows": product_group_rows,
                "machine_rows": machine_rows,
                "exception_groups": exception_groups,
            }
        )
        selected = BI_DASHBOARDS["zarzad"].copy()
        selected["embed_url"] = getattr(settings, "GRAFANA_EMBED_URL", selected["embed_url"])
        selected["dashboard_url"] = getattr(settings, "GRAFANA_DASHBOARD_URL", selected["dashboard_url"])
        ctx["selected_bi"] = selected
        ctx["grafana_embed_url"] = selected["embed_url"]
        ctx["grafana_dashboard_url"] = selected["dashboard_url"]
        return ctx


class ProductionView(LoginRequiredMixin, RoleAccessMixin, ActivePeriodMixin, PaginationMixin, TemplateView):
    template_name = "reports/production_list.html"
    allowed_roles = (User.Role.ADMIN, User.Role.MANAGEMENT, User.Role.PROD_EDITOR)
    paginate_by = 12

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        period = self.get_active_period()
        records = ProductionRecord.objects.filter(period=period).order_by("order_number") if period else ProductionRecord.objects.none()
        page_obj = self.paginate_queryset(self.request, records, page_param="page")
        ctx["period"] = period
        ctx["records"] = page_obj.object_list
        ctx["page_obj"] = page_obj
        return ctx


class RnDView(LoginRequiredMixin, RoleAccessMixin, ActivePeriodMixin, PaginationMixin, TemplateView):
    template_name = "reports/rnd_list.html"
    allowed_roles = (User.Role.ADMIN, User.Role.MANAGEMENT, User.Role.RND_EDITOR)
    paginate_by = 12

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        period = self.get_active_period()
        records = RnDRecord.objects.filter(period=period).order_by("code") if period else RnDRecord.objects.none()
        page_obj = self.paginate_queryset(self.request, records, page_param="page")
        ctx["period"] = period
        ctx["records"] = page_obj.object_list
        ctx["page_obj"] = page_obj
        return ctx


class BiReportsView(LoginRequiredMixin, RoleAccessMixin, TemplateView):
    template_name = "reports/bi_reports.html"
    allowed_roles = (User.Role.ADMIN, User.Role.MANAGEMENT, User.Role.PROD_EDITOR, User.Role.RND_EDITOR)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        selected_key = self.request.GET.get("tab", "zarzad").strip().lower()
        selected = BI_DASHBOARDS.get(selected_key, BI_DASHBOARDS["zarzad"]).copy()
        if selected["key"] == "zarzad":
            selected["embed_url"] = getattr(settings, "GRAFANA_EMBED_URL", selected["embed_url"])
            selected["dashboard_url"] = getattr(settings, "GRAFANA_DASHBOARD_URL", selected["dashboard_url"])
        ctx["selected_bi"] = selected
        ctx["grafana_embed_url"] = selected["embed_url"]
        ctx["grafana_dashboard_url"] = selected["dashboard_url"]
        return ctx
