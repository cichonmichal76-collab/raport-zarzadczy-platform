import json
import shlex

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from reports.models import ProdioSyncSettings


class Command(BaseCommand):
    help = "Zwraca i aktualizuje stan harmonogramu sync Prodio."

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["state", "start", "finish"])
        parser.add_argument("--format", choices=["shell", "json"], default="shell")
        parser.add_argument("--status", choices=["success", "error"], default=None)
        parser.add_argument("--message", default="")

    def handle(self, *args, **options):
        action = options["action"]
        sync = ProdioSyncSettings.get_solo()

        if action == "state":
            return self._print_state(sync, options["format"])

        if action == "start":
            sync.last_started_at = timezone.now()
            sync.last_status = "running"
            sync.last_message = ""
            sync.save(update_fields=["last_started_at", "last_status", "last_message", "updated_at"])
            self.stdout.write("started")
            return

        if action == "finish":
            status = options["status"]
            if not status:
                raise CommandError("--status jest wymagane dla akcji finish")
            sync.last_finished_at = timezone.now()
            sync.last_status = status
            sync.last_message = options["message"]
            sync.save(update_fields=["last_finished_at", "last_status", "last_message", "updated_at"])
            self.stdout.write(status)
            return

    def _print_state(self, sync, fmt):
        now = timezone.now()
        sync.recover_stale_running(now=now)
        payload = {
            "enabled": sync.enabled,
            "interval_minutes": sync.interval_minutes,
            "is_running": sync.is_running(),
            "is_due": sync.is_due(now=now),
            "has_forced_run_pending": sync.has_forced_run_pending(),
            "last_status": sync.last_status,
        }
        if fmt == "json":
            self.stdout.write(json.dumps(payload))
            return
        lines = [
            f"PRODIO_SYNC_ENABLED={1 if payload['enabled'] else 0}",
            f"PRODIO_SYNC_INTERVAL_MINUTES={payload['interval_minutes']}",
            f"PRODIO_SYNC_IS_RUNNING={1 if payload['is_running'] else 0}",
            f"PRODIO_SYNC_DUE={1 if payload['is_due'] else 0}",
            f"PRODIO_SYNC_HAS_FORCED_RUN_PENDING={1 if payload['has_forced_run_pending'] else 0}",
            f"PRODIO_SYNC_LAST_STATUS={shlex.quote(payload['last_status'] or '')}",
        ]
        self.stdout.write("\n".join(lines))
