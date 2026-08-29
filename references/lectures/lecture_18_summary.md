# Лекция 18 — выжимка

**Тема:** Kubernetes основы: оркестрация, декларативность/reconcile,
архитектура, Deployment/Service/Ingress, ConfigMap/Secret, пробы, ресурсы,
RollingUpdate. Старый файл — в `archive_2025/` (сырьё переплавлено).

## Ключевые концепции (введены здесь)

- Оркестратор: размещает, лечит, масштабирует, обновляет; K8s НЕ делает
  CI, мониторинг, БД. K8s ≠ бесплатная надёжность.
- Декларативность: желаемое состояние (манифест) + **reconcile loop**
  (желаемое → реальное → шаг); аналогия термостата. Источник истины —
  манифест, не руки.
- Архитектура: control plane — kube-apiserver («единственная дверь»),
  etcd (Raft, л. 7), scheduler, controller-manager; нода — kubelet,
  kube-proxy (L4), containerd. Data plane переживает смерть мозга, но
  недолго (DNS).
- Матрёшка Pod → ReplicaSet → Deployment; новая версия = новый RS.
  Namespace. Теги образов, не :latest.
- Service (ClusterIP/NodePort/LoadBalancer) = L4 + DNS-дискавери
  (`telemetry.smartdom.svc.cluster.local`); Endpoints только готовые
  поды. Ingress (правила) + Ingress Controller (исполнитель); Gateway
  API — тизер л. 20.
- ConfigMap/Secret: конфиг вне образа; Secret = base64, не шифрование
  (л. 25); env читается на старте.
- Пробы: readiness («слать трафик?»), liveness («перезапустить?» — только
  сам процесс!), startup (прогрев). Золотое правило против
  рестарт-штормов.
- requests (бронь) / limits (OOMKill, троттлинг); RollingUpdate
  (maxUnavailable 0/maxSurge 1), rollout status/undo; canary — л. 22.

## Слоты

- **Крючок:** сбой OpenAI 11.12.2024 — телеметрия завалила apiserver всех
  кластеров, DNS-кэш маскировал 20 мин, откат через мёртвую дверь —
  `sources/Веб-находки_Лекция_18.md`.
- **Квиз-извлечение:** по л. 17 (TTL, L4/L7, TLS, HTTP/3).
- **PI-1:** сервис греется 60 с, при мёртвой БД отвечает ошибками; верный B
  (readiness с зависимостями + liveness процесса + startup); дистракторы:
  liveness на БД, initialDelay 5 c, «пробы не нужны».
- **Живой сеанс:** «Хочу 3 реплики!» — mermaid sequence kubectl→apiserver→
  etcd→контроллер→scheduler→kubelet; смерть ноды; обновление с undo.
- **Мост к лабе 5 (стартует):** kind, Deployment+пробы+ресурсы,
  Service+Ingress, ConfigMap/Secret, RollingUpdate.

## Примеры «СмартДома»

Deployment telemetry (3 реплики, ghcr.io/smartdom/telemetry:1.2.0,
namespace smartdom), Service telemetry:80→8080, Ingress
api.smartdom.local, ConfigMap ALERT_THRESHOLD_C=60.

## Студенты знают после

Оркестратор, reconcile, control plane/нода, Pod/RS/Deployment, Service,
Ingress, ConfigMap/Secret, пробы, requests/limits, RollingUpdate,
CrashLoopBackOff/ImagePullBackOff. НЕ знают ещё: PVC/StatefulSet (л. 19),
NetworkPolicy/mTLS/Gateway API (л. 20), HPA (л. 26), RBAC глубоко (л. 25).

## Презентация

`curriculum/Презентация_18_Kubernetes_основы.pptx`, 26 слайдов,
build_pres18.js. PI-разбор A,C,D→B; пауза — слайд 20 (диалог с джинном);
YAML-слайд 10. GATE: verify 0, OOXML PASS, COM 26 PNG, все просмотрены;
находки (авторы Up and Running, «20 строк») исправлены.
