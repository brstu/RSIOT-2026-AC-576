# QUICK START — ЛР05: kind + kubectl за 30 минут

Чек-лист готовности и первый работающий под. ОС — Windows, команды —
PowerShell.

## 1. Что должно быть установлено

| Инструмент | Проверка | Откуда |
| --- | --- | --- |
| Docker Desktop (из ЛР01) | `docker version` | уже стоит после ЛР01 |
| kubectl | `kubectl version --client` | `winget install Kubernetes.kubectl` |
| kind | `kind version` | `winget install Kubernetes.kind` |

> 💡 Если `winget` недоступен — скачайте бинарники со страниц
> [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/)
> и [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
> и положите в каталог из `PATH`.

## 2. Создать кластер (одна команда)

```powershell
kind create cluster --name smartdom
```

Ожидаемо: через 1–2 минуты — `You can now use your cluster with: kubectl
cluster-info --context kind-smartdom`.

Проверка:

```powershell
kubectl cluster-info
kubectl get nodes
```

Ожидаемо: одна нода `smartdom-control-plane` в статусе `Ready`.

## 3. Первый под — эталонный пример «СмартДома»

```powershell
kubectl apply -f examples/k8s/
kubectl -n smartdom get pods -w
```

Дождитесь `Running` и `READY 1/1` (Ctrl+C — выйти из режима наблюдения).

Проверка сервиса:

```powershell
kubectl -n smartdom port-forward svc/telemetry 8080:80
# в соседнем окне PowerShell:
curl http://localhost:8080/health/ready
```

Ожидаемо: `{"status":"ready"}`. 🎉 Кластер работает — дальше по заданию.

## 4. Частые проблемы

| Симптом | Причина и лечение |
| --- | --- |
| `kind create` висит на `Ensuring node image` | первый запуск тянет образ ноды (~900 MB) — ждите; проверьте интернет |
| Под в `ImagePullBackOff` | образ не загружен в kind: `kind load docker-image <image>:<tag> --name smartdom` |
| Под в `CrashLoopBackOff` | смотрите `kubectl -n smartdom logs <pod>` — чаще всего ошибка старта приложения |
| `port-forward` обрывается | это нормально при пересоздании пода — перезапустите команду |
| Docker Desktop «выключился» после перезагрузки Windows | запустите Docker Desktop и дождитесь зелёного статуса, потом `kind` |

## 5. Снести и пересоздать кластер

```powershell
kind delete cluster --name smartdom
kind create cluster --name smartdom
```

Кластер одноразовый и бесплатный — не бойтесь ломать.
