# Лекция 19 — выжимка

**Тема:** Kubernetes: состояние и хранение — PV/PVC/StorageClass,
StatefulSet, Headless Service, бэкапы (RPO/RTO, 3-2-1), операторы vs
managed. Старый конспект — в `archive_2025/`.

## Ключевые концепции (введены здесь)

- Аналогия «палатка (под, emptyDir) vs квартира (PV через PVC)»; всё,
  что жалко потерять, не живёт в поде. Данные хранит **PVC/PV**, а не
  контроллер.
- Цепочка: volumeMounts → PVC (заявка разработчика) → StorageClass
  (прейскурант, CSI-драйвер) → PV (байты). Динамический провижининг;
  reclaimPolicy Delete/Retain; `WaitForFirstConsumer` (зональность
  дисков, л. 16); allowVolumeExpansion (только вверх).
- Режимы доступа: RWO = «одна НОДА» (не под!), ROX, RWX (NFS/CephFS);
  засада: 2 пода на RWO на разных нодах.
- **StatefulSet**: стабильные имена (postgres-0…), свой PVC каждой
  реплике (volumeClaimTemplates), упорядоченные операции; PVC переживают
  удаление SS (retentionPolicy опционально). SS НЕ настраивает
  репликацию СУБД. YAML-грабли: POSTGRES_PASSWORD обязателен, PGDATA —
  подкаталог (lost+found).
- **Headless Service** (clusterIP: None): DNS-имя каждому поду
  (`postgres-0.postgres-hl.smartdom.svc.cluster.local`); писать в
  лидера, читать с реплик.
- Бэкапы — три слоя: реплики (не переживают DROP TABLE) → снапшоты+PITR
  → **копия вне провайдера** (dump по CronJob). RPO/RTO; правило 3-2-1;
  «непроверенное восстановление — не бэкап».
- Выбор: managed вне кластера (по умолчанию) vs оператор в кластере
  (CloudNativePG, CNCF Sandbox 01.2025) — но не голый StatefulSet.

## Слоты

- **Крючок:** UniSuper, май 2024 — Google Cloud автоудалил приватное
  облако фонда ($125 млрд, 620 тыс. клиентов) вместе с копиями в обеих
  зонах; спасла копия у другого провайдера —
  `sources/Веб-находки_Лекция_19.md`.
- **Квиз-извлечение:** по л. 18 (reconcile, control plane, пробы,
  антипаттерн состояния).
- **PI-1:** «данные сохранит только StatefulSet»; верный B (хранит PVC;
  SS — имена/PVC на реплику/порядок); дистракторы: «только SS», «в K8s
  нельзя», «Deployment только с 1 репликой».
- **Живой сеанс:** PostgreSQL переживает смерть пода — mermaid-схема
  «под → PVC → PV» + команды INSERT/delete pod/SELECT; контрольный
  вопрос «а если умрёт диск?» → мост к бэкапам.
- **Мост к лабе 6:** StatefulSet PG + volumeClaimTemplates + Headless,
  CronJob-бэкап, тест восстановления, RPO/RTO; перечитать модели данных
  л. 10.

## Примеры «СмартДома»

PVC readings-data (10Gi RWO), StatefulSet postgres (2 реплики,
postgres:16.4, secret+PGDATA), Headless postgres-hl, слои защиты истории
показаний, RPO/RTO для показаний vs тревог.

## Студенты знают после

volume/emptyDir, PV/PVC/StorageClass/CSI, reclaimPolicy, WFFC,
RWO/ROX/RWX, StatefulSet/volumeClaimTemplates, Headless, VolumeSnapshot,
RPO/RTO, 3-2-1, оператор. НЕ знают ещё: NetworkPolicy/mesh (л. 20),
шифрование секретов (л. 25), DR-стратегии целиком (л. 28).

## Презентация

`curriculum/Презентация_19_Kubernetes_состояние_и_хранение.pptx`,
23 слайда, build_pres19.js. PI-разбор A,C,D→B; пауза — слайд 14 (диалог
пода и PVC); слайд 18 замыкает крючок (3 слоя защиты). GATE: verify 0,
OOXML PASS, COM 23 PNG, все просмотрены; находки (POSTGRES_PASSWORD/
PGDATA в YAML, тире в подписи) исправлены.
