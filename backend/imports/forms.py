from django import forms
from .models import UploadBatch


class UploadBatchForm(forms.ModelForm):
    class Meta:
        model = UploadBatch
        fields = ["period", "source", "file"]
