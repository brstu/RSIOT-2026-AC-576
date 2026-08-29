# Лекция 02 — выжимка

**Тема:** контейнеры: Docker, OCI, образы, compose. Написана заново по
стандарту university-teacher; старый конспект (и дубль Лекция_17) — в
`curriculum/archive_2025/`.

## Ключевые концепции (введены здесь)

- Контейнер — **процесс хоста с изоляцией**, не «лёгкая виртуалка»:
  ядро общее (у VM — своя гостевая ОС); Docker Desktop на Windows сам
  живёт в VM (WSL2).
- Три кита: namespaces (видимость), cgroups (лимиты, OOM-kill), слои
  union FS; записываемый слой умирает вместе с контейнером.
- Образ = стопка read-only слоёв + метаданные; порядок инструкций
  Dockerfile управляет кэшем (requirements раньше кода).
- Тег — изменяемая метка (`latest` — просто дефолт), digest (`sha256:`) —
  неизменяемый хэш; OCI — стандарт, образ переносим между рантаймами.
- Dockerfile-минимум: non-root USER, HEALTHCHECK (exec-форма, без curl
  в slim), EXPOSE — документация, порт открывает `-p`.
- Запуск: `-p` порты, `-e` конфиг, volume (прод) / bind-mount (dev),
  пользовательская сеть → DNS по имени; `host.docker.internal`.
- Гигиена: multi-stage («цех → витрина»), slim/distroless, скан (trivy),
  лимиты `--memory/--cpus`; секреты не в ENV Dockerfile.
- Compose v2 (`docker compose`, файл `compose.yaml`, без `version:`);
  `depends_on` — порядок старта, не готовность → ретраи из лекции 01.

## Слоты

- **Крючок:** компрометация Trivy 19–23.03.2026 (TeamPCP, перезаписан
  `latest` на Docker Hub, инфостилер) — `sources/Веб-находки_Лекция_02.md`.
- **Квиз-извлечение:** лекция 01 — 4 сценария «нет ответа», безопасный
  ретрай, SLI/SLO/SLA, p99 против среднего.
- **PI-1:** контейнер пересоздали — что с `/data/readings.db`; верный B
  (writable-слой умер, нужен volume); дистракторы: данные «в образе»,
  «автосохранение» (commit), «файлы на диске хоста».
- **Живой сеанс:** Dockerfile телеметрии в три подхода: наивный →
  кэш-порядок → non-root + HEALTHCHECK.
- **Мост к лабе 1:** контейнеризация сервиса «СмартДома» (tasks/task_01),
  критерии = кэш слоёв, non-root, HEALTHCHECK, compose.

## Примеры «СмартДома»

FastAPI-сервис телеметрии (POST /readings, GET /health; Device, Sensor,
Reading); Node-нотификатор `Alert` (multi-stage); compose: telemetry +
redis (том readings-data); изоляция cgroups = частичный отказ вместо
полного (связка с лекцией 01).

## Студенты знают после

Термины: образ, слой, writable-слой, тег vs digest, реестр, OCI,
namespaces, cgroups, multi-stage, volume/bind-mount, HEALTHCHECK,
compose. НЕ знают ещё: REST/gRPC подробно (л. 3), Kubernetes (л. 18),
supply chain/SLSA (л. 25).

## Презентация

`curriculum/Презентация_02_Контейнеры.pptx`, 25 слайдов, палитра «Океан»
(`deck_common.js` + `build_pres02.js`). PI-разбор — слайды 12–15
(A, C, D → верный B); пауза — слайд 16; маркеры 🖥 в лекции совпадают
с колодой.
