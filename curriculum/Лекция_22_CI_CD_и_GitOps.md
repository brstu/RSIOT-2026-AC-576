# Лекция 22. CI/CD и GitOps — непрерывная интеграция, поставка и управление инфраструктурой через Git

## Цель
Понять полный жизненный цикл доставки изменения: от коммита до работающего продакшена. Научиться проектировать надёжные и безопасные пайплайны (build → test → scan → package → deploy), применять стратегии деплоя (blue/green, canary, progressive delivery), внедрять GitOps (Argo CD / Flux) для управляемого и воспроизводимого обновления кластеров. Осознать роль безопасности цепочки поставки (supply chain security: SAST, SBOM, подписи образов) и качественных метрик (lead time, deployment frequency, MTTR, change fail rate — DORA).

## План
1. Термины: CI vs CD vs Continuous Deployment.
2. Стадии пайплайна: fetch → build → test → scan → package → publish → deploy.
3. Артефакты, версии, семантика, build metadata, traceability.
4. Кеши и матричные сборки (parallelism, strategy matrix).
5. Стратегии деплоя: rolling / blue-green / canary / A/B / shadow / feature flags.
6. GitOps принципы: декларативность, единственный источник истины, автоматическая реконсиляция, наблюдаемость.
7. Argo CD и Flux архитектура.
8. Progressive Delivery: измерение метрик во время развёртывания.
9. Supply Chain Security: подпись контейнеров (Cosign), SBOM (Syft), проверки зависимостей (SLSA уровни).
10. Secrets в CI/CD: OIDC, Vault, sealed-secrets.
11. Промоушн окружений dev → stage → prod: gating, approvals, артефакт‑пиннинг.
12. Практическое задание.
13. Вопросы и материалы.

---

## 1. CI vs CD vs Continuous Deployment
| Понятие | Определение |
|---------|-------------|
| CI (Continuous Integration) | Частое объединение кода в main + автоматические тесты и статический анализ |
| CD (Continuous Delivery) | Готовность кода к деплою в любой момент (автоматическая сборка + артефакты + инфраструктура) |
| Continuous Deployment | Автоматический деплой в прод без ручного подтверждения, если проверки прошли |

DORA метрики: Lead Time (время от коммита до прод), Deployment Frequency, Change Fail Rate (% неудачных релизов), MTTR (время восстановления).

## 2. Стадии пайплайна
```plaintext
Commit → Trigger → Checkout → Build → Unit Test → Lint → Security Scan → Package → Integration Test → Publish Artifact → Deploy (Dev) → Promote (Stage) → Canary/Prod
```

### Разделение
- Build: компиляция, сборка Docker image.
- Test: unit/integ/e2e.
- Scan: SAST (код), DAST (динамика), Dependency (CVEs), License check.
- Package: jar, npm package, image.
- Deploy: либо push-инициированный (imperative), либо GitOps (declarative pull).

## 3. Версионирование и артефакты
Используйте SemVer (MAJOR.MINOR.PATCH). Добавляйте build metadata: `1.4.2+sha.c0ffee`.

Артефакт должен быть:
- Immutable (никогда не перезаписывать тот же тег для другого содержимого).
- Traceable: тег → commit SHA → PR → автор.
- Подписанный (Cosign) для доверия.

## 4. Кеши и матрицы
Кеширование зависимостей (npm, Maven, Gradle) уменьшает время билда.
Матрица: сборка и тестирование на нескольких версиях языка / ОС.

GitHub Actions пример матрицы:
```yaml
jobs:
	test:
		runs-on: ubuntu-latest
		strategy:
			matrix:
				node: [18, 20]
		steps:
			- uses: actions/checkout@v4
			- uses: actions/setup-node@v4
				with: { node-version: ${{ matrix.node }} }
			- run: npm ci
			- run: npm test
```

## 5. Стратегии деплоя
| Стратегия | Описание | Плюсы | Минусы |
|-----------|----------|-------|--------|
| Rolling | Постепенная замена подов | Просто | Риск деградации, нет возврата к старому состоянию мгновенно |
| Blue/Green | Два стека: old (blue), new (green); переключение трафика | Быстрый rollback | Двойные ресурсы |
| Canary | Малый % трафика на новую версию → постепенное увеличение | Раннее выявление | Требует маршрутизации и метрик |
| Shadow | Трафик дублируется в новый сервис (не влияет на пользователя) | Безопасно | Сложность, лишние ресурсы |
| Feature Flags | Включение функций на уровне кода | Гибко | Управление состояниями флагов |

## 6. GitOps принципы
1. Декларативная инфраструктура/приложения (манифесты).
2. Git — единственный источник истины.
3. Автоматическая реконсиляция (оператор сравнивает текущее состояние кластера с Git).
4. Наблюдаемость и аудит: все изменения через PR.
5. Rollback — git revert.

Преимущества: согласованность, меньше дрейфа, прозрачность, воспроизводимость.

## 7. Argo CD и Flux
### Argo CD архитектура
```plaintext
Argo CD API Server ← UI/CLI
			 ↓
Repo Server (git clone/cache)
			 ↓
Application Controller → сравнивает желаемое состояние (Git) vs живое (K8s) → sync/health
```
Flux: контроллеры (source-controller, kustomize-controller, helm-controller) следят за Git/OCI источниками и применяют изменения. Оба инструмента реализуют reconciliation loop.

## 8. Progressive Delivery и метрики
Подход: менять трафик постепенно + наблюдать SLI (latency, error rate, saturation). Авто rollback при нарушении SLO.

Argo Rollouts и Flagger (для Flux) интегрируются с Prometheus.
Пример шага canary (встроенные паузы, анализ метрик):
```yaml
strategy:
	canary:
		steps:
			- setWeight: 10
			- pause: { duration: 120 }
			- analysis: { templateName: error-rate-check }
			- setWeight: 50
			- pause: {}
			- setWeight: 100
```

## 9. Supply Chain Security
| Скан | Цель |
|------|------|
| SAST | Анализ исходного кода (инъекции, уязвимости) |
| DAST | Динамическое тестирование работающего приложения |
| Dependency Scan | Проверка библиотек на CVE |
| Container Scan | Уязвимости в базовом образе |
| SBOM (Software Bill of Materials) | Список компонентов для аудита |

Инструменты: Trivy, Syft/Grype, Semgrep, OWASP ZAP, Dependabot.
Подпись образов: Cosign (`cosign sign <image>`). Политики проверки подписи в admission controller (Kyverno/OPA Gatekeeper).
SLSA уровни — гарантия происхождения артефакта (build provenance).

## 10. Секреты в пайплайнах
Не хранить секреты в коде / логах.
Методы:
- GitHub OIDC → выдача временных облачных кредов через провайдера (AWS/GCP/Azure) без статических ключей.
- HashiCorp Vault — получение секретов в рантайме.
- Sealed Secrets (Bitnami) / External Secrets Operator для Kubernetes.
- SOPS (шифрование манифестов).

## 11. Промоушн окружений
Правильный путь: один артефакт → много окружений. Не пересобирать код для prod.
Процесс:
1. Build & Test → Docker image `app:1.2.0+sha.abcd`.
2. Deploy dev (auto).
3. Авто smoke тесты.
4. Manual approval → stage.
5. Нагрузочные тесты / security scans.
6. Canary → prod.

Артефакт‑пиннинг: манифесты prod ссылаются на конкретный тег.

## 12. Пример CI (GitHub Actions расширенный)
```yaml
name: ci
on:
	pull_request:
		branches: [ main ]
	push:
		branches: [ main ]

jobs:
	build-test:
		runs-on: ubuntu-latest
		steps:
			- uses: actions/checkout@v4
			- uses: actions/setup-node@v4
				with: { node-version: '20' }
			- name: Cache deps
				uses: actions/cache@v3
				with:
					path: node_modules
					key: deps-${{ hashFiles('package-lock.json') }}
			- run: npm ci
			- run: npm run lint
			- run: npm test -- --ci
			- name: Build image
				run: docker build -t ghcr.io/${{ github.repository }}:sha-${{ github.sha }} .
			- name: Scan image
				uses: aquasecurity/trivy-action@v0.12.0
				with:
					image-ref: ghcr.io/${{ github.repository }}:sha-${{ github.sha }}
					ignore-unfixed: true
			- name: Login registry
				uses: docker/login-action@v3
				with:
					registry: ghcr.io
					username: ${{ github.actor }}
					password: ${{ secrets.GITHUB_TOKEN }}
			- name: Push image
				run: docker push ghcr.io/${{ github.repository }}:sha-${{ github.sha }}
			- name: Generate SBOM
				run: syft ghcr.io/${{ github.repository }}:sha-${{ github.sha }} -o json > sbom.json
			- name: Upload SBOM artifact
				uses: actions/upload-artifact@v4
				with:
					name: sbom
					path: sbom.json

	deploy-dev:
		needs: [build-test]
		runs-on: ubuntu-latest
		if: github.ref == 'refs/heads/main'
		steps:
			- uses: actions/checkout@v4
			- name: Patch image tag in kustomize overlay
				run: |
					sed -i "s|image: .*|image: ghcr.io/${{ github.repository }}:sha-${{ github.sha }}|" k8s/overlays/dev/deployment.yaml
			- name: Commit manifest change
				run: |
					git config user.name CI
					git config user.email ci@example.local
					git commit -am "Update dev image to sha-${{ github.sha }}" || echo "No changes"
					git push origin main

	report:
		needs: [build-test]
		runs-on: ubuntu-latest
		steps:
			- name: DORA summary (mock)
				run: echo "Lead Time: TBD" >> report.txt
			- uses: actions/upload-artifact@v4
				with: { name: dora, path: report.txt }
```

## 13. Пример GitOps (Argo CD Application)
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
	name: demo-app
	namespace: argocd
spec:
	project: default
	source:
		repoURL: https://github.com/org/repo
		targetRevision: main
		path: k8s/overlays/dev
	destination:
		server: https://kubernetes.default.svc
		namespace: demo
	syncPolicy:
		automated:
			prune: true
			selfHeal: true
		syncOptions:
			- CreateNamespace=true
			- ApplyOutOfSyncOnly=true
```
`prune` удаляет ресурсы, убранные из Git; `selfHeal` пересоздаёт изменённые вручную.

## 14. Canary (Argo Rollouts) пример
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
	name: demo-rollout
spec:
	replicas: 4
	selector:
		matchLabels:
			app: demo
	template:
		metadata:
			labels:
				app: demo
		spec:
			containers:
				- name: app
					image: ghcr.io/org/repo:sha-<commit>
					ports:
						- containerPort: 8080
	strategy:
		canary:
			steps:
				- setWeight: 10
				- pause: { duration: 120 }
				- setWeight: 50
				- pause: {}
				- setWeight: 100
			trafficRouting:
				nginx: { stableIngress: demo-ing }
```

## 15. Rollback и наблюдаемость
Rollback в GitOps = revert коммита → оператор синхронизирует. Для imperative деплоя — храните предыдущий артефакт и манифест.
Метрики: время деплоя, время синхронизации, процент откатов.
Логи контроллеров Argo CD / Flux для диагностики.

## 16. Безопасность пайплайна
- Principle of Least Privilege: токену не нужны лишние разрешения.
- Изоляция: self-hosted runners → обновление, защита от supply chain атак.
- Верификация источников: pin action версии (`@v4`), не использовать `@master`.
- Проверка подписей Git (commit signing), защита main ветки (required PR, статус чеков).

## 17. Практическое задание
Создайте репозиторий с приложением + инфраструктурой:
1. CI: сборка Docker образа, тесты, линтер, скан Trivy, генерация SBOM.
2. Публикация образа в реестр (GHCR) с тегами: `sha-<commit>`, `vX.Y.Z` (на release), `latest` (опционально).
3. GitOps: каталог `k8s/` с base и overlays (`dev`, `stage`, `prod`). Argo CD Application для каждого окружения.
4. Canary деплой через Argo Rollouts или простой blue/green (двойной Deployment + переключение сервисов).
5. Автоматический patch образа для dev окружения в CI; для stage/prod — через отдельный PR и review.
6. Secrets: хотя бы демо использования Sealed Secret или ExternalSecret.
7. Документация: README с описанием пайплайна + rollback процедуры.

Критерии оценки:
- Полнота стадий CI (build/test/scan/publish).
- Наличие артефакт‑трейсабилити (SBOM + ссылка на commit).
- Работа GitOps (авто‑sync + selfHeal).
- Реализована стратегия постепенного деплоя.
- Безопасные практики (pin versions, отсутствие секретов в явном виде).

## 18. Дополнительные ресурсы
- GitHub Actions Docs
- GitLab CI/CD Docs
- Jenkins Declarative Pipeline
- Argo CD / Argo Rollouts Docs
- FluxCD Docs
- Trivy, Syft, Grype (security tooling)
- Cosign (подпись контейнеров)
- Kyverno / OPA Gatekeeper (политики)
- DORA Metrics (google research)
- SLSA.dev (supply chain levels)

## 19. Вопросы для самопроверки
1. В чём отличие Continuous Delivery и Continuous Deployment?
2. Зачем нужен stage между dev и prod?
3. Что такое GitOps reconciliation loop?
4. Как работает canary деплой и когда остановить его?
5. Какие метрики безопасности цепочки поставки вы бы измеряли?
6. Зачем нужен SBOM и как его генерировать?
7. Почему важно подписывать контейнерные образы?
8. Как реализовать rollback в GitOps?
9. Для чего используются workspaces или overlays в манифестах?
10. Что даёт матричная сборка?
11. Чем Argo CD отличается от Flux?
12. Почему нельзя обновлять прод образ без прохождения пайплайна?
13. Какие уязвимости может выявить SAST vs DAST?
14. Что такое selfHeal в Argo CD?
15. Как связаны DORA метрики и качество процесса доставки?

---
**Итог:** CI/CD — фундамент автоматизации поставки ценности, а GitOps переносит эту автоматизацию на управление состоянием инфраструктуры и приложений через Git. Совместно они обеспечивают ускорение релизов, прозрачность, безопасность и надёжность. Умение проектировать эффективный пайплайн и GitOps поток — ключевой навык современного инженера.
