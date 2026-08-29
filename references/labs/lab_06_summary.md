# Лаба 06 — выжимка

**Тема:** Kubernetes: состояние и хранение (`tasks/task_06`).
Лекции-основы: 19 (стейт в K8s), 10 (хранилища), 16 (shared
responsibility). Сырьё — старая ЛР03 (`archive_2025/task_03`,
снапшот сидов — `archive_2025/task_06_src`); методичка 2025 — справочник.

## Состав

- `readme.md` — README с метками, 4 части, правила ИИ и пересдачи 85 %,
  10 контрольных вопросов; окружение — из лабы 5 (без своего
  QUICK_START).
- `Макет_отчета.md` — титул 2026, таблица критериев = README, разделы
  «Зачем в реальных системах» и «Использование ИИ», место под
  измеренные RPO/RTO.
- `Варианты.md` — 45+ вариантов (postgres/redis, размер PVC,
  storageClass default/ssd/premium, cron-расписание; расписания в
  код-спанах).
- `examples/` — вариант 0: PostgreSQL «СмартДома» — StorageClass-алиас
  `smartdom-standard` (local-path, WFFC), Secret, Headless
  `smartdom-db-hl`, StatefulSet `smartdom-db` (PGDATA-подкаталог,
  pg_isready readiness, volumeClaimTemplates 1Gi), backup-PVC,
  CronJob pg_dump (*/15, latest.sql), restore-Job.

## Задание (4 части)

1. Быстрый первый успех (30–40 мин): эталон + «удали под — данные живы».
2. Свой StatefulSet по варианту (PGDATA/appendonly, secret, метки).
3. Доказательство сохранности: delete pod И delete statefulset
   (PVC живут) со скриншотами и объяснением.
4. Бэкап CronJob по расписанию варианта + тест восстановления
   (осознанный DROP → restore-Job) + измеренные RPO/RTO.

## Оценивание

Критерии 100: манифесты 25, сохранность 20, CronJob 20, restore+RPO/RTO
15, StorageClass/PVC 10, метаданные 5, документация 5. Бонусы 15:
S3/MinIO +5, Helm/Kustomize +4, мониторинг бэкапов +3, CloudNativePG +3.
Пересдача 85 %, защита по своему коду, сдача PR + 2 ревью,
`students/<NameLatin>/task_06/{doc,src}`.

## Связи

Мост из лекции 19 ведёт сюда. Пример подчёркивает: бэкап в отдельный PVC
внутри кластера НЕ закрывает 3-2-1 (кейс UniSuper) — прод-копия уезжает
за пределы провайдера (бонус S3). Следующая лаба блока — 7 (IaC+GitOps,
task_07, с нуля, после лекций 21–22).
