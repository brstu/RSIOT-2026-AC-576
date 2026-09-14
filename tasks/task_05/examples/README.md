# Эталонный пример (вариант 0): сервис телеметрии «СмартДома»

Минимальный stateless HTTP-сервис платформы «СмартДом»: принимает
показания датчиков (`Reading`) от Hub'ов и отдаёт счётчик принятого.
Это **вариант 0** — эталон преподавателя: копировать 1:1 нельзя,
параметры и логика вашей сдачи — по вашему варианту.

## Состав

```text
examples/
├── README.md            # этот файл
├── Dockerfile           # multi-stage, non-root
├── src/
│   ├── app.py           # FastAPI: /readings, /health/live, /health/ready
│   └── requirements.txt
└── k8s/
    ├── namespace.yaml   # namespace smartdom
    ├── configmap.yaml   # ALERT_THRESHOLD_C
    ├── secret.yaml      # DB_PASSWORD (учебная заглушка!)
    ├── deployment.yaml  # 2 реплики, пробы, ресурсы, RollingUpdate 0/1
    └── service.yaml     # ClusterIP telemetry:80 → 8080
```

## Запуск локально (без Kubernetes)

```powershell
docker build -t smartdom-telemetry:0.1.0 .
docker run --rm -p 8080:8080 -e STU_ID=00000 -e STU_VARIANT=0 smartdom-telemetry:0.1.0
curl http://localhost:8080/health/ready
curl -X POST http://localhost:8080/readings -H "Content-Type: application/json" -d '{"device_id":"dev-1","sensor":"temp","value":21.5}'
curl http://localhost:8080/stats
```

## Запуск в kind

```powershell
kind create cluster --name smartdom
docker build -t smartdom-telemetry:0.1.0 .
kind load docker-image smartdom-telemetry:0.1.0 --name smartdom
kubectl apply -f k8s/
kubectl -n smartdom get pods
kubectl -n smartdom port-forward svc/telemetry 8080:80
```

## Что показывает пример (сверьте со своей сдачей)

- **Пробы по «золотому правилу» лекции 18:** liveness (`/health/live`) —
  только сам процесс; readiness (`/health/ready`) — готовность делать
  работу (здесь — окончание прогрева).
- **Graceful shutdown:** сервис ловит SIGTERM, дологирует остановку.
- **Конфигурация вне образа:** порог тревоги — из ConfigMap, «пароль» —
  из Secret; при старте логируются STU_* из ENV.
- **RollingUpdate 0/1:** обновление без даунтайма; проверьте
  `kubectl -n smartdom get rs` до и после `kubectl set image`.
- **Идемпотентность (лекции 1 и 3):** повтор POST с тем же заголовком
  `Idempotency-Key` не создаёт дубль показания. Внимание: дедупликация
  здесь — в памяти пода, при 2+ репликах повтор может попасть на соседний
  под; продовая дедупликация живёт в общем хранилище (лекция 19, ЛР06).
