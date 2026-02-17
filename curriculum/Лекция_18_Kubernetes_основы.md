# Лекция 18. Kubernetes: основы

Эта лекция знакомит с базовыми понятиями Kubernetes и даёт практические шаги для «первого деплоя». Материал построен от простого к сложному, включает мини-демо YAML-манифестов, лучшие практики и задания для самостоятельной работы.

План:

* Что такое Kubernetes и где он применяется
* Архитектура (Control Plane и узлы)
* Базовые объекты: Pod, ReplicaSet, Deployment
* Сеть и доступ: Service, Ingress
* Конфигурации и секреты: ConfigMap, Secret, переменные окружения, тома
* Надёжность: probes (liveness/readiness/startup), lifecycle hooks
* Ресурсы и планирование: requests/limits, QoS, eviction
* Обновления: RollingUpdate, паузы, откаты
* Namespaces и вводный RBAC
* Практика: деплой stateless сервиса в кластер
* Рекомендации и ссылки

Чтение:

* Kubernetes docs: Workloads, Services & Networking, Configuration, Security
* Production best practices: probes, resources, graceful shutdown

---

## 1. Что такое Kubernetes (K8s)

1. Установите kubectl и minikube.
1. Стартуйте кластер:

1. Включите Ingress (по желанию):

1. Примените YAML-файлы из разделов лекции. Для Ingress допишите `example.local` в `C:\Windows\System32\drivers\etc\hosts`, используя IP из `minikube ip`.
1. Проверьте развертывание:
Следующая задача — распределить нагрузку. Для этого используем балансировщик. Но как он поймет, куда перенаправлять трафик?

Нужно руками в нем указать все IP-адреса всех серверов и порты, где находятся приложения. Со временем нагрузка увеличивается, сервис растет, становится больше пользователей. Необходимо добавить еще один экземпляр основного сервиса. И снова приходится обновлять все руками, что очень неудобно.

В какой-то день все сервисы на третьем сервере умирают, а балансировщик продолжает отправлять туда запросы. Он не понимает, что с ними что-то не так. Самостоятельно сервисы не поднимутся, придется делать это руками. При этом пострадали мы и пользователи, у которых в лучшем случае была большая задержка, а в худшем — все зависло на полчаса.

С обновлениями приложения ситуация еще интереснее. Можем убить сразу все пять сервисов, а потом поднять их заново. Но тогда будет даунтайм, и пользователи будут ждать. Поэтому выключать сервисы надо по очереди. Первый сервис выключили, потом включили его новую версию. Если все хорошо, то версию деплоим на все остальные серверы. Да, снова руками, снова неудобно.

Потом в новом обновлении нашлась утечка памяти. Нужно откатываться на прошлую версию. И конечно, нам нужно убивать попеременно каждый сервис и заново запускать со старой версией.

Это был маленький кусочек системы. В небольших компаниях это выглядит вот так:

![alt text](image.png)

И чтобы всем этим управлять, на помощь пришел Kubernetes.

Kubernetes — оркестратор контейнеров (Docker/OCI), который автоматизирует развёртывание, масштабирование и управление приложениями. Ключевая идея — декларативная модель: вы описываете желаемое состояние (YAML), а контроллеры поддерживают кластер в этом состоянии.

Слово «Kubernetes» происходит от древнегреческого κυβερνήτης — «рулевой». Сокращение «K8s» означает 8 букв между K и s. Это открытая платформа для управления контейнеризованными приложениями и сервисами.

Kubernetes или K8S — это не просто система оркестрации. Техническое определение оркестрации — это выполнение определенного рабочего процесса: сначала сделай A, затем B, затем C. Напротив, Kubernetes содержит набор независимых, компонуемых процессов управления, которые непрерывно переводят текущее состояние к предполагаемому состоянию. Неважно, как добраться от А до С. Не требуется также и централизованный контроль. Это делает систему более простой в использовании, более мощной, надежной, устойчивой и расширяемой.

Что делает Kubernetes:

* Управляет и запускает контейнеры на узлах кластера
* Балансирует трафик и распределяет нагрузку между репликами
* Контролирует состояние, выполняет автоматические развертывания и откаты
* Подключает системы хранения (volumes, PVC)
* Предоставляет декларативный API/CLI для управления

Что Kubernetes не делает:

* Не собирает образы из исходников (это задачи CI/CD)
* Не является системой CI и не включает её из коробки
* Не поставляется с системами логирования/метрик/хранилищ (интегрируется с ними)
* Не является «панацеей» для всех проблем инфраструктуры

Почему это не просто оркестратор:

* Вместо сценариев «сначала A, потом B, затем C» — набор контроллеров, непрерывно приводящих текущее состояние к желаемому
* Нет жёстного центрального управляющего потока — проще, надёжнее, расширяемее

Зачем бизнесу Kubernetes (кратко):

* Микросервисы вместо монолитов → быстрее релизы отдельных частей
* «Лего»-подход: сервисы легко добавлять/удалять/обновлять без простоев
* Автомасштабирование под нагрузку и простой перенос между провайдерами/кластерами
* Инфраструктура как код: предсказуемость окружений и быстрые эксперименты

Кейсы применения:

* Микросервисы и API на разных языках
* Stateless веб-приложения
* Batch/cron-задачи
* Edge/On-prem/Cloud сценарии благодаря абстракциям и унифицированным API

Термины:

* Кластер: набор узлов (Nodes) под управлением Control Plane.
* Объекты: декларативные сущности API (Pod, Deployment, Service, ...).
* Контроллеры: следят и устраняют дрейф между желаемым и текущим состоянием.

 

---

## 2. Архитектура кластера

Давайте поверхностно коснёмся архитектуры K8s и его основных компонентов.

![alt text](image-1.png)

### Узлы (Worker Nodes)

На рабочих узлах запускаются контейнеры приложений и системные компоненты.

* kubelet — агент, управляющий жизненным циклом подов на узле
* kube-proxy — сетевой прокси/балансировщик для Service (или CNI). Может выполнять простейшее перенаправление потоков TCP и UDP (round robin) между набором бэкендов.
* Container runtime — Docker/Containerd/CRI-O

### Плоскость управления (Control Plane)

![alt text](image-2.png)

Отвечает за управление кластером и принятие решений о размещении/состоянии.

* kube-apiserver — точка входа API. Он предназначен для того, чтобы быть CRUD сервером со встроенной бизнес-логикой, реализованной в отдельных компонентах или в плагинах
* etcd — распределённое key–value хранилище состояния кластера, обеспечивает надёжное хранение конфигурационных данных и своевременное оповещение прочих компонентов об изменении состояния.
* kube-scheduler — планирование размещения подов на узлах. привязывает незапущенные pod'ы к нодам через вызов /binding API. Scheduler подключаем; планируется поддержка множественных scheduler'ов и пользовательских scheduler'ов.
* kube-controller-manager — запуск контроллеров (Deployment/ReplicaSet/Node/Namespace и др.)

### Контроллеры (основные виды)

* Deployment — управляет желаемым состоянием подов через ReplicaSet, обновлениями и откатами.
манифест или просто yaml-файл, в котором описываем, что нам надо. Deployment не сразу создает под, он сначала создает, ReplicaSet. Она уже поднимает поды и следит за тем, что поднято и что работает.
* ReplicaSet — поддерживает заданное количество реплик подов
* StatefulSet — как Deployment, но с устойчивыми идентификаторами/томами для каждого пода
* DaemonSet — гарантирует, что на каждом узле есть экземпляр пода (или на подмножестве узлов)
* Job — запускает поды до успешного завершения
* CronJob — запускает Job по расписанию

Лучшие практики:

* Проектируйте с предположением о сбоях (fault-tolerant mindset)
* Не храните состояние в Pod; используйте внешние БД/тома (PVC)
* Вносите изменения декларативно (YAML/Helm/kustomize), избегайте ручных правок

---

## 3. Базовые объекты: Pod → ReplicaSet → Deployment

Pod — минимальная сущность выполнения (один или несколько контейнеров, общая сеть и файловая система). Обычно вы не создаёте Pod напрямую, а используете Deployment (через ReplicaSet) для управления количеством реплик и обновлениями.

Минимальный Deployment (Nginx):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: nginx
          image: nginx:1.25
          ports:
            - containerPort: 80
```

Пояснения:

* selector.matchLabels должен совпадать с labels шаблона Pod.
* replicas — желаемое число подов.
* Deployment управляет обновлениями (создаёт/обновляет ReplicaSet).

Полезные команды:

* kubectl apply -f deployment.yaml — применить манифест
* kubectl get deploy, rs, pods -o wide — посмотреть ресурсы
* kubectl describe deploy web — детальная диагностика

Примеры команд:

```powershell
kubectl apply -f deployment.yaml
kubectl get deploy,rs,pods -o wide
kubectl describe deploy web
```

---

## 4. Сеть: Service и Ingress

![alt text](image-3.png)

Pod имеют эфемерные IP. Для стабильного доступа используйте Service.

ClusterIP Service (внутрикластерный доступ):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 80
      protocol: TCP
```

NodePort/LoadBalancer предоставляют доступ извне. Для продакшена обычно используют Ingress + Ingress Controller.

Пример Ingress (Nginx Ingress Controller):

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
    - host: example.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web
                port:
                  number: 80
```

Примечания:

* Требуется установленный Ingress Controller (например, ingress-nginx).
* DNS/hosts должны указывать на балансировщик/узлы.

---

## 5. Конфигурации и секреты: ConfigMap, Secret, Volumes

Используйте ConfigMap/Secret для параметров и чувствительных данных, а не bake в образ.

ConfigMap и Secret:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_MESSAGE: "Hello from ConfigMap"
---
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
stringData:
  DB_PASSWORD: supersecret
```

Подключение в Deployment:

```yaml
containers:
  - name: app
    image: ghcr.io/library/alpine:3.19
    env:
      - name: APP_MESSAGE
        valueFrom:
          configMapKeyRef:
            name: app-config
            key: APP_MESSAGE
      - name: DB_PASSWORD
        valueFrom:
          secretKeyRef:
            name: app-secret
            key: DB_PASSWORD
```

Советы:

* Для больших конфигов монтируйте через volumes (configMap/secret volume).
* Secret кодируется base64, но не шифруется — используйте Encryption at Rest/KMS.

---

## 6. Пробы и жизненный цикл: liveness/readiness/startup

Пробы помогают K8s понимать здоровье приложения.

Пример probes и graceful shutdown:

```yaml
containers:
  - name: app
    image: nginx:1.25
    ports:
      - containerPort: 80
    readinessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
    livenessProbe:
      httpGet:
        path: /healthz
        port: 80
      initialDelaySeconds: 15
      periodSeconds: 10
    lifecycle:
      preStop:
        exec:
          command: ["/bin/sh", "-c", "sleep 5"]
    terminationGracePeriodSeconds: 30
```

Лучшие практики:

* readiness определяет готовность принимать трафик; держите её строгой.
* liveness перезапускает зависшие контейнеры — используйте осторожно.
* startupProbe — для медленного старта (Java/. NET), чтобы не «убить» до готовности.
* Реализуйте корректное завершение: SIGTERM → остановка приёма запросов → завершение.

---

## 7. Ресурсы: requests/limits, QoS, eviction

Requests — гарантированный минимум ресурса для планировщика, Limits — верхний предел.

Пример:

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "256Mi"
```

Влияние:

* Отсутствие requests приводит к непредсказуемому размещению.
* Слишком низкие memory limits → OOMKilled.
* QoS классы: Guaranteed (req=lim), Burstable, BestEffort — влияют на eviction.

Практики:

* Калибруйте ресурсы метриками (HPA/встроенный мониторинг).
* Учитывайте пики и холодный старт.

---

## 8. Обновления и релизы: RollingUpdate, откаты

Deployment по умолчанию использует RollingUpdate: постепенно заменяет поды новой версией.

Ключевые поля стратегии:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 0
    maxSurge: 1
```

Команды:

* kubectl rollout status deploy/web — статус развёртывания
* kubectl rollout history deploy/web — история
* kubectl rollout undo deploy/web — откат к предыдущей версии

Примеры:

```powershell
kubectl rollout status deploy/web
kubectl rollout history deploy/web
kubectl rollout undo deploy/web
```

Продвинутые паттерны: Blue/Green, Canary (через разные Deployment/Service/Ingress, сервис-меши).

---

## 9. Namespaces и вводный RBAC

Namespaces изолируют ресурсы и квоты между командами/окружениями.

Пример Namespace:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: demo
```

RBAC (вводно):

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: viewer
  namespace: demo
rules:
  - apiGroups: [""]
    resources: ["pods", "services"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: viewer-binding
  namespace: demo
subjects:
  - kind: User
    name: student@example.com
roleRef:
  kind: Role
  name: viewer
  apiGroup: rbac.authorization.k8s.io
```

В продакшене используйте групповые субъекты (Groups), сервисные аккаунты и минимум прав.

---

## 10. Практика: первый деплой stateless сервиса

Предварительно: установите minikube или kind на локальную машину. Для Ingress — включите контроллер (addons в minikube).

Задача:

1. Создайте Namespace `demo`.
2. Разверните Deployment `web` с образом `nginx:1.25`, 2 реплики, readinessProbe на `/`.
3. Создайте Service `web` типа ClusterIP.
4. (Опционально) Настройте Ingress `web` на хост `example.local`.
5. Добавьте ConfigMap `app-config` и передайте переменную в контейнер.
6. Пропишите requests/limits (cpu/memory) и проверьте `kubectl describe pod`.
7. Обновите образ на новую версию и проследите rollout/undo.

Проверка:

Выполните команды:

```powershell
kubectl -n demo get all
kubectl port-forward svc/web -n demo 8080:80
curl http://example.local/
```

Типичные ошибки:

* Несовпадение селекторов Service и labels Pod.
* Пробы слишком ранние/жёсткие → под не выходит в Ready.
* Отсутствуют requests/limits → проблемы планирования.

---

## 11. Рекомендации и лучшие практики

* Декларативность и IaC: используйте GitOps/Helm/kustomize, избегайте «kubectl edit» в продакшене.
* Конфигурация вне образа: ConfigMap/Secret, версии конфигов, перезагрузка подов через аннотации.
* Здоровье и завершение: корректные probes, graceful shutdown, terminationGracePeriodSeconds.
* Ресурсы: requests/limits, HPA, мониторинг метрик (Prometheus), логирование (ELK/EFK).
* Сеть: минимально необходимые порты и политики сети (NetworkPolicy) — вводно.
* Безопасность: минимальные права RBAC, секреты — не в git, используйте Sealed Secrets/SOPS.

---

## 12. Полезные ссылки (старт)

* Kubernetes Documentation: <https://kubernetes.io/docs/home/>
* Workloads: <https://kubernetes.io/docs/concepts/workloads/>
* Services/Networking: <https://kubernetes.io/docs/concepts/services-networking/>
* Configuration: <https://kubernetes.io/docs/concepts/configuration/>
* Probes: <https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/>
* RBAC: <https://kubernetes.io/docs/reference/access-authn-authz/rbac/>

---

## 13. Домашнее задание (вариант для новичков)

Соберите простое echo-приложение (любой язык) и заверните в контейнер. Разверните в Namespace `demo` :

* Deployment (2–3 реплики) + Service (ClusterIP)
* readiness/liveness пробы
* ConfigMap с сообщением и часовой пояс; Secret с «псевдо-паролем»
* requests/limits и проверка rollout после обновления версии

Критерии приёма:

* Все поды в Ready, пробрасывается трафик через Service/Ingress
* При обновлении нет даунтайма (RollingUpdate), есть возможность rollback

Подсказка: начните с предоставленных примеров YAML и адаптируйте под своё приложение.

---

## Дополнение: Повествовательное объяснение ключевых идей

Этот блок — «рассказ по-человечески» о том, как Kubernetes живёт внутри. Его цель — связать сухие определения из лекции с интуицией и повседневной практикой.

### День из жизни кластера: «Хочу 3 реплики!»

Вы пишете YAML: «Хочу Deployment web, 3 реплики, образ nginx:1.25». Этот манифест попадает в kube-apiserver и сохраняется в etcd. Контроллер Deployment замечает новое желаемое состояние и говорит: «Сейчас 0, должно быть 3 — создаю ReplicaSet и 3 Pod». Планировщик (scheduler) подбирает узлы: где хватает CPU/памяти, где нет конфликтов с taints/affinity. На выбранных узлах kubelet скачивает образ, запускает контейнеры, настраивает сеть. Readiness-проба становится зелёной — Service начинает слать трафик на поды. Всё прозрачно, без ручной рутины.

Через время вы обновляете образ на nginx:1.26. Контроллер создаёт новый ReplicaSet и по одному меняет поды (RollingUpdate), следит за readiness. Если один под не готов — обновление «подвиснет» на нём, ожидая ваших действий. Вы читаете логи, находите проблему, правите конфиг — и rollout продолжается. Это и есть «управление к желаемому состоянию».

### Reconcile loop: не скрипт, а постоянная корректировка

Каждый контроллер в Kubernetes работает в цикле согласования (reconcile):

1) Читает желаемое состояние ресурсов из API.
2) Сверяет с реальностью (что на самом деле запущено/готово).
3) Делает маленький шаг к цели: создаёт/удаляет/обновляет дочерние объекты.

Если что-то ломается (узел «падает», контейнер зависает), контроллер просто делает ещё один шаг к желаемому состоянию. Поэтому кластер устойчив к сбоям и человеческим ошибкам — ничего не «забывается», пока не совпадёт с желаемым.

### Жизненный цикл Pod: от Pending до Terminated

1) Pod создаётся контроллером (обычно ReplicaSet).
2) Планировщик привязывает его к узлу; kubelet готовит контейнеры, монтирует тома, настраивает сеть.
3) Запуск: контейнеры стартуют, readiness/liveness начинают «щёлкать» проверки.
4) Готовность: как только readiness зелёная, Endpoint попадает в Service — трафик пошёл.
5) Завершение: удаление Pod → SIGTERM процессу → выполняется preStop → ждём terminationGracePeriodSeconds → при необходимости SIGKILL. Если ваше приложение корректно ловит SIGTERM и завершает активные запросы — обновления проходят без даунтайма.

Типичные анти-паттерны:

* Писать данные на локальный диск контейнера и ожидать, что они «останутся» после пересоздания.
* Ставить «жёсткие» liveness-пробы, которые «лечат» функциональные баги перезапуском.
* Тянуть гигабайты данных в основной контейнер при старте вместо initContainers/Job.

### Сеть изнутри: Service, DNS и типы доступа

У Pod эфемерные IP — они меняются при пересоздании. Service даёт стабильное имя и виртуальный IP (ClusterIP), а CoreDNS автоматически создаёт DNS-записи вида web.demo.svc.cluster.local. Запрос, попавший на Service, распределяется на здоровые поды (readiness обязательно!).

Коротко о типах Service:

* ClusterIP — доступ только изнутри кластера (по умолчанию).
* NodePort — открывает порт на всех нодах; удобно для стендов без внешнего LB.
* LoadBalancer — просит облако поднять внешний балансировщик.
* Headless (clusterIP: None) — без виртуального IP, отдаёт прямые адреса подов (удобно для StatefulSet и клиентской балансировки).

Ingress — это «умный HTTP-вход» по хостам/путям уровня L7. Он работает только вместе с конкретным Ingress Controller (ingress-nginx, traefik и т.д.). В новых инсталляциях часто смотрят в сторону Gateway API как более гибкой альтернативы.

### Хранение данных: PV, PVC и StorageClass «в двух словах»

Контейнеры — эфемерны. Если нужны постоянные данные — используйте PVC (PersistentVolumeClaim): это «заявка» на хранилище. Kubernetes сопоставит её с PV (реальный диск/том) через StorageClass. Приложение монтирует PVC как обычный каталог в контейнере.

Правило трёх:

* emptyDir — для временных файлов (исчезают при пересоздании Pod).
* PVC — для постоянных данных приложения (логи, кэш, артефакты).
* Управляемые БД — зачастую лучше держать вне кластера (RDS/Cloud SQL), если вы не готовы администрировать stateful-нагрузку внутри K8s.

### Пробы здоровья: зачем три вида

* readinessProbe — можно ли сейчас отправлять трафик? Если «красная», Service не будет слать запросы.
* livenessProbe — жив ли процесс? Если «красная», kubelet перезапустит контейнер.
* startupProbe — полезна для медленного старта (JVM/.NET): пока она «ждёт», остальные пробы молчат и не «убивают» процесс.

Рецепт: сделайте readiness максимально честной (проверка ключевых зависимостей), liveness — аккуратно и только для явных зависаний, startup — для «долго разогревающихся» приложений.

### Ресурсы и автомасштабирование: не забывайте про HPA

Requests — это «минимум, который обещан планировщиком», limits — потолок. Память не резиновая: при превышении limit процесс получит OOMKilled. CPU при нехватке будет троттлиться.

Автомасштабирование:

* HPA добавляет/убирает реплики по метрикам (часто CPU%).
* VPA подсказывает/меняет requests/limits для одной реплики (в продакшене используют осторожно).

### Релизы без стресса: практические приёмы

* Стратегия по умолчанию RollingUpdate обычно достаточна. Для «страховки» ставьте maxUnavailable: 0, maxSurge: 1.
* `kubectl rollout pause/resume` — удобно, когда хотите изменить сразу несколько параметров и потом «свести» обновление.
* Не забывайте «дергать» Pod при изменении ConfigMap/Secret — добавляйте аннотацию в podTemplate (это запустит новый ReplicaSet).
* Фиксируйте версии образов или используйте digest. Никогда не `:latest` в проде.

### Безопасность на практике: ServiceAccount и RBAC

Каждый Pod может иметь токен доступа к API. Если приложению не нужен доступ — выключайте автомаунт токена (`automountServiceAccountToken: false`). Если нужен — создавайте отдельный ServiceAccount с минимумом прав и привязывайте Role/ClusterRole только к этому аккаунту.

### Практика на Windows (PowerShell): короткий маршрут

1. Установите kubectl и minikube.
2. Стартуйте кластер:

```powershell
minikube start --cpus=2 --memory=4096
```

3. Включите Ingress (по желанию):

```powershell
minikube addons enable ingress
```

4. Примените YAML-файлы из разделов лекции. Для Ingress допишите `example.local` в `C:\Windows\System32\drivers\etc\hosts`, используя IP из `minikube ip`.

5. Проверьте развертывание:

```powershell
kubectl -n demo get pods -o wide; kubectl -n demo get svc,ingress
kubectl -n demo rollout status deploy/web
```

### Шпаргалка по отладке

```powershell
kubectl get events --sort-by=.lastTimestamp -A
kubectl -n demo describe pod <имя-пода>
kubectl -n demo logs <имя-пода> --all-containers
kubectl -n demo exec -it <имя-пода> -- sh
kubectl -n demo get endpoints web -o yaml
```

Типовые симптомы → куда смотреть:

* Pending — не хватает ресурсов/несовпадение nodeSelector/taints.
* CrashLoopBackOff — ошибка в старте приложения; логи контейнера, пробы.
* ImagePullBackOff — опечатка в имени образа/нет доступа к реестру (Secret для pull).
* Readiness «красная» — Service не шлёт трафик: проверьте зависимости (БД, очереди).

### Наблюдаемость одним взглядом

* Метрики: Prometheus + kube-state-metrics + Grafana.
* Логи: EFK/ELK или Loki.
* Трейсинг: OpenTelemetry + Jaeger/Tempo.

### Дополнительные ссылки

* Storage: <https://kubernetes.io/docs/concepts/storage/>
* HPA: <https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/>
* Gateway API: <https://gateway-api.sigs.k8s.io/>

### Мини-глоссарий и короткий FAQ

Глоссарий:

* Pod — минимальная сущность выполнения, общая сеть и тома для контейнеров.
* ReplicaSet — поддержание заданного числа подов.
* Deployment — декларативное управление ReplicaSet и обновлениями.
* Service — стабильная точка доступа к группе подов.
* Ingress — L7-маршрутизация трафика извне в кластер.
* PV/PVC — постоянное хранилище и запрос на него.

FAQ:

— Можно ли запускать БД в Kubernetes?
Можно, но это требует StatefulSet и надёжного хранилища. Без опыта проще использовать управляемые БД облака.

— Почему «пропали» файлы после рестарта Pod?
Файловая система Pod эфемерна. Используйте PVC или внешний сторедж.

— Нужен ли Docker?
Нужен контейнерный runtime. Сейчас чаще используются containerd/CRI-O; образы остаются OCI-совместимыми.
