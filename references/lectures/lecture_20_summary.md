# Лекция 20 — выжимка

**Тема:** сеть Kubernetes и сервис-меш: плоская сеть/CNI, NetworkPolicy,
Gateway API, меш (sidecar→ambient→eBPF), mTLS, canary. Переработана из
старой 20 (+Gateway API, ambient, eBPF — состояние 2026); старый файл —
в `archive_2025/`.

## Ключевые концепции (введены здесь)

- Контракт сети K8s: каждому поду — IP, связь без NAT; исполняет
  **CNI** (Flannel/Calico/**Cilium**). eBPF — программы в ядре на пути
  пакета. Аналогия пары: офисное здание (опенспейс/турникеты/ресепшен/
  ассистенты).
- **NetworkPolicy**: default allow → implicit deny при первой политике;
  исполняет CNI — часть **молча игнорируют** (проверять тестом!);
  ловушка egress без DNS-правила.
- **Gateway API** (наследник Ingress): GatewayClass (реализация,
  админ) / Gateway (слушатель, инфра) / HTTPRoute (маршруты и **веса**,
  команда приложения).
- **Сервис-меш**: выносит из кода mTLS, ретраи, метрики, маршрутизацию;
  data plane (Envoy) + control plane; меш — ещё одна РС поверх вашей
  (Monzo). Ландшафт 2026: sidecar (дорого) → ambient (Istio GA,
  рекомендуемый) → eBPF/Cilium (CNI и меш сливаются).
- **mTLS**: обе стороны предъявляют сертификаты; identity SPIFFE;
  политики по личности, не по IP; кирпич zero trust (тизер л. 25).
- **Canary** через веса HTTPRoute (90/10 → … → 0/100); RollingUpdate
  меняет поды, canary — долю трафика; автоматизация — progressive
  delivery (л. 22).

## Слоты

- **Крючок:** Monzo 27.10.2017 — баг K8s + linkerd слал платежи на
  несуществующие IP, рестарт прокси вскрыл несовместимость версий —
  `sources/Веб-находки_Лекция_20.md`.
- **Квиз-извлечение:** по л. 19 (PVC, Headless, слои защиты, RPO/RTO).
- **PI-1:** «apply прошёл — что мы знаем о защите?»; верный B (ничего,
  пока не проверили тестом: CNI может молча игнорировать); дистракторы:
  «применена без ошибок», «запрещает всё», «только новые поды».
- **Живой сеанс:** canary 90/10 для telemetry v2 — HTTPRoute с weights
  (YAML в лекции), цикл весов по метрикам.
- **Мост к лабе 7:** GitOps покатит и Gateway API-манифесты; canary —
  объект progressive delivery.

## Примеры «СмартДома»

NetworkPolicy «к smartdom-db только от telemetry:5432», identity
spiffe://cluster/ns/smartdom/sa/telemetry, HTTPRoute telemetry-canary
(v1 90 / v2 10) на Gateway smartdom-gw.

## Студенты знают после

CNI, eBPF, плоская сеть, NetworkPolicy/implicit deny/«тихий CNI»,
Gateway API (3 ресурса), data/control plane, sidecar/ambient/eBPF, mTLS,
SPIFFE, canary по весам. НЕ знают ещё: IaC (л. 21), progressive delivery
(л. 22), zero trust целиком (л. 25), метрики для canary (л. 24).

## Презентация

`curriculum/Презентация_20_Сеть_и_сервис_меш.pptx`, 22 слайда,
build_pres20.js. PI-разбор A,C,D→B; пауза — слайд 14 (диалог на
архитектурном комитете); живой сеанс — слайд 18 (схема canary). GATE:
verify 0 (после фикса переполнения сл. 15), OOXML PASS, COM 22 PNG, все
просмотрены.
