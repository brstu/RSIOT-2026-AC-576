# 🚀 Quick Start: брокер за 10 минут

## Чек-лист готовности

- [ ] Docker Desktop запущен (`docker --version` работает)
- [ ] Python 3.12 (`python --version`)
- [ ] Репозиторий склонирован, вы в `tasks/task_04/examples/`

## Шаг 1. Поднять Kafka (одна нода, KRaft — без ZooKeeper)

```powershell
cd examples
docker compose up -d
docker ps        # контейнер smarthome-kafka должен быть Up
```

Первый запуск тянет образ — 1–2 минуты.

## Шаг 2. Создать топик

```powershell
docker exec smarthome-kafka /opt/kafka/bin/kafka-topics.sh --create --topic readings.thermo --partitions 6 --replication-factor 1 --bootstrap-server localhost:9092
docker exec smarthome-kafka /opt/kafka/bin/kafka-topics.sh --describe --topic readings.thermo --bootstrap-server localhost:9092
```

`--describe` должен показать 6 партиций с Leader: 1.

## Шаг 3. Проверить «руками» (два окна PowerShell)

Окно 1 — консюмер:

```powershell
docker exec -it smarthome-kafka /opt/kafka/bin/kafka-console-consumer.sh --topic readings.thermo --from-beginning --bootstrap-server localhost:9092
```

Окно 2 — продюсер (введите строку и Enter):

```powershell
docker exec -it smarthome-kafka /opt/kafka/bin/kafka-console-producer.sh --topic readings.thermo --bootstrap-server localhost:9092
```

Строка из окна 2 появилась в окне 1 → брокер работает. `Ctrl+C` для выхода.

## Шаг 4. Python-клиент и примеры

```powershell
pip install -r requirements.txt
python producer.py      # окно 1: шлёт события термостатов
python consumer.py      # окно 2: обрабатывает, коммитит после обработки
```

## Частые проблемы

| Симптом | Причина и лечение |
| --- | --- |
| `NoBrokersAvailable` / timeout | Kafka ещё стартует — подождите 20–30 с; проверьте `docker logs smarthome-kafka` |
| Порт 9092 занят | Остановите старые контейнеры: `docker ps` → `docker stop <id>`; либо смените порт в compose |
| `pip install confluent-kafka` падает | Обновите pip: `python -m pip install --upgrade pip`; нужен Python 3.12+ x64 |
| Консюмер «молчит» | Он читает только новые записи; перезапустите продюсера или добавьте `--from-beginning` консольному |
| Всё сломалось, хочу заново | `docker compose down -v` — сотрёт брокер вместе с данными, потом `up -d` |
