# Пример «СмартДом»: сервис телеметрии (вариант 0)

Эталон преподавателя для лабораторной работы 1. Сущности — `Device` и
`Reading` из словаря курса ([лекция 01](../../../curriculum/Лекция_01_Введение_в_распределенные_системы.md));
приёмы Dockerfile и compose — из [лекции 02](../../../curriculum/Лекция_02_Контейнеры.md).
Ваша работа делает то же самое, но под параметры **своего** варианта
([Варианты.md](../Варианты.md), №46–70) — копировать этот код в сдачу нельзя.

## Что внутри

| Файл | Что показывает |
| --- | --- |
| `app/main.py` | FastAPI-сервис: `POST /readings`, `GET /devices/{id}/readings`, `GET /health`; 503 при недоступном Redis; graceful shutdown через lifespan |
| `Dockerfile` | Multi-stage («цех → витрина»), кэш слоёв (requirements до кода), числовой non-root UID, HEALTHCHECK exec-формой без curl |
| `compose.yaml` | Сервис + Redis, именованный volume, `depends_on: condition: service_healthy`, labels и env по стандарту лабы |
| `.dockerignore` | Что не пускаем в контекст сборки |

## Запуск (PowerShell)

```powershell
docker compose up --build -d
Invoke-RestMethod -Method Post -Uri http://localhost:8080/readings -ContentType "application/json" -Body '{"device_id":"dev-42","sensor":"temperature","value":21.5}'
Invoke-RestMethod http://localhost:8080/devices/dev-42/readings
docker compose ps          # STATUS обоих сервисов должен стать healthy
```

## Что проверить руками (мини-эксперименты)

```powershell
# 1. Данные переживают пересоздание контейнеров (volume, не writable-слой)
docker compose down        # БЕЗ -v — volume остаётся
docker compose up -d
Invoke-RestMethod http://localhost:8080/devices/dev-42/readings   # показания на месте

# 2. Частичный отказ: сервис живёт без Redis, но честно отвечает 503
docker compose stop redis
Invoke-RestMethod http://localhost:8080/health -SkipHttpErrorCheck   # 503
docker compose start redis

# 3. Graceful shutdown: в логах — строка про завершение, exit code 0
docker compose stop telemetry
docker compose logs telemetry | Select-String "graceful"
docker compose ps -a
```

Примечание: `-SkipHttpErrorCheck` доступен в PowerShell 7+; в Windows
PowerShell 5.1 используйте `curl.exe -i http://localhost:8080/health`.

## Уборка

```powershell
docker compose down -v   # -v удаляет и volume с данными
```
