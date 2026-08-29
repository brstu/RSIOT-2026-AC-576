# Пример «СмартДом»: devices → alerts с circuit breaker (вариант 0)

Эталон преподавателя для лабораторной работы 3. Это **продолжение стенда
лабы 2** («телеметрия → тревога»): сервис `devices` принимает показания
(`Reading`) и при превышении порога создаёт тревогу (`Alert`) в сервисе
`alerts`. Таймауты, ретраи и Idempotency-Key уже есть из
[лабы 2](../../task_02/examples/README.md); новое — оборона по
[лекции 09](../../../curriculum/Лекция_09_Отказоустойчивость_и_chaos_engineering.md):
circuit breaker, fallback-очередь с догоном и backpressure.

Ваша работа делает то же самое, но со **своей** парой сервисов из лабы 2 и
параметрами из [Варианты.md](../Варианты.md) — копировать этот сценарий и
код в сдачу нельзя.

## Что внутри

| Файл | Что показывает |
| --- | --- |
| `devices/app/breaker.py` | Сердце лабы: конечный автомат CLOSED → OPEN → HALF-OPEN (~80 строк), порог ошибок в окне, таймаут восстановления, счётчики и журнал переходов |
| `devices/app/client.py` | Клиент из лабы 2, укороченный: таймауты + 2 попытки; над ним теперь стоит breaker |
| `devices/app/fallback.py` | Fallback-очередь тревог в jsonl-файле: деградация (202) вместо 500 |
| `devices/app/main.py` | Порядок обороны: backpressure (семафор) → breaker → вызов → fallback; фоновый догон очереди; `/health` со состоянием breaker'а |
| `devices/app/pressure_demo.py` | Эксперимент backpressure: N параллельных клиентов, часть получает честный 503 + Retry-After |
| `alerts/app/main.py` | Callee из лабы 2 + окна хаоса: `POST /outage` (503) и `POST /slow` (медленные ответы); Idempotency-Key делает догон безопасным |
| `compose.yaml` | Оба сервиса; `depends_on` намеренно нет — devices живёт без alerts |
| `chaos_demo.ps1` | Мини-chaos по канону лекции 09: steady state → впрыск (pause/stop) → серия запросов → откат → догон |

Пример **сломан из коробки**: `BREAKER=off`. Заморозьте alerts — и каждое
показание выше порога будет висеть на таймаутах (~2 с), пока не отработают
все попытки клиента. Это каскад в миниатюре.

## Запуск (PowerShell)

```powershell
docker compose up --build -d
docker compose ps                        # оба сервиса должны стать healthy

# Steady state: тревога доставляется быстро
Invoke-RestMethod -Method Post -Uri http://localhost:8080/readings -ContentType "application/json" -Body '{"device_id":"dev-7","sensor":"temperature","value":72.5}'

# Впрыск: заморозить alerts («завис», не «умер»)
docker compose pause alerts

# Каждый запрос теперь висит ~2 секунды (все таймауты и попытки клиента)
Measure-Command { Invoke-RestMethod -Method Post -Uri http://localhost:8080/readings -ContentType "application/json" -Body '{"device_id":"dev-7","sensor":"temperature","value":73.0}' } | Select-Object TotalSeconds

# Чиним: включаем breaker
docker compose unpause alerts
$env:BREAKER = "on"
docker compose up -d devices
```

Дальше — тот же впрыск с breaker'ом: первые `FAIL_THRESHOLD` (= 3) запроса
медленные (breaker набирает статистику), затем состояние `open` и мгновенные
`202` с `degraded=true`. После `docker compose unpause alerts` фоновый догон
закрывает breaker и доставляет очередь — без дублей, спасибо Idempotency-Key
из лабы 2.

## Мини-chaos одним скриптом

```powershell
# Прогон 1: BREAKER=off — каскад таймаутов (сохраните вывод для отчёта)
powershell -ExecutionPolicy Bypass -File .\chaos_demo.ps1

# Прогон 2: BREAKER=on — fail fast + fallback + догон
$env:BREAKER = "on"
docker compose up -d devices
powershell -ExecutionPolicy Bypass -File .\chaos_demo.ps1

# Режим «умер» вместо «завис» (сравните: отказ мгновенный, а не таймаут!)
powershell -ExecutionPolicy Bypass -File .\chaos_demo.ps1 -Mode stop
```

## Эксперимент backpressure

```powershell
docker compose pause alerts
docker compose exec devices python -m app.pressure_demo --clients 12
docker compose unpause alerts
```

При `BREAKER=off` четыре запроса занимают слоты (`MAX_CONCURRENT=4`) и висят
на таймаутах, остальные мгновенно получают `503` + `Retry-After` — честный
отказ вместо бесконечной очереди. При `BREAKER=on` (после открытия) слоты
освобождаются мгновенно и почти все запросы — быстрые `202`.

## Состояние breaker'а и очереди

```powershell
Invoke-RestMethod http://localhost:8080/health | ConvertTo-Json -Depth 5
Invoke-RestMethod http://localhost:8081/alerts          # тревоги: доставка и догон
curl.exe -X DELETE http://localhost:8081/alerts         # очистить между прогонами
docker compose logs devices                             # переходы breaker'а в логах
```

## Флаги поведения (переменные окружения devices)

| Флаг | По умолчанию | Смысл |
| --- | --- | --- |
| `BREAKER` | `off` | Включить circuit breaker (из коробки off — «сломано») |
| `FAIL_THRESHOLD` / `WINDOW_SIZE` | `3` / `10` | Порог: сколько ошибок в окне последних вызовов открывает breaker |
| `RECOVERY_TIMEOUT` | `8.0` | Секунд в OPEN до пробы (HALF_OPEN) |
| `HALF_OPEN_MAX` | `1` | Сколько проб пускаем одновременно в HALF_OPEN |
| `MAX_CONCURRENT` / `RETRY_AFTER` | `4` / `5` | Backpressure: слоты обработки тревог и подсказка в 503 |
| `DRAIN_INTERVAL` | `2.0` | Период фонового догона очереди, секунд |
| `CLIENT_READ_TIMEOUT` / `MAX_ATTEMPTS` | `0.8` / `2` | Клиент из лабы 2 (укороченный) |

## Уборка

```powershell
docker compose down
Remove-Item Env:BREAKER -ErrorAction SilentlyContinue
```
