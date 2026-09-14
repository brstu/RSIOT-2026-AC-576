# Эталонный пример (вариант 0): полный путь коммита «СмартДома»

Стенд кодом + Argo CD + конвейер. Это **вариант 0** — эталон
преподавателя: копировать 1:1 нельзя, параметры вашей сдачи — по
варианту.

## Состав

```text
examples/
├── README.md
├── terraform/
│   └── main.tf            # стенд: namespace + ConfigMap параметров
├── infra/                 # за этим каталогом следит Argo CD
│   ├── deployment.yaml    # telemetry (образ из лабы 5)
│   └── service.yaml
├── argocd/
│   └── application.yaml   # Application с автосинком и self-heal
└── workflows/
    └── ci.yml             # положить в .github/workflows/ своего репо
```

## Порядок применения

```powershell
# 1. Стенд кодом (или tofu вместо terraform):
cd terraform
terraform init
# namespace smartdom уже создан руками в части 1 — заберите его
# под управление кода (заодно потренируете import из лекции 21):
terraform import kubernetes_namespace.stand smartdom
terraform plan     # прочитать дифф!
terraform apply

# 2. Argo CD уже установлен (QUICK_START); подключаем Application:
#    в argocd/application.yaml замените repoURL на ваш fork!
kubectl apply -f ../argocd/application.yaml

# 3. Смотрим UI: приложение smartdom-telemetry → Synced/Healthy
```

## Эксперименты эталона

```powershell
# дрейф IaC: ломаем руками — plan видит, apply возвращает
kubectl -n smartdom delete configmap stand-params
terraform plan     # + create: возвращение ConfigMap
terraform apply

# self-heal GitOps: удаляем Deployment — Argo CD вернёт за секунды
kubectl -n smartdom delete deployment telemetry
kubectl -n smartdom get deploy -w
```

## Про workflow

`workflows/ci.yml` рассчитан на репозиторий студента с каталогами
`app/` (код + Dockerfile из лабы 5) и `infra/`. Он собирает образ с
тегом SHA, публикует в GHCR и коммитит новый тег в
`infra/deployment.yaml` — дальше Argo CD доводит кластер сам. Файл
нужно положить в `.github/workflows/` **вашего** репозитория; прав
стандартного `GITHUB_TOKEN` достаточно (packages: write,
contents: write).
