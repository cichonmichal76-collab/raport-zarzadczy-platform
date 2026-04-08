from datetime import date
from django.core.management.base import BaseCommand
from accounts.models import User
from reports.models import ProductionRecord, ReportingPeriod, RnDRecord


class Command(BaseCommand):
    help = "Tworzy przykładowe dane do dashboardu."

    def handle(self, *args, **options):
        period, _ = ReportingPeriod.objects.get_or_create(
            year=2026,
            week=14,
            defaults={
                "name": "Tydzień 14 / 2026",
                "start_date": date(2026, 3, 30),
                "end_date": date(2026, 4, 5),
                "is_active": True,
                "is_published": False,
            },
        )
        ReportingPeriod.objects.exclude(pk=period.pk).update(is_active=False)
        period.is_active = True
        period.save(update_fields=["is_active"])

        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                email="admin@example.com",
                password="admin12345",
                role=User.Role.ADMIN,
                display_name="Administrator",
            )

        ProductionRecord.objects.filter(period=period).delete()
        RnDRecord.objects.filter(period=period).delete()

        production_seed = [
            {
                "order_number": "3/84/2026",
                "status": "Gotowe",
                "product": "EM-D10001P000_revG",
                "product_group": "WBTS",
                "machine": "Frezarka 3X",
                "completed_units": 7,
                "planned_units": 7,
                "work_time": "02:19:33",
                "norm_time": "03:30:00",
                "workers": "Grzegorz Zimny",
                "current_state": "Praca zakończona bez odchyleń.",
                "problem": "",
                "solution": "",
            },
            {
                "order_number": "1/131/2026",
                "status": "W toku",
                "product": "EM-D10001P067_rev2",
                "product_group": "UCHWYT WBTS",
                "machine": "Frezarka 5X",
                "completed_units": 8,
                "planned_units": 10,
                "work_time": "11:03:23",
                "norm_time": "05:50:00",
                "workers": "Marcin Piekarz, Tomasz Wójcik",
                "current_state": "Wymaga rewizji normatywu.",
                "problem": "Istotne odchylenie od normatywu przy obróbce 5X.",
                "solution": "Przeprowadzić analizę ścieżki CAM i korektę normy.",
            },
            {
                "order_number": "8/56/2026",
                "status": "Stop",
                "product": "ISO EM-0017 | Wkładka stemplowa",
                "product_group": "Formy wtrysk.",
                "machine": "Przebijarka DRILL 20",
                "completed_units": 0,
                "planned_units": 5,
                "work_time": "00:59:30",
                "norm_time": "02:30:00",
                "workers": "Bartosz Buczek, Piotr Żurek",
                "current_state": "Zlecenie zatrzymane.",
                "problem": "Brak operatora.",
                "solution": "Przesunąć zasób lub zmienić kolejkę maszyn.",
            },
        ]

        rnd_seed = [
            {
                "code": "BR1",
                "name": "Modele elektromechaniczne sanek",
                "status": "W toku",
                "progress": 75,
                "trl_level": 6,
                "milestone": "Prototyp sanek",
                "work_type": "Badania przemysłowe",
                "parameters": "Liniowość <= 6um",
                "current_state": "Testy liniowości w toku.",
                "problem": "Uszkodzenie enkodera i brak decyzji zakupowej.",
                "solution": "Dostarczyć enkoder i zatwierdzić zakup hamulca.",
            },
            {
                "code": "WBTS",
                "name": "WBTS",
                "status": "W toku",
                "progress": 68,
                "trl_level": 7,
                "milestone": "Walidacja elementów systemu",
                "work_type": "Rozwój produktu",
                "parameters": "Szczelność i ergonomia",
                "current_state": "Trwają testy wdrożeniowe.",
                "problem": "Występują wycieki z jeziorek.",
                "solution": "Przeprowadzić analizę przyczyn i korektę konstrukcji.",
            },
            {
                "code": "PNC",
                "name": "PNC",
                "status": "W toku",
                "progress": 72,
                "trl_level": 7,
                "milestone": "Przygotowanie do EMC",
                "work_type": "Rozwój produktu",
                "parameters": "Gotowość dokumentacji EMC",
                "current_state": "Projekt zbliża się do testów EMC.",
                "problem": "Brak decyzji dot. położenia ekranu EMC.",
                "solution": "Wybrać wariant ekranu i zamknąć BOM.",
            },
        ]

        for row in production_seed:
            ProductionRecord.objects.create(period=period, **row)
        for row in rnd_seed:
            RnDRecord.objects.create(period=period, **row)

        self.stdout.write(self.style.SUCCESS("Utworzono przykładowe dane i konto admin/admin12345."))
