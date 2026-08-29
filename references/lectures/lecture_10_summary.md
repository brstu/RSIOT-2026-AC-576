# Лекция 10 — выжимка

**Тема:** хранилища данных в РС: KV, документные, wide-column, колоночные,
NewSQL, time-series; выбор по вокрладу. Старая лекция 09 была заглушкой —
написана с нуля. Файл: `curriculum/Лекция_10_Хранилища_данных_в_РС.md`.

## Ключевые концепции (введены здесь)

- **Вокрлад (workload)**: 4 типа у «СмартДома» — горячее чтение по ключу,
  поток записи (append, 200К Reading/с), OLAP-аналитика, транзакционное
  ядро. Метод пары: сначала вокрлад — потом хранилище.
- **Schema-on-write vs schema-on-read**: «schema-less» — миф, схема
  переезжает в читающий код и становится неявной.
- **B-дерево vs LSM**: B-tree — запись на место, чемпион чтения; LSM —
  memtable → SSTable → compaction, чемпион записи; чтение LSM ищет по
  нескольким файлам. Выбор по вокрладу, не «LSM быстрее».
- **KV**: Redis (AGPL, 8.x) / форк Valkey (BSD, LF); структуры, TTL;
  роль — кэш последних значений `sensor:<id>:last` EX 300.
- **Документные**: MongoDB; агрегат Device+sensors читается целиком;
  слабость — связи многие-ко-многим и schema-on-read.
- **Wide-column**: Cassandra/ScyllaDB; ключ партиции `(device_id, day)`
  (bucketing!) + ключ кластеризации ts; «сначала запросы, потом таблицы»;
  full scan запрещён; внутри LSM + кворумы (л. 6), consistent hashing (л. 8).
- **Колоночные (columnar)**: ClickHouse; читает только нужные колонки,
  сжатие, векторные агрегации; UPDATE неудобен. НЕ путать wide-column
  и columnar.
- **NewSQL**: Spanner/CockroachDB/Yugabyte = SQL + шардирование (л. 8) +
  Raft (л. 7); PACELC: COMMIT платит консенсусом.
- **Time-series**: TimescaleDB/InfluxDB — bucketing, downsampling, retention.
- **Polyglot persistence**: цена — несколько копий правды → мост к л. 11/13.

## Слоты

- **Крючок:** Discord 2022 — триллионы сообщений, 177 узлов Cassandra,
  hot partitions, GC-паузы → ScyllaDB + Rust data services: 72 узла,
  p99 чтения 15 мс. Вопрос «что Discord НЕ сменил?» (модель данных) —
  `sources/Веб-находки_Лекция_10.md`.
- **Квиз-извлечение:** по л. 9 (бюджет таймаутов, амплификация 27,
  состояния breaker, shedding vs backpressure).
- **PI:** «среднее за март по областям, миллиарды строк — куда?» Верный D
  (колоночное); дистракторы: Redis «самый быстрый», MongoDB «гибкие
  документы», Cassandra «для больших данных».
- **Живой сеанс:** сборка polyglot-хранения «СмартДома»: PostgreSQL
  (ядро) + Cassandra (история) + Redis (горячие значения) + ClickHouse
  (аналитика, батчи); mermaid-схема; MongoDB не понадобился.
- **Мост:** лаба 6 (K8s состояние/хранение, tasks/task_06, после л. 19):
  сегодня «что
  разворачивать», л. 19 — «как не потерять данные».

## Примеры «СмартДома»

redis-cli SET/GET/TTL кэша последнего показания; CQL-таблица readings с
партицией (device_id, day); ClickHouse GROUP BY region; JSON-документ
Device dev-17 с сенсорами.

## Студенты знают после

Вокрлад, OLTP/OLAP, schema-on-read/write, B-tree, LSM (memtable, SSTable,
compaction), KV, документная модель, ключ партиции/кластеризации,
bucketing, hot partition, columnar, NewSQL, time-series, polyglot
persistence. НЕ знают ещё: как синхронизировать копии (л. 11 транзакции,
л. 13 событийные), очереди (л. 12), K8s-хранение (л. 19).

## Презентация

`curriculum/Презентация_10_Хранилища_данных_в_РС.pptx`, 24 слайда,
«Океан» (`build_pres10.js`). PI-разбор A, B, C → D с бейджем; пауза —
слайд 17 (диалог «какой у вас вокрлад? — …большой»); маркеры 🖥 сходятся.
GATE: verify 0 ошибок, OOXML PASS, COM-экспорт 24 PNG, все просмотрены.
