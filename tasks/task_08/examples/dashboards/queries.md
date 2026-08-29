# PromQL для панелей Grafana (вариант 0, prefix=smarthome_)

Три панели из критериев лабы. Для своего варианта замените prefix.

## 1. Доступность (availability, %)

```promql
sum(rate(smarthome_readings_total{status!~"5.."}[5m]))
/
sum(rate(smarthome_readings_total[5m])) * 100
```

## 2. Задержка p95 / p99 (секунды)

```promql
histogram_quantile(0.95,
  sum(rate(smarthome_ingest_duration_seconds_bucket[5m])) by (le))
```

```promql
histogram_quantile(0.99,
  sum(rate(smarthome_ingest_duration_seconds_bucket[5m])) by (le))
```

## 3. Частота ошибок 5xx (%)

```promql
sum(rate(smarthome_readings_total{status=~"5.."}[5m]))
/
sum(rate(smarthome_readings_total[5m])) * 100
```

## Бонус: burn rate (лекция 24, recording rules)

```promql
# recording rule: sli:ingest:ratio_rate1h
sum(rate(smarthome_readings_total{status!~"5.."}[1h]))
/
sum(rate(smarthome_readings_total[1h]))
```

```promql
# burn rate против бюджета 0,1 % (SLO 99,9 %)
(1 - sli:ingest:ratio_rate1h) / 0.001
```

Алерт: `burn_1h > 14.4 and burn_5m > 14.4`, `for: 2m` — см. живой сеанс
лекции 24.

## Как проверить срабатывание алерта

```bash
# включить имитацию деградации (30 % ответов 503)
kubectl set env deployment/smarthome-app FAULT=1 -n app-smarthome
# дать нагрузку
for i in $(seq 1 300); do curl -s -o /dev/null -X POST localhost:8080/readings \
  -H "Content-Type: application/json" -d '{"deviceId":"d-1","type":"smoke","value":1}'; done
# смотреть Prometheus → Alerts (PENDING → FIRING), затем выключить: FAULT=0
```
