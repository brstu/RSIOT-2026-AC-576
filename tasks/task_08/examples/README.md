# Примеры ЛР08 на «СмартДоме» (вариант 0 — эталон преподавателя)

Сквозной пример курса — IoT-платформа «СмартДом» (Device, Sensor,
Reading, Hub, Rule, Alert). Здесь — эталонная реализация лабораторной:
сервис приёма показаний `ingest-reading` с метриками Prometheus,
Helm-чарт и алерт по SLO.

**Параметры варианта 0:** `prefix=smarthome_`, `slo=99.9%`, `p95=300ms`,
`alert="5xx>1% за 10м"` (+ burn-rate-алерт из лекции 24 — как бонус
«recording rules»).

## Состав

```text
examples/
├── README.md                  # этот файл
├── app/
│   ├── server.js              # Node.js: POST /readings + GET /metrics
│   ├── package.json
│   └── Dockerfile
├── helm/smarthome-app/
│   ├── Chart.yaml
│   ├── values.yaml            # prefix, SLO, replicas, resources
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── servicemonitor.yaml
│       └── prometheusrule.yaml
└── dashboards/
    └── queries.md             # PromQL для трёх панелей Grafana
```

## Как запустить

```bash
# 1. Мониторинг (см. «Быстрый первый успех» в readme лабы)
helm install monitoring prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

# 2. Образ приложения (из каталога app/)
docker build -t smarthome-ingest:0.1.0 app/
minikube image load smarthome-ingest:0.1.0

# 3. Приложение чартом
helm install smarthome-app helm/smarthome-app -n app-smarthome --create-namespace

# 4. Нагрузка и проверка метрик
kubectl port-forward svc/smarthome-app 8080:80 -n app-smarthome
curl -X POST localhost:8080/readings -H "Content-Type: application/json" -d '{"deviceId":"d-1","type":"temperature","value":22.5}'
curl -s localhost:8080/metrics | grep smarthome_
```

Ожидаемо: в Prometheus (Status → Targets) появляется цель
`smarthome-app`, метрики `smarthome_readings_total`,
`smarthome_ingest_duration_seconds_bucket`, `smarthome_hub_connections`.

## Чем пример отличается от вашей работы

- prefix и пороги SLO — из **вашего** варианта, не `smarthome_`;
- приложение — ваше из ЛР01/ЛР02 (пример показывает только приёмы);
- слепое копирование заметно на защите: вопросы задаются по вашему коду.
