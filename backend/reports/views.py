from collections import defaultdict
from datetime import timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit, quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connection
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.dateparse import parse_datetime
from django.views import View
from django.views.generic import TemplateView
from django.utils import timezone

from accounts.models import User
from accounts.permissions import RoleAccessMixin

from .models import ProdioSyncSettings, ProductionRecord, ReportingPeriod, RnDRecord


BI_DASHBOARDS = {
    "zarzad": {
        "key": "zarzad",
        "label": "Dane",
        "title": "Przeglad danych",
        "description": "Najwazniejsze KPI, realizacja produkcji, obciazenie maszyn oraz wyjatki wymagajace decyzji.",
        "source_label": "Zrodlo: Wewnetrzne",
        "embed_url": "/grafana/d/raport-zarzadczy-zarzad/raport-zarzadczy-zarzad?orgId=1&kiosk",
        "dashboard_url": "/grafana/d/raport-zarzadczy-zarzad/raport-zarzadczy-zarzad?orgId=1",
    },
    "produkcja": {
        "key": "produkcja",
        "label": "Produkcja",
        "title": "Przeglad produkcji",
        "description": "Realizacja planu, grupy produktowe, maszyny i zlecenia wymagajace interwencji na produkcji.",
        "source_label": "Zrodlo: Wewnetrzne",
        "embed_url": "/grafana/d/raport-zarzadczy-produkcja/raport-zarzadczy-produkcja?orgId=1&kiosk",
        "dashboard_url": "/grafana/d/raport-zarzadczy-produkcja/raport-zarzadczy-produkcja?orgId=1",
    },
    "prodio": {
        "key": "prodio",
        "label": "Prodio",
        "title": "Zlecenia z Prodio",
        "description": "Otwarte zlecenia produkcyjne pobrane z API Prodio i zapisane w bazie raportowej.",
        "source_label": "Zrodlo: Prodio",
        "embed_url": "/grafana/d/afik9bhsvh7nkb/zlecenia-z-prodio-otwarte?orgId=1&kiosk",
        "dashboard_url": "/grafana/d/afik9bhsvh7nkb/zlecenia-z-prodio-otwarte?orgId=1",
    },
    "prodio_ops": {
        "key": "prodio_ops",
        "label": "Operacje Prodio",
        "title": "Prodio - produkcja operacyjna",
        "description": "Operacje na stanowiskach, praca operatorow, postep wykonania i stany produktow z API Prodio.",
        "source_label": "Zrodlo: Prodio",
        "embed_url": "/grafana/d/prodio-produkcja-operacje/prodio-produkcja-operacyjna?orgId=1&kiosk",
        "dashboard_url": "/grafana/d/prodio-produkcja-operacje/prodio-produkcja-operacyjna?orgId=1",
    },
    "br": {
        "key": "br",
        "label": "B+R",
        "title": "Przeglad B+R",
        "description": "Statusy projektow, poziomy TRL, typy prac oraz blokery i tematy wymagajace decyzji.",
        "source_label": "Zrodlo: Wewnetrzne",
        "embed_url": "/grafana/d/raport-zarzadczy-br/raport-zarzadczy-br?orgId=1&kiosk",
        "dashboard_url": "/grafana/d/raport-zarzadczy-br/raport-zarzadczy-br?orgId=1",
    },
}


BI_ACCESS_BY_DEPARTMENT = {
    User.Department.MANAGEMENT: ("zarzad",),
    User.Department.PRODUCTION: ("produkcja", "prodio", "prodio_ops"),
    User.Department.RND: ("br",),
}


def allowed_bi_keys(user):
    if user.is_superuser or getattr(user, "is_program_admin", False):
        return ("zarzad", "produkcja", "prodio", "prodio_ops", "br")
    department = getattr(user, "effective_department", User.Department.MANAGEMENT)
    return BI_ACCESS_BY_DEPARTMENT.get(department, ())


def embed_url_for_user(url, user):
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    if user.is_superuser or user.role == User.Role.ADMIN:
        query["kiosk"] = ""
    else:
        query["kiosk"] = "tv"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def append_query_params(url, **params):
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    for key, value in params.items():
        query[key] = str(value)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def grafana_refresh_label(minutes):
    if minutes == 1:
        return "1m"
    if minutes == 10:
        return "10m"
    if minutes == 60:
        return "1h"
    return "10m"


def landing_url_for_user(user):
    if user.is_superuser or getattr(user, "is_program_admin", False):
        return None
    department = getattr(user, "effective_department", User.Department.MANAGEMENT)
    if department == User.Department.PRODUCTION:
        return "/production/"
    if department == User.Department.RND:
        return "/bi/?tab=br"
    return None


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


WORKERS_TODAY_MODES = {
    "start": {
        "label": "Wejscie dzis",
        "description": "Pracownicy, ktorzy rozpoczeli prace dzisiaj wedlug godziny wejscia.",
        "where_sql": "start_time::date = CURRENT_DATE",
        "empty_text": "Brak zarejestrowanych wejsc na dzis.",
    },
    "stop": {
        "label": "Wyjscie dzis",
        "description": "Pracownicy, ktorzy zakonczyli prace dzisiaj wedlug godziny wyjscia.",
        "where_sql": "stop_time::date = CURRENT_DATE",
        "empty_text": "Brak zarejestrowanych wyjsc na dzis.",
    },
    "activity": {
        "label": "Aktywnosc dzis",
        "description": "Pracownicy, dla ktorych dzisiejsza aktywnosc wynika z wejscia lub wyjscia w biezacym dniu.",
        "where_sql": "COALESCE(stop_time, start_time)::date = CURRENT_DATE",
        "empty_text": "Brak dzisiejszej aktywnosci pracownikow.",
    },
}


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

    def get(self, request, *args, **kwargs):
        landing_url = landing_url_for_user(request.user)
        if landing_url:
            return redirect(landing_url)
        return super().get(request, *args, **kwargs)

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
        ctx["grafana_embed_url"] = embed_url_for_user(selected["embed_url"], self.request.user)
        ctx["grafana_dashboard_url"] = selected["dashboard_url"]
        return ctx


class ProductionView(LoginRequiredMixin, RoleAccessMixin, ActivePeriodMixin, PaginationMixin, TemplateView):
    template_name = "reports/production_list.html"
    allowed_roles = (User.Role.ADMIN, User.Role.MANAGEMENT, User.Role.PROD_EDITOR)

    def post(self, request, *args, **kwargs):
        sync = ProdioSyncSettings.get_solo()
        action = request.POST.get("action")
        if action == "toggle_sync":
            sync.enabled = not sync.enabled
            sync.save(update_fields=["enabled", "updated_at"])
            messages.success(request, f"Sync Prodio {'wlaczony' if sync.enabled else 'wylaczony'}.")
        elif action == "set_interval":
            try:
                interval = int(request.POST.get("interval_minutes", "0"))
            except ValueError:
                interval = 0
            allowed = {choice[0] for choice in ProdioSyncSettings.INTERVAL_CHOICES}
            if interval in allowed:
                sync.interval_minutes = interval
                sync.save(update_fields=["interval_minutes", "updated_at"])
                messages.success(request, f"Interwal sync Prodio ustawiony na {interval} minut.")
            else:
                messages.error(request, "Niepoprawny interwal sync Prodio.")
        return redirect("production-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        sync = ProdioSyncSettings.get_solo()
        workers_mode = self.request.GET.get("workers_mode", "start").strip().lower()
        if workers_mode not in WORKERS_TODAY_MODES:
            workers_mode = "start"
        workers_mode_config = WORKERS_TODAY_MODES[workers_mode]
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    worker_full_name,
                    MIN(start_time) AS first_entry,
                    MAX(stop_time) AS last_exit,
                    BOOL_OR(stop_time IS NULL) AS active_now,
                    ROUND(COALESCE(SUM(work_minutes), 0) / 60.0, 2) AS worked_hours,
                    COUNT(DISTINCT operation_id) AS operations_count
                FROM reports_grafana_prodio_work_logs
                WHERE {workers_mode_config["where_sql"]}
                GROUP BY worker_full_name
                ORDER BY first_entry ASC, worker_full_name ASC;
                """
            )
            worker_rows = [
                {
                    "worker_full_name": row[0],
                    "first_entry": row[1],
                    "last_exit": row[2],
                    "active_now": row[3],
                    "worked_hours": row[4] or 0,
                    "operations_count": row[5],
                }
                for row in cursor.fetchall()
            ]

            cursor.execute(
                """
                SELECT
                    COALESCE(machine_name, 'Bez stanowiska') AS machine_name,
                    COUNT(DISTINCT operation_id) AS orders_count,
                    COUNT(DISTINCT auto_order_id) AS operation_steps,
                    ROUND(COALESCE(SUM(todo), 0), 2) AS planned_total,
                    ROUND(COALESCE(SUM(done), 0), 2) AS done_total,
                    ROUND(COALESCE(SUM(remaining), 0), 2) AS remaining_total
                FROM reports_grafana_prodio_operations
                WHERE deadline = CURRENT_DATE
                GROUP BY COALESCE(machine_name, 'Bez stanowiska')
                ORDER BY orders_count DESC, operation_steps DESC, machine_name ASC;
                """
            )
            machine_rows = [
                {
                    "machine_name": row[0],
                    "orders_count": row[1],
                    "operation_steps": row[2],
                    "planned_total": row[3] or 0,
                    "done_total": row[4] or 0,
                    "remaining_total": row[5] or 0,
                }
                for row in cursor.fetchall()
            ]

            cursor.execute(
                """
                SELECT
                    auto_order_id,
                    product_name,
                    machine_name,
                    status_label,
                    todo,
                    done,
                    remaining,
                    deadline
                FROM reports_grafana_prodio_operations
                WHERE deadline = CURRENT_DATE
                ORDER BY machine_name ASC, auto_order_id ASC
                LIMIT 120;
                """
            )
            today_orders = [
                {
                    "auto_order_id": row[0],
                    "product_name": row[1],
                    "machine_name": row[2],
                    "status_label": row[3],
                    "todo": row[4],
                    "done": row[5],
                    "remaining": row[6],
                    "deadline": row[7],
                }
                for row in cursor.fetchall()
            ]

            cursor.execute(
                """
                SELECT COUNT(DISTINCT COALESCE(machine_name, 'Bez stanowiska'))
                FROM reports_grafana_prodio_operations;
                """
            )
            total_machines = cursor.fetchone()[0] or 0

        ctx["workers_today"] = worker_rows
        ctx["workers_today_mode"] = workers_mode
        ctx["workers_today_mode_label"] = workers_mode_config["label"]
        ctx["workers_today_description"] = workers_mode_config["description"]
        ctx["workers_today_empty_text"] = workers_mode_config["empty_text"]
        ctx["workers_today_modes"] = [
            {"key": key, "label": value["label"], "is_current": key == workers_mode}
            for key, value in WORKERS_TODAY_MODES.items()
        ]
        ctx["machines_today"] = machine_rows
        ctx["today_orders"] = today_orders
        ctx["kpi_workers_today"] = len(worker_rows)
        ctx["kpi_active_now"] = sum(1 for row in worker_rows if row["active_now"])
        ctx["kpi_orders_today"] = sum(row["orders_count"] for row in machine_rows)
        ctx["kpi_machines_today"] = len(machine_rows)
        ctx["kpi_machines_total"] = total_machines
        ctx["production_chart_title"] = "Godziny pracy dzisiaj wg pracownika"
        ctx["production_chart_description"] = "Dolny panel Grafany pokazuje tylko dzisiejsze wpisy czasu pracy, bez historycznej tabeli."
        chart_url = embed_url_for_user(
            append_query_params(
                "/grafana/d-solo/prodio-produkcja-operacje/prodio-produkcja-operacyjna?orgId=1&panelId=7",
                refresh=grafana_refresh_label(sync.interval_minutes),
            ),
            self.request.user,
        )
        table_url = embed_url_for_user(
            append_query_params(
                "/grafana/d-solo/prodio-produkcja-operacje/prodio-produkcja-operacyjna?orgId=1&panelId=8",
                refresh=grafana_refresh_label(sync.interval_minutes),
            ),
            self.request.user,
        )
        ctx["production_chart_embed_url"] = chart_url
        ctx["production_table_embed_url"] = table_url
        ctx["production_chart_dashboard_url"] = (
            "/grafana/d/prodio-produkcja-operacje/prodio-produkcja-operacyjna?orgId=1&viewPanel=7"
        )
        ctx["production_table_dashboard_url"] = (
            "/grafana/d/prodio-produkcja-operacje/prodio-produkcja-operacyjna?orgId=1&viewPanel=8"
        )
        ctx["prodio_sync"] = sync
        ctx["prodio_sync_interval_ms"] = sync.interval_minutes * 60 * 1000
        return ctx


class ProdioSyncControlView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        sync = ProdioSyncSettings.get_solo()
        action = request.POST.get("action")
        if action == "toggle_sync":
            sync.enabled = not sync.enabled
            sync.save(update_fields=["enabled", "updated_at"])
            messages.success(request, f"Sync Prodio {'wlaczony' if sync.enabled else 'wylaczony'}.")
        elif action == "set_interval":
            try:
                interval = int(request.POST.get("interval_minutes", "0"))
            except ValueError:
                interval = 0
            allowed = {choice[0] for choice in ProdioSyncSettings.INTERVAL_CHOICES}
            if interval in allowed:
                sync.interval_minutes = interval
                sync.save(update_fields=["interval_minutes", "updated_at"])
                messages.success(request, f"Interwal sync Prodio ustawiony na {interval} minut.")
            else:
                messages.error(request, "Niepoprawny interwal sync Prodio.")
        target = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
        if not str(target).startswith("/"):
            target = "/"
        return redirect(target)


class LoginSyncWaitView(LoginRequiredMixin, TemplateView):
    template_name = "reports/login_sync_wait.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("login_sync_requested_at"):
            target = request.session.get("login_sync_redirect_to") or landing_url_for_user(request.user) or "/"
            return redirect(target)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["redirect_to"] = self.request.session.get("login_sync_redirect_to") or landing_url_for_user(self.request.user) or "/"
        return ctx


class LoginSyncStatusView(LoginRequiredMixin, View):
    LOGIN_SYNC_MAX_WAIT_SECONDS = 120

    def get(self, request, *args, **kwargs):
        requested_iso = request.session.get("login_sync_requested_at")
        redirect_to = request.session.get("login_sync_redirect_to") or landing_url_for_user(request.user) or "/"
        if not requested_iso:
            return JsonResponse({"ready": True, "redirect_to": redirect_to})

        requested_at = parse_datetime(requested_iso)
        sync = ProdioSyncSettings.get_solo()
        sync.recover_stale_running()
        ready = False
        status = sync.last_status or "never"
        timed_out = False
        can_continue = False
        if requested_at and sync.last_finished_at and sync.last_finished_at >= requested_at:
            ready = True
        elif requested_at:
            timeout_at = requested_at + timedelta(seconds=self.LOGIN_SYNC_MAX_WAIT_SECONDS)
            if timezone.now() >= timeout_at:
                timed_out = True
                can_continue = True
                ready = True

        if ready:
            request.session.pop("login_sync_requested_at", None)
            request.session.pop("login_sync_redirect_to", None)

        return JsonResponse(
            {
                "ready": ready,
                "redirect_to": redirect_to,
                "last_status": status,
                "last_finished_at": sync.last_finished_at.isoformat() if sync.last_finished_at else None,
                "is_running": sync.is_running(),
                "timed_out": timed_out,
                "can_continue": can_continue,
            }
        )


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

    def get(self, request, *args, **kwargs):
        allowed_keys = allowed_bi_keys(request.user)
        selected_key = request.GET.get("tab", "zarzad").strip().lower()
        if allowed_keys and selected_key not in allowed_keys:
            return redirect(f"{request.path}?tab={allowed_keys[0]}")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        allowed_keys = allowed_bi_keys(self.request.user)
        selected_key = self.request.GET.get("tab", "zarzad").strip().lower()
        if allowed_keys and selected_key not in allowed_keys:
            selected_key = allowed_keys[0]
        selected = BI_DASHBOARDS.get(selected_key, BI_DASHBOARDS["zarzad"]).copy()
        if selected["key"] == "zarzad":
            selected["embed_url"] = getattr(settings, "GRAFANA_EMBED_URL", selected["embed_url"])
            selected["dashboard_url"] = getattr(settings, "GRAFANA_DASHBOARD_URL", selected["dashboard_url"])
        ctx["selected_bi"] = selected
        ctx["grafana_embed_url"] = embed_url_for_user(selected["embed_url"], self.request.user)
        ctx["grafana_dashboard_url"] = selected["dashboard_url"]
        ctx["available_bi_dashboards"] = [BI_DASHBOARDS[key] for key in allowed_keys]
        return ctx


class FullGrafanaView(LoginRequiredMixin, RoleAccessMixin, TemplateView):
    template_name = "reports/grafana_full.html"
    allowed_roles = (User.Role.ADMIN,)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        query_string = self.request.META.get("QUERY_STRING", "")
        grafana_src = "/grafana/"
        if query_string:
            grafana_src = f"{grafana_src}?{quote(query_string, safe='=&')}"
        ctx["grafana_full_url"] = grafana_src
        return ctx
