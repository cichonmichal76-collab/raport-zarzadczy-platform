from rest_framework import serializers
from .models import ProductionRecord, ReportingPeriod, RnDRecord


class ReportingPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportingPeriod
        fields = ["id", "name", "year", "week", "start_date", "end_date", "is_active", "is_published"]


class ProductionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionRecord
        fields = [
            "id",
            "period",
            "order_number",
            "status",
            "product",
            "product_group",
            "machine",
            "completed_units",
            "planned_units",
            "work_time",
            "norm_time",
            "workers",
            "current_state",
            "problem",
            "solution",
        ]


class RnDRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RnDRecord
        fields = [
            "id",
            "period",
            "code",
            "name",
            "status",
            "progress",
            "trl_level",
            "milestone",
            "work_type",
            "parameters",
            "current_state",
            "problem",
            "solution",
        ]
