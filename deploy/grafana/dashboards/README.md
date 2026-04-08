# Dashboards Grafany

Ten katalog jest montowany do kontenera Grafany jako:

- `/var/lib/grafana/dashboards`

Możesz tu zapisywać:
- eksporty dashboardów `.json`
- gotowe dashboardy provisionowane przy starcie

Plik `provisioning/dashboards/default.yml` ustawia folder:
- `Raport Zarzadczy`

Najprostszy workflow:
1. tworzysz dashboard w Grafanie przez UI,
2. eksportujesz go do JSON,
3. wrzucasz tutaj jako plik wersjonowany.
