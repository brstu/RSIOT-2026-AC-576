# Examples — вариант 0 (термостаты «СмартДома»)

Эталонная реализация лабораторной №4 на сквозном примере курса:
устройства `Device` (термостаты dev-11/17/23/42) шлют события
`ReadingRecorded` (сущность `Reading`), консюмер играет роль
Rule engine и рождает `Alert` при перегреве (> 28 °C).

## Состав

| Файл | Что делает |
| --- | --- |
| `docker-compose.yml` | Kafka 4.x, одна нода, KRaft (без ZooKeeper) |
| `producer.py` | продюсер: ключ = device_id, acks=all, идемпотентность |
| `consumer.py` | группа rule-engine: ручной коммит ПОСЛЕ обработки, дедупликация по event_id (SQLite), DLQ после 3 попыток, флаг `--crash-before-commit` |
| `requirements.txt` | confluent-kafka |

## Запуск (полный сценарий)

```powershell
docker compose up -d
docker exec smarthome-kafka /opt/kafka/bin/kafka-topics.sh --create --topic readings.thermo --partitions 6 --replication-factor 1 --bootstrap-server localhost:9092
pip install -r requirements.txt
python producer.py      # окно 1
python consumer.py      # окно 2
```

## Эксперимент «дубль» (часть 4 задания)

```powershell
python consumer.py --crash-before-commit   # обработает 1 событие и умрёт ДО коммита
python consumer.py                          # рестарт: то же событие приходит снова
```

В логе второго запуска будет `duplicate skipped: <event_id>` — дубль
пришёл (at-least-once честен), но эффекта не произвёл (идемпотентность).
Чтобы увидеть дубль «во всей красе», временно закомментируйте проверку
в `process_idempotent` — и верните обратно для скриншота «после».

## Эксперимент «DLQ» (часть 5 задания)

Отправьте битое сообщение консольным продюсером:

```powershell
docker exec -it smarthome-kafka /opt/kafka/bin/kafka-console-producer.sh --topic readings.thermo --bootstrap-server localhost:9092
>это не JSON
```

Консюмер сделает 3 попытки и отправит его в `readings.thermo.dlq`;
посмотреть:

```powershell
docker exec smarthome-kafka /opt/kafka/bin/kafka-console-consumer.sh --topic readings.thermo.dlq --from-beginning --max-messages 1 --bootstrap-server localhost:9092
```

## Примечания

- `processed.db` (SQLite) создаётся рядом с consumer.py; удалите файл,
  чтобы «забыть» обработанные события.
- Порядок гарантирован только внутри партиции: события одного термостата
  упорядочены, разных — нет (лекция 12).
- Ваш вариант отличается подсистемой, полем payload и правилом тревоги —
  см. [../Варианты.md](../Варианты.md).
