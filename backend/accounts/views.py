from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.utils import timezone

from reports.models import ProdioSyncSettings


class AppLoginView(LoginView):
    template_name = "registration/login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        sync = ProdioSyncSettings.get_solo()
        requested_at = timezone.now()
        sync.force_run_requested_at = requested_at
        sync.save(update_fields=["force_run_requested_at", "updated_at"])

        self.request.session["login_sync_requested_at"] = requested_at.isoformat()
        self.request.session["login_sync_redirect_to"] = self.get_success_url()
        return redirect("login-sync-wait")
