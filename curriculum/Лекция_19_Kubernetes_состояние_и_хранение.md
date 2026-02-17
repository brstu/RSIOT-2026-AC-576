# Лекция 19. Kubernetes: состояние и хранение

## Цель
Разобраться, как Kubernetes работает с состоянием: чем отличается эфемерное (ephemeral) от устойчивого (persistent) хранения, как использовать PersistentVolume / PersistentVolumeClaim / StorageClass, чем полезен StatefulSet и Headless Service для упорядоченных и "именованных" Pod'ов, как подключаются внешние хранилища через CSI драйверы, как организовать резервное копирование и восстановление (backup/restore) для баз данных и других stateful сервисов, а также какие есть шаблоны (init/sidecar) и анти‑паттерны.

## План
1. Ephemeral vs Persistent: emptyDir, config, данные.
2. Volumes в Kubernetes: общая модель.
3. PersistentVolume (PV) и PersistentVolumeClaim (PVC): связывание.
4. AccessModes и VolumeModes: RWO / ROX / RWX, Filesystem / Block.
5. StorageClass и динамическое провижининг.
6. StatefulSet: стабильные имена, порядок, обновления.
7. Headless Service и DNS паттерны.
8. CSI драйверы, snapshots, volume expansion.
9. Backup/Restore: инструменты (Velero, CronJob + dump), RPO/RTO.
10. Конфигурации и секреты: ConfigMap, Secret, External Secrets.
11. Шаблоны: initContainer, sidecar (backup, exporter), оператор (DB Operator).
12. Распределённое хранилище: Ceph, Longhorn, Rook, NFS, EBS/GCE PD.
13. Производительность и планирование: IOPS, topology, multi‑AZ.
14. Безопасность: шифрование, права, изоляция.
15. Практическое задание.
16. Вопросы для самопроверки.

---

## 1. Ephemeral vs Persistent
| Тип | Примеры | Характеристики | Когда использовать |
|-----|---------|----------------|--------------------|
| Ephemeral | `emptyDir`, `configMap` volume, `secret` | Живёт пока жив Pod | Кэш, временные файлы, сокеты |
| Persistent | `PersistentVolume` (EBS, NFS, Ceph) | Переживает перезапуск Pod'а | База данных, очередь, хранилище файлов |

`emptyDir`: создаётся при стартe Pod'а, удаляется при удалении Pod'а. Не для критичных данных.

## 2. Модель volume в Kubernetes
Pod определяет **mount**. Kubernetes контейнер не управляет жизненным циклом самого диска — PV/PVC отвязаны от конкретного контейнера.

## 3. PersistentVolume (PV) и PersistentVolumeClaim (PVC)
PV — абстракция физического/сетевого тома. PVC — запрос (claim) на ресурсы: размер, режим доступа.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
	name: data-pvc
spec:
	accessModes: ["ReadWriteOnce"]
	resources:
		requests:
			storage: 10Gi
	storageClassName: fast-ssd
```
После создания PVC контроллер ищет PV (статический) или создаёт динамически через StorageClass.

## 4. AccessModes и VolumeModes
- RWO (ReadWriteOnce) — монтируется для записи/чтения одним узлом (EBS, GCE PD).
- ROX (ReadOnlyMany) — несколько узлов read-only.
- RWX (ReadWriteMany) — несколько узлов read-write (NFS, CephFS).

VolumeMode:
- Filesystem — стандартный случай (монтируется как каталог).
- Block — raw device, приложения сами управляют ФС.

## 5. StorageClass и динамическое провижининг
StorageClass описывает: провижионер (CSI), параметры (тип диска, IOPS), reclaimPolicy.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
	name: fast-ssd
provisioner: ebs.csi.aws.com
parameters:
	type: gp3
	iops: "3000"
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```
`WaitForFirstConsumer` откладывает выделение до планирования Pod'а (учёт зоны).

## 6. StatefulSet
Предназначен для stateful рабочих нагрузок: порядок, стабильные hostname'ы, устойчивые PVC.

Особенности:
- Имя Pod'а: `<statefulset-name>-0`, `<name>-1`, ...
- Упорядоченные create/update/delete.
- Автоматическое создание PVC по шаблону.

Пример:
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
	name: postgres
spec:
	serviceName: postgres-headless
	replicas: 3
	selector:
		matchLabels: { app: postgres }
	template:
		metadata: { labels: { app: postgres } }
		spec:
			containers:
			- name: db
				image: postgres:15
				ports:
				- containerPort: 5432
				volumeMounts:
				- name: data
					mountPath: /var/lib/postgresql/data
	volumeClaimTemplates:
	- metadata:
			name: data
		spec:
			accessModes: ["ReadWriteOnce"]
			resources:
				requests: { storage: 10Gi }
			storageClassName: fast-ssd
```

## 7. Headless Service
Service без ClusterIP: `clusterIP: None`. Возвращает A‑записи на каждый Pod.

```yaml
apiVersion: v1
kind: Service
metadata:
	name: postgres-headless
spec:
	clusterIP: None
	selector: { app: postgres }
	ports:
	- port: 5432
```
DNS записи: `postgres-0.postgres-headless.namespace.svc.cluster.local`.
Используется для: обнаружение шардов, узлов кластера.

## 8. CSI драйверы, Snapshots, Expansion
Container Storage Interface (CSI) стандартизирует интеграцию драйверов хранилища.

Возможности:
- Dynamic provisioning.
- Volume snapshot (Point-in-time). Пример CRD `VolumeSnapshot`.
- Volume expansion (если `allowVolumeExpansion: true`).

Snapshot пример:
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
	name: data-snap
spec:
	volumeSnapshotClassName: csi-aws-snap
	source:
		persistentVolumeClaimName: data-pvc
```

## 9. Backup / Restore
Подходы:
- Логический dump (pg_dump, mysqldump, redis RDB snapshot).
- Файловый backup (копирование каталога PVC, snapshot диска через CSI).
- Инструменты: **Velero** (бэкап ресурсов + volume snapshot), **Stash**.

RPO (Recovery Point Objective) — сколько данных можно потерять (интервал между бэкапами). RTO — время восстановления.

CronJob пример логического бэкапа Postgres в MinIO:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
	name: pg-backup
spec:
	schedule: "0 * * * *" # ежечасно
	jobTemplate:
		spec:
			template:
				spec:
					containers:
					- name: dump
						image: postgres:15
						env:
						- name: PGPASSWORD
							valueFrom:
								secretKeyRef:
									name: pg-secret
									key: password
						command: ["/bin/sh","-c"]
						args:
						- |
							pg_dump -h postgres-0.postgres-headless -U app db > /tmp/dump.sql && \
							curl -X PUT -T /tmp/dump.sql http://minio.minio:9000/backups/pg-$(date +%Y%m%d%H).sql
						volumeMounts:
						- name: tmp
							mountPath: /tmp
					restartPolicy: OnFailure
					volumes:
					- name: tmp
						emptyDir: {}
```

## 10. ConfigMap и Secret
ConfigMap: неконфиденциальные параметры.
Secret: base64 данные (должно храниться зашифрованно на уровне etcd).

Примеры монтирования:
```yaml
volumeMounts:
- name: cfg
	mountPath: /etc/app/config
volumes:
- name: cfg
	configMap:
		name: app-config
```
Используйте External Secrets Operator для синхронизации с Vault/Cloud Secrets.

## 11. Шаблоны
- Init Container: подготовка данных, миграции.
- Sidecar: backup, metrics exporter, логирование.
- Operator: StatefulSet + CRD управление жизненным циклом (например, Postgres Operator).

## 12. Распределённое хранилище
| Решение | Тип | Особенности |
|---------|-----|-------------|
| EBS/GCE PD | Блочный | Привязка к зоне (AZ), RWO |
| NFS | Файловый | Простота, RWX, может быть bottleneck |
| Ceph / Rook | Объект+блок+файл | Масштабируемость, сложность управления |
| Longhorn | Блочный (репликация) | Простая установка, UI |
| Local PV | Локальные диски узла | Высокая производительность, нет переноса между узлами |

## 13. Производительность и планирование
- Учитывайте IOPS: gp2/gp3 (AWS), размер диска влияет на производительность.
- Файловая система: ext4 vs xfs (для некоторых БД предпочтения).
- Topology aware provisioning (multi‑AZ). Используйте `volumeBindingMode: WaitForFirstConsumer`.
- Следите за latency: мониторинг через Prometheus + kube-state-metrics.

## 14. Безопасность
- Шифрование at-rest (cloud provider KMS).
- Контроль доступа к Secret (RBAC, least privilege).
- Avoid running DB контейнеры с root.
- NetworkPolicies для ограничения доступа к сервису БД.
- Admission политики (OPA/Gatekeeper) — запрещать нешифрованные storage классы.

## 15. Практическое задание
Создайте кластерный Postgres (или Redis) с помощью StatefulSet:
1. StatefulSet + Headless Service.
2. PVC через StorageClass с `WaitForFirstConsumer`.
3. CronJob для логического бэкапа.
4. Документируйте RPO/RTO.
5. Проведите тест восстановления: удалите Pod `postgres-1`, убедитесь в сохранности данных.
6. Опционально: создать VolumeSnapshot и восстановиться из него (если доступен CSI snapshot контроллер).

Расширение (опционально):
- Добавить Sidecar экспорт метрик (postgres_exporter).
- Использовать Velero для бэкапа ресурсов и PV.

## 16. Вопросы для самопроверки
1. Чем отличается PV от PVC?
2. Что делает StorageClass и зачем `volumeBindingMode: WaitForFirstConsumer`?
3. Разница между RWO/ROX/RWX?
4. Для чего StatefulSet использует ordinal имена Pod'ов?
5. Что даёт Headless Service?
6. Подходы к бэкапу: логический dump vs snapshot — плюсы/минусы?
7. Что такое RPO и RTO?
8. Опасность использования `emptyDir` для критичных данных?
9. Для чего нужны CSI драйверы?
10. Какие случаи требуют RWX тома?
11. Почему важно шифрование Secret (etcd encryption)?
12. Преимущества оператора (DB Operator) над вручную настроенным StatefulSet?
13. Что такое drift в контексте хранения?
14. Как мониторить использование PVC?
15. Когда выбирать NFS vs Ceph?

---
**Итог:** Работа с состоянием в Kubernetes требует внимательного выбора типа хранилища, стратегии бэкапа и обновления. Понимание PV/PVC/StorageClass, StatefulSet и Headless Service позволяет надёжно запускать базы данных и другие stateful сервисы. Добавляя автоматизацию бэкапов и политики безопасности, вы снижаете риск потери данных и повышаете устойчивость системы.

---

## Дополнительное расширение

### 1. Аналогия: палатка vs квартира
Представьте, что Pod — как палатка на природе: вы ставите её (запускаете контейнер), потом убираете — всё внутри пропадает. Это "ephemeral" (временное) хранение. А PersistentVolume — как квартира с адресом и мебелью: вы можете съехать (Pod удалён), потом въехать снова (Pod пересоздан) — вещи на месте.

| Ситуация | Палатка (emptyDir) | Квартира (PV/PVC) |
|----------|--------------------|-------------------|
| Перезапуск приложения | Данные теряются | Данные сохраняются |
| Нужны резервные копии | Обычно нет | Да, критично |
| Скорость прототипирования | Очень быстро | Чуть сложнее (нужен PVC) |
| Подходит для | Кэш, временные файлы | БД, загрузки пользователей |

### 2. Почему нельзя просто Deployment для базы данных?
Deployment не гарантирует стабильное имя и порядок запуска. Если у вас кластер PostgreSQL или Redis Sentinel, важно знать какой экземпляр "первый" (master/primary). StatefulSet даёт предсказуемые имена (`db-0`, `db-1`) и упорядоченное обновление — при апгрейде сначала `db-0`, потом `db-1`.

### 3. Пошаговый сценарий: поднимаем PostgreSQL с сохранением данных
1. Создаём StorageClass (если нет подходящего).
2. Описываем StatefulSet с `volumeClaimTemplates`.
3. Создаём Headless Service.
4. Подключаемся к `postgres-0` и создаём таблицу.
5. Удаляем Pod `postgres-0` → Kubernetes создаёт новый `postgres-0` с тем же PVC.
6. Проверяем, что таблица осталась.

Команды (пример):
```bash
kubectl apply -f storageclass.yaml
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f postgres-headless.yaml
kubectl exec -it postgres-0 -- psql -U app -c "CREATE TABLE test(id INT);"
kubectl delete pod postgres-0
kubectl exec -it postgres-0 -- psql -U app -c "\dt" # таблица test присутствует
```

### 4. Частые ошибки новичков
| Ошибка | Почему плохо | Как правильно |
|--------|--------------|---------------|
| Использовать `emptyDir` для БД | Потеря данных при пересоздании | PVC через StatefulSet |
| Удалять PVC вручную без бэкапа | Безвозвратная потеря | Перед удалением сделать snapshot/dump |
| Одновременный доступ нескольких Pod к RWO томy | Конфликты/ошибки | Один Pod или RWX том |
| Нет мониторинга свободного места | Неожиданный отказ записи | Алёрты на 80%, расширение тома |
| Секреты в ConfigMap | Публично видны в etcd | Использовать Secret/ExternalSecrets |
| Отсутствие стратегии бэкапа | Невозможность восстановления | План: периодичность + тест восстановления |

### 5. Таблица стратегий бэкапа
| Стратегия | Что сохраняется | Скорость | Размер | Время восстановления | Применимость |
|-----------|-----------------|---------|--------|----------------------|--------------|
| Логический dump (pg_dump) | Структура + данные | Медленнее | Меньше | Дольше (импорт) | Простой перенос между версиями |
| Snapshot диска (CSI) | Битовая копия тома | Быстро | Больше | Быстро (attach) | Однотипные среды, быстрый rollback |
| Инкрементальный бэкап (pg_basebackup + WAL) | Последовательность изменений | Средне | Средне | Быстро | Минимальная потеря данных |
| Репликация на вторичный кластер | Почти real-time | Быстро | Как прод | Переключение | Высокая доступность |

### 6. Velero: быстрый обзор установки
Velero делает бэкап Kubernetes объектов + Pv (через snapshots или копию). Пример базовой установки (AWS):
```bash
velero install \
	--provider aws \
	--plugins velero/velero-plugin-for-aws:v1.8.0 \
	--bucket my-velero-backups \
	--backup-location-config region=eu-central-1 \
	--snapshot-location-config region=eu-central-1 \
	--secret-file ./credentials-velero
```
Создать бэкап:
```bash
velero backup create postgres-backup --include-namespaces db
velero restore create --from-backup postgres-backup
```
Всегда тестируйте восстановление (DR test) раз в квартал.

### 7. Проверка persistency (мини‑тест)
1. Создайте запись в таблице.
2. Удалите Pod.
3. Проверьте запись.
4. Удалите StatefulSet (не удаляя PVC), создайте заново — данные должны сохраниться.

### 8. Мониторинг хранилища
Что отслеживать:
- Использование диска (%). 
- IOPS / latency (CloudWatch, Prometheus exporter).
- Ошибки записи/чтения.
- Количество открытых файлов.

Пример Prometheus метрик: `kube_persistentvolumeclaim_resource_requests_storage_bytes`, `kubelet_volume_stats_used_bytes`.

### 9. Расширение тома (volume expansion)
Если StorageClass поддерживает расширение (`allowVolumeExpansion: true`), можно увеличить PVC:
```yaml
spec:
	resources:
		requests:
			storage: 20Gi # было 10Gi
```
Затем `kubectl apply -f pvc.yaml`. Под может потребовать перезапуск в зависимости от драйвера.

### 10. Безопасность для начинающих
- Включите шифрование Secret в etcd (фича kube-apiserver).
- Ограничьте кто может читать Secret (RBAC: `get secrets`).
- Не кладите пароль БД в образ контейнера.
- Применяйте NetworkPolicy: разрешайте трафик только от нужных сервисов.
- Ограничьте доступ по namespace (multi-tenancy). 

### 11. Best Practices список
1. Один StatefulSet — одна логическая реплика группа (не смешивать разные приложения).
2. Храните инфраструктурный код (манифесты) в Git → GitOps.
3. Обязательно тест восстановления: сценарий документация + шаги.
4. Используйте теги версий образов БД, не `latest`.
5. Автоматизируйте бэкапы CronJob + проверка успешности (exit code).
6. Разделяйте StorageClass для разных уровней производительности (fast / standard / archive).
7. Следите за квотами namespace (ResourceQuota) чтобы не исчерпать дисковую ёмкость.
8. Отдельный namespace для каждой критичной БД (упрощает управление политиками).
9. Используйте readinessProbe/livenessProbe для быстрого обнаружения проблем.
10. Документируйте RPO/RTO и проверяйте соответствие.

### 12. Частые вопросы
| Вопрос | Краткий ответ |
|--------|---------------|
| Можно ли разделить один PVC между несколькими Pod? | Только если RWX (NFS/CephFS); RWO — один узел. |
| Как удалить данные безопасно? | Сначала бэкап, затем `kubectl delete pvc`, убедитесь что reclaimPolicy корректен. |
| Что делать если заканчивается место? | Расширить PVC (если возможно) или создать новый том и мигрировать данные. |
| Зачем Headless Service при StatefulSet? | Для прямых DNS имён Pod'ов (обнаружение peer'ов). |
| Почему `WaitForFirstConsumer`? | Правильная зона/топология для диска до его выделения. |

### 13. Мини чек-лист перед продакшеном
- [ ] PVC использует подходящий StorageClass.
- [ ] Бэкап CronJob работает (логи + артефакты).
- [ ] Мониторинг заполнения диска и алёрты настроены.
- [ ] RPO/RTO согласованы с бизнесом.
- [ ] Секреты не хранятся в ConfigMap.
- [ ] Snapshot тест восстановления выполнен.
- [ ] NetworkPolicy ограничивает доступ к БД.
- [ ] Документация по процедуре disaster recovery актуальна.

---
**Дополнительный итог:** Теперь вы видите не только "что" использовать (PV/PVC/StatefulSet), но и "как" и "почему" — через простые аналогии, пошаговые сценарии и список типичных ошибок. Это база для уверенного запуска stateful приложений в Kubernetes.
