# Пример «СмартДом»: devices → alerts (вариант 0)

Эталон преподавателя для лабораторной работы 2. Сценарий — «телеметрия →
тревога»: сервис `devices` принимает показания (`Reading`) и при превышении
порога вызывает сервис `alerts` (`POST /alerts`, создание `Alert`).
Сущности — из словаря курса ([лекция 01](../../../curriculum/Лекция_01_Введение_в_распределенные_системы.md)),
приёмы вызова — из [лекции 03](../../../curriculum/Лекция_03_Взаимодействие_в_распределенных_системах.md).

Ваша работа делает то же самое, но под **свой** сценарий из
[Варианты.md](../Варианты.md) — копировать этот сценарий и код в сдачу нельзя.

## Что внутри

| Файл | Что показывает |
| --- | --- |
| `devices/app/main.py` | Caller: `POST /readings`; при `value > 60.0` — межсервисный вызов alerts |
| `devices/app/client.py` | Сердце лабы: таймауты httpx, ретраи только сети/таймауты/5xx, backoff + full jitter, потолок попыток, Idempotency-Key до первой попытки |
| `devices/app/retry_storm.py` | Эксперимент части 5: N клиентов, окно отказа, ASCII-гистограмма волн ретраев |
| `alerts/app/main.py` | Callee: `POST /alerts` (неидемпотентный по природе), хранилище «ключ → ответ», replay с заголовком `Idempotency-Replayed`, имитация потерянного ответа, окно отказа `POST /outage` |
| `compose.yaml` | Оба сервиса, DNS по имени, healthcheck, флаги поведения через переменные окружения |

Пример **намеренно сломан из коробки**: `IDEMPOTENCY=off` и
`SIMULATE_LOST_RESPONSE=on` — первый ответ alerts задерживается дольше
read-таймаута клиента (0.8 с < 2.0 с), клиент ретраит, тревога дублируется.

## Запуск (PowerShell)

```powershell
docker compose up --build -d
docker compose ps                        # оба сервиса должны стать healthy

# Дубль без ключа: одно показание -> ДВЕ тревоги
Invoke-RestMethod -Method Post -Uri http://localhost:8080/readings -ContentType "application/json" -Body '{"device_id":"dev-7","sensor":"temperature","value":72.5}'
Invoke-RestMethod http://localhost:8081/alerts

# Чиним: ключ идемпотентности
$env:IDEMPOTENCY = "on"
docker compose up -d devices
Invoke-RestMethod -Method Post -Uri http://localhost:8080/readings -ContentType "application/json" -Body '{"device_id":"dev-7","sensor":"temperature","value":80.1}'
Invoke-RestMethod http://localhost:8081/alerts    # добавилась только ОДНА
```

В поле `alert.attempt_log` ответа видно всю историю: `ReadTimeout` → пауза
backoff → `HTTP 201`, а при включённом ключе — `replayed=true` на повторе.

## Эксперимент retry storm

```powershell
# Волны без джиттера: пик = все клиенты в одном окне 0.2 c
docker compose exec devices python -m app.retry_storm --clients 30 --outage 3 --jitter off

# С джиттером: волна размазана, пик в разы ниже
docker compose exec devices python -m app.retry_storm --clients 30 --outage 3 --jitter on

# Очистить журнал тревог после экспериментов
curl.exe -X DELETE http://localhost:8081/alerts
```

Сравнивайте строку `пик запросов в одном окне`. Прогоны недетерминированы
(джиттер — случайность): числа будут отличаться, картина волн — нет.
С джиттером отдельный клиент может истратить попытки раньше конца окна
отказа — увеличьте `--attempts`, это тоже наблюдение для отчёта.

## Флаги поведения (переменные окружения devices)

| Флаг | По умолчанию | Смысл |
| --- | --- | --- |
| `IDEMPOTENCY` | `off` | Слать ли `Idempotency-Key` (генерируется до первой попытки) |
| `RETRY_JITTER` | `on` | Full jitter в паузах между ретраями |
| `SIMULATE_LOST_RESPONSE` | `on` | Метить первую попытку — alerts задержит ответ дольше таймаута |
| `CLIENT_READ_TIMEOUT` / `MAX_ATTEMPTS` / `BACKOFF_BASE` / `BACKOFF_CAP` | `0.8` / `4` / `0.2` / `2.0` | Параметры клиента (`devices/app/client.py`) |

## Уборка

```powershell
docker compose down
Remove-Item Env:IDEMPOTENCY -ErrorAction SilentlyContinue
```
