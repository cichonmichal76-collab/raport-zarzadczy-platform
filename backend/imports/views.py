from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.models import User
from accounts.permissions import RoleAccessMixin
from .forms import UploadBatchForm
from .models import UploadBatch
from .tasks import process_upload_batch


def paginate(request, queryset, page_param="page", per_page=10):
    return Paginator(queryset, per_page).get_page(request.GET.get(page_param))


class UploadBatchCreateView(LoginRequiredMixin, RoleAccessMixin, View):
    template_name = "imports/upload_form.html"
    allowed_roles = (User.Role.ADMIN, User.Role.PROD_EDITOR, User.Role.RND_EDITOR)

    def get(self, request):
        recent_batches = UploadBatch.objects.select_related("period", "uploaded_by").order_by("-created_at")
        page_obj = paginate(request, recent_batches, page_param="imports_page", per_page=8)
        return render(request, self.template_name, {"form": UploadBatchForm(), "recent_batches": page_obj.object_list, "imports_page_obj": page_obj})

    def post(self, request):
        form = UploadBatchForm(request.POST, request.FILES)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.uploaded_by = request.user
            batch.save()
            process_upload_batch.delay(batch.id)
            messages.success(request, "Wsad zostal przyjety do przetwarzania. Sprawdz status i log importu.")
            return redirect("upload-batch-detail", pk=batch.pk)

        recent_batches = UploadBatch.objects.select_related("period", "uploaded_by").order_by("-created_at")
        page_obj = paginate(request, recent_batches, page_param="imports_page", per_page=8)
        return render(request, self.template_name, {"form": form, "recent_batches": page_obj.object_list, "imports_page_obj": page_obj})


class UploadBatchDetailView(LoginRequiredMixin, RoleAccessMixin, View):
    template_name = "imports/upload_detail.html"
    allowed_roles = (User.Role.ADMIN, User.Role.PROD_EDITOR, User.Role.RND_EDITOR)

    def get(self, request, pk):
        batch = get_object_or_404(
            UploadBatch.objects.select_related("period", "uploaded_by").prefetch_related("logs"),
            pk=pk,
        )
        recent_batches = UploadBatch.objects.select_related("period").order_by("-created_at")
        page_obj = paginate(request, recent_batches, page_param="imports_page", per_page=8)
        log_page_obj = paginate(request, batch.logs.all(), page_param="logs_page", per_page=10)

        return render(
            request,
            self.template_name,
            {
                "batch": batch,
                "logs": log_page_obj.object_list,
                "logs_page_obj": log_page_obj,
                "recent_batches": page_obj.object_list,
                "imports_page_obj": page_obj,
            },
        )
