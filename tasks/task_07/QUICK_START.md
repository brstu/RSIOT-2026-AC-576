# QUICK START — ЛР07: Terraform/OpenTofu + Argo CD за 30–40 минут

Чек-лист готовности и первый автосинк. ОС — Windows, команды —
PowerShell. Окружение лаб 5–6 (Docker Desktop, kubectl, kind) должно
работать.

## 1. Инструмент IaC (один на выбор)

```powershell
winget install Hashicorp.Terraform   # вариант А
winget install OpenTofu.Tofu         # вариант Б (команда tofu вместо terraform)
terraform -version                   # или: tofu -version
```

## 2. Кластер и Argo CD

```powershell
kind create cluster --name smartdom
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl -n argocd get pods -w        # дождаться Running у всех (2–3 минуты)
```

## 3. UI и пароль

```powershell
# пароль администратора (логин admin):
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | %{ [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($_)) }
# проброс UI:
kubectl -n argocd port-forward svc/argocd-server 8443:443
```

Откройте <https://localhost:8443> (предупреждение о сертификате —
ожидаемо: self-signed; вспомните лекцию 17), войдите `admin` / пароль.

## 4. Первый автосинк (эталон)

1. Сделайте fork репозитория курса (или используйте свой рабочий репо).
2. Создайте namespace (позже, в части 2, его возьмёт под управление
   terraform) и примените Application, заменив в
   `examples/argocd/application.yaml` `repoURL` на URL вашего fork:

```powershell
kubectl create namespace smartdom
kubectl apply -f examples/argocd/application.yaml
```

Через ~1 минуту в UI появится приложение `smartdom-telemetry` со
статусом **Synced / Healthy** — Argo CD сам развернул манифесты из
`examples/infra/`. 🎉 Дальше по заданию.

## 5. Частые проблемы

| Симптом | Причина и лечение |
| --- | --- |
| Application в `Unknown` / repo errors | опечатка в repoURL или приватный репозиторий: сделайте fork публичным либо добавьте repo credentials в Argo CD |
| `ComparisonError: path not found` | поле `path` не совпадает с каталогом в репо — проверьте `examples/infra` против вашей структуры |
| Поды infra в `ImagePullBackOff` | образ недоступен: `kind load docker-image …` или опубликуйте в GHCR и сделайте пакет публичным |
| UI не открывается | port-forward упал — перезапустите команду из шага 3 |
| `terraform apply` не видит кластер | kubeconfig: kind пишет контекст `kind-smartdom` — проверьте `kubectl config current-context` |
