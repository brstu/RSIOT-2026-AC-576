# Лабораторная работа 02. Kubernetes: базовый деплой

Описание, цели, задания и критерии приёмки приведены ниже и в локальных методических материалах каталога `tasks/`.

## Описание

В этой работе студенты выполняют базовый деплой HTTP-сервиса в Kubernetes: подготовка манифестов, настройка конфигурации, ресурсы (Deployment, Service, ConfigMap/Secret), readiness/liveness probes и минимум для локального запуска (Kind/Minikube/Minishift). Документы и примеры находятся в каталоге `tasks/task_02/`.

## Цели

* Научиться готовить Kubernetes-манифесты для простого HTTP-сервиса (Deployment + Service).
* Настроить liveness/readiness probes и политику обновления (rolling update).
* Подготовить конфигурацию через ConfigMap/Secret и смонтировать volume для данных при необходимости.
* Научиться запускать кластер локально (Kind/Minikube) и проверять корректность деплоя.

## Материалы и варианты

* [Список вариантов](./Варианты.md).
* [Методические материалы](./Лабораторная_работа_02_Методические_материалы.md)

## Задания

1. Подготовить минимальный HTTP-сервис (на базе уже выполненного в ЛР01) и контейнерный образ с теми же ограничениями, что и в ЛР01:
    * multi-stage build; финальный образ ≤ 150 MB;
    * не запускать сервис от root-пользователя; добавить корректные EXPOSE / health endpoints;
    * логировать запуск, остановку и корректное завершение работы (graceful shutdown).
2. Описать Kubernetes-манифесты:
    * Deployment с стратегией RollingUpdate и ресурсными лимитами/запросами;
    * Service (ClusterIP / NodePort — в зависимости от варианта) для доступа к приложению;
    * ConfigMap/Secret для конфигурации сервиса;
    * (опционально) PersistentVolumeClaim + volume, если вариант требует хранения данных.
3. Настроить liveness и readiness probes (HTTP) и убедиться, что они работают корректно.
4. Подготовить инструкции для локального тестирования (Kind/Minikube): создание кластера, применение манифестов, проверка статусов Pod/Service, простая smoke-тест проверка HTTP-эндпоинта.

## Артефакты (что сдаём)

* Каталог с Kubernetes-манифестами (`k8s/` или `manifests/`) и кратким README с командами деплоя и проверки.
* Dockerfile для сборки образа (multi-stage) и README с шагами сборки/запуска образа.
* Файл `README.md` с шагами проверки, используемыми командами и кратким описанием того, что сделано.

---

### Метаданные (что указываем)

В README (корне проекта/папке) укажите:

* ФИО (полностью)
* Группа
* № студенческого (StudentID)
* Email (учебный)
* GitHub username
* Номер варианта
* Дата выполнения
* ОС (версия), версия Docker Desktop/Engine, версия kubectl, Kind/Minikube

В Kubernetes-манифестах/аннотациях/labels укажите следующее (пример для Deployment/Service):

* org.bstu.student.fullname = <ФИО>
* org.bstu.student.id = <StudentID>
* org.bstu.group = <Группа>
* org.bstu.variant = <Номер варианта>
* org.bstu.course = RSIOT

В metadata разделах Helm chart / k8s manifests можно добавить лейблы для owner/slug:

* org.bstu.owner = <GitHub username>
* org.bstu.student.slug = <slug>

slug = <группа>-<StudentID>-v<вариант> (пример, feis-41-12345-v07)

<!-- START:criteria -->
## Критерии оценивания (100 баллов)

* Подготовка и корректность Kubernetes-манифестов (Deployment, Service, ConfigMap/Secret, PVC при необходимости) — 30
* Настройка liveness/readiness probes и политика обновления (RollingUpdate) — 25
* Корректность контейнеризации и образа (multi-stage, non-root, health endpoints, логирование) — 20
* Инструкции для локального тестирования (Kind/Minikube), проверка статусов и smoke-tests — 15
* Метаданные и именование (labels, аннотации, slug, ENV) и оформление README — 10

<!-- END:criteria -->

<!-- START:bonuses -->
## Бонусы (+ до 10)

* Использование Helm chart или Kustomize для управления манифестами.
* Автоматизация локального разворачивания (скрипты/Makefile) и интеграция с CI.
* Корректная настройка PersistentVolumeClaim и демонстрация работы с данными (если актуально для варианта).

<!-- END:bonuses -->

### Требования к именованию

* Kubernetes-ресурсы: префиксы в именах: app-<slug>, data-<slug>, net-<slug> — это облегчает поиск и очистку ресурсов.
* ENV: STU_ID, STU_GROUP, STU_VARIANT должны логироваться при старте контейнера.
