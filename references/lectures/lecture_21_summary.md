# Лекция 21 — выжимка

**Тема:** инфраструктура как код: HCL, plan/apply, state и drift, remote
backend, модули, ландшафт Terraform/OpenTofu 2026. Переработана из
старой 21 (+OpenTofu); старый файл — в `archive_2025/`.

## Ключевые концепции (введены здесь)

- **Clickops** («состояние без истории») vs **IaC** («история, из
  которой выводится состояние»); аналогия — чертежи здания. Четыре
  суперсилы текста в git: история, ревью, воспроизводимость, откат.
- **HCL** (общий для Terraform/OpenTofu): блоки terraform (версии, не
  latest) / provider / resource / variable; граф зависимостей. Цикл
  `init → plan (дифф!) → apply`; повторный plan = No changes
  (идемпотентность).
- **State** — третья вершина «код–реальность–реестр»; потеря = амнезия
  (apply создаст дубликаты; лечение — import); руками не править
  (state mv/rm). **Drift**: ручные правки; apply возвращает реальность к
  коду — источник истины всегда код (параллель с reconcile л. 18).
- Команда: remote backend (шифрованный — в state секреты!), locking,
  окружения отдельными каталогами (workspaces — для простых вариаций).
- **Модули**: variables/outputs, версии `?ref=`, validation, README.
- Ландшафт: 08.2023 MPL→BSL → форк **OpenTofu** (LF, CNCF 2025; ~12 %
  практиков, шифрование state); 2025 — IBM купил HashiCorp; общие
  HCL/plan/state. Соседи: Pulumi (языки), Ansible (внутри ОС),
  Crossplane (CRD).
- Секреты (Vault/SOPS/KMS; тизер л. 25) и policy as code (OPA на план =
  guardrails из крючка).

## Слоты

- **Крючок:** AWS S3 28.02.2017 — опечатка в параметре штатной команды,
  ~4 часа, ~$150 млн; ответ Amazon — guardrails в инструменте —
  `sources/Веб-находки_Лекция_21.md`.
- **Квиз-извлечение:** по л. 20 (enforcement политик, Gateway API, меш,
  canary).
- **PI-1:** ночью лимит подняли руками, утром plan+apply; верный B
  (вернёт к коду, правка исчезнет); дистракторы: «не заметит»,
  «обновит код под реальность», «упадёт с конфликтом».
- **Живой сеанс:** main.tf (kubernetes-провайдер: ns + deployment
  телеметрии) → plan/apply → дрейф `kubectl scale --replicas=5` →
  plan «5 → 2» → apply чинит.
- **Мост к лабе 7:** стартует после л. 22; цикл plan→review→apply,
  «менять только через код», заготовка сеанса = первая часть лабы;
  Terraform или OpenTofu на выбор.

## Примеры «СмартДома»

kubernetes_namespace smartdom, deployment телеметрии кодом, модуль
smartdom-app (telemetry_prod, image ghcr.io/smartdom/telemetry:1.2.0).

## Студенты знают после

IaC/clickops, HCL, провайдер, plan/apply, state, drift, backend/lock,
workspaces vs каталоги, модуль, OpenTofu/BSL-история, Pulumi/Ansible/
Crossplane, policy as code. НЕ знают ещё: CI/CD-конвейер и GitOps
(л. 22), секреты подробно (л. 25).

## Презентация

`curriculum/Презентация_21_IaC_и_автоматизация.pptx`, 23 слайда,
build_pres21.js. PI-разбор A,C,D→B; пауза — слайд 14 («Заметил. Записал.
Верну как было»); HCL-код на слайдах 7 и 16. GATE: verify 0, OOXML PASS,
COM 23 PNG, все просмотрены; находка (кавычка ломала JS-строку)
исправлена.
