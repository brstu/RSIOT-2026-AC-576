# Эталонный пример (вариант 0): PostgreSQL «СмартДома» со StatefulSet и бэкапом

История показаний «СмартДома» в PostgreSQL: StatefulSet + Headless
Service + свой StorageClass, бэкап CronJob'ом в отдельный PVC и
восстановление Job'ом. Это **вариант 0** — эталон: копировать 1:1
нельзя, параметры вашей сдачи — по варианту.

## Состав

```text
examples/
├── README.md
└── k8s/
    ├── namespace.yaml        # smartdom (общий с лабой 5)
    ├── storageclass.yaml     # smartdom-standard → local-path (kind)
    ├── secret.yaml           # пароль PostgreSQL (учебная заглушка)
    ├── headless-service.yaml # smartdom-db-hl (clusterIP: None)
    ├── statefulset.yaml      # smartdom-db: PGDATA, volumeClaimTemplates
    ├── backup-pvc.yaml       # отдельный PVC под копии
    ├── backup-cronjob.yaml   # pg_dump каждые 15 минут
    └── restore-job.yaml      # восстановление из последней копии
```

## Деплой и тестовые данные

```powershell
kubectl apply -f k8s/
kubectl -n smartdom get pods -w        # дождаться smartdom-db-0 READY 1/1
kubectl -n smartdom exec -it smartdom-db-0 -- psql -U app -d smartdom -c "CREATE TABLE readings(id SERIAL, device TEXT, value NUMERIC); INSERT INTO readings(device, value) VALUES ('dev-7', 21.5);"
kubectl -n smartdom exec -it smartdom-db-0 -- psql -U app -d smartdom -c "SELECT * FROM readings;"
```

## Эксперимент: данные переживают под

```powershell
kubectl -n smartdom delete pod smartdom-db-0
kubectl -n smartdom get pods -w        # reconcile вернёт smartdom-db-0
kubectl -n smartdom exec -it smartdom-db-0 -- psql -U app -d smartdom -c "SELECT * FROM readings;"
# строка dev-7 | 21.5 на месте: её хранил PVC, а не под
```

## Бэкап и восстановление

```powershell
# CronJob каждые 15 минут; для быстрой проверки — разовый запуск руками:
kubectl -n smartdom create job backup-now --from=cronjob/db-backup
kubectl -n smartdom logs job/backup-now
# осознанно ломаем:
kubectl -n smartdom exec -it smartdom-db-0 -- psql -U app -d smartdom -c "DROP TABLE readings;"
# восстанавливаем из последней копии (засеките время — это ваш RTO):
kubectl apply -f k8s/restore-job.yaml
kubectl -n smartdom logs job/db-restore -f
kubectl -n smartdom exec -it smartdom-db-0 -- psql -U app -d smartdom -c "SELECT * FROM readings;"
```

## Что показывает пример (сверьте со своей сдачей)

- **PVC хранит, контроллер управляет:** удалите даже StatefulSet —
  `kubectl -n smartdom get pvc` покажет живой `data-smartdom-db-0`.
- **PGDATA в подкаталоге** — обход граблей `lost+found` первого запуска.
- **Пароль в Secret**, не в манифесте StatefulSet.
- **Бэкап в отдельный PVC** — копия не живёт на том же томе, что данные.
  Внимание: по правилу 3-2-1 этого мало — в проде копия обязана уезжать
  за пределы кластера и провайдера (лекция 19, кейс UniSuper).
- **restore-job.yaml** перед повторным запуском удалите:
  `kubectl -n smartdom delete job db-restore` (Job неизменяем).
