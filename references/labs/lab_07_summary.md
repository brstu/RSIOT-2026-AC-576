# Лаба 07 — выжимка

**Тема:** IaC + CI/CD GitOps (`tasks/task_07`, написана с нуля).
Лекции-основы: 21 (IaC), 22 (CI/CD и GitOps). Сквозная цель: полный
путь коммита «СмартДома» без ручных шагов.

## Состав

- `readme.md` — README с метками, 4 части, критерии/бонусы, правила ИИ
  и пересдачи 85 %, 10 контрольных вопросов. Оговорка: вместо двух
  репозиториев (лекция 22) допускается один с каталогами `app/` и
  `infra/` (GITHUB_TOKEN хватает без PAT).
- `QUICK_START.md` — установка Terraform/OpenTofu (winget), Argo CD в
  kind (официальный манифест), пароль/UI через port-forward, первый
  автосинк; таблица частых проблем.
- `Макет_отчета.md` — титул 2026, таблица критериев = README, разделы
  «Зачем в реальных системах» и «Использование ИИ».
- `Варианты.md` — 45 вариантов: tool (terraform/opentofu чередуются),
  app (telemetry/alerts/devices/readings/rules), ns gitopsNN, port,
  replicas.
- `examples/` — вариант 0: `terraform/main.tf` (kubernetes-провайдер:
  namespace + ConfigMap stand-params; в README — упражнение
  `terraform import` намespace из части 1), `infra/`
  (deployment telemetry с envFrom optional + service),
  `argocd/application.yaml` (automated + prune + selfHeal,
  CreateNamespace=false), `workflows/ci.yml` (тесты → образ:SHA в GHCR →
  sed-бамп тега в infra → commit ботом; permissions contents+packages).

## Задание (4 части)

1. Быстрый первый успех (30–40 мин): Argo CD + эталонный Application
   → Synced/Healthy.
2. Стенд кодом: HCL по варианту, plan/apply, повторный plan =
   No changes, эксперимент «дрейф».
3. Application с selfHeal: эксперименты «удалили руками — вернулось» и
   «git revert откатывает релиз».
4. Конвейер: полный путь коммита без ручного kubectl (цепочка
   скриншотов).

## Оценивание

Критерии 100: стенд 20, Argo CD+Application 20, конвейер 25, полный
путь 15, эксперименты 10, метаданные 5, документация 5. Бонусы 15:
Argo Rollouts canary +6, policy as code +3, отдельный infra-репо +3,
state-дисциплина +3. Пересдача 85 %; защита по своему коду; сдача
PR + 2 ревью, `students/<NameLatin>/task_07/{doc,src}` + ссылка на
рабочий репозиторий.

## GATE и находки

markdownlint 0; все YAML примера валидны (yaml.safe_load_all).
Исправлено адверсариальным проходом: порядок частей ломал эталон
(Application до terraform) → namespace создаётся в QUICK_START и
импортируется в state в части 2; envFrom stand-params сделан optional.

## Связи

Мосты лекций 20–22 ведут сюда; canary из л. 20/22 — бонус Rollouts.
Следующая лаба курса — 8 (наблюдаемость, блок D, не наш блок).
