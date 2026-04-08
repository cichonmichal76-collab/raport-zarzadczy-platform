from django.urls import path

from .views import UploadBatchCreateView, UploadBatchDetailView

urlpatterns = [
    path("upload/", UploadBatchCreateView.as_view(), name="upload-batch"),
    path("batch/<int:pk>/", UploadBatchDetailView.as_view(), name="upload-batch-detail"),
]
