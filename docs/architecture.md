# Architektura V1

## Komponenty

- `nginx` - reverse proxy, static, media
- `web` - Django + Gunicorn
- `worker` - Celery worker dla importów
- `db` - PostgreSQL
- `redis` - broker i cache

## Moduły Django

- `accounts` - użytkownicy, role, grupy
- `reports` - okresy raportowe i dane dashboardowe
- `imports` - wsady Excel i logi importu
- `publishing` - publikacja raportów read-only

## Frontend

- Django templates
- HTMX/Alpine gotowe do dodania
- ECharts jako biblioteka wykresów
