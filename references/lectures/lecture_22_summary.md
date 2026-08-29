# Лекция 22 — выжимка

**Тема:** CI/CD и GitOps: конвейер, артефакты, push vs pull, Argo CD,
стратегии выкатки, progressive delivery. Переработана из старой 22
(+progressive delivery); старый файл — в `archive_2025/`.

## Ключевые концепции (введены здесь)

- CI / continuous delivery / continuous deployment — степень
  автоматизации после тестов; **DORA**: частота деплоев, lead time,
  доля неудач, MTTR. Частые мелкие деплои безопаснее.
- **Конвейер — код** (.github/workflows): build → тесты → сканы →
  образ → push → deploy; тег = SHA коммита.
- **Артефакты**: неизменяемость (никакой перезаписи тегов),
  прослеживаемость (версия→SHA→PR→автор), один образ на все окружения
  (меняется конфиг, не бинарь).
- **Push vs pull**: push = CI с ключами от прода, сверка только в
  деплой; **GitOps** (pull) = агент в кластере + 4 принципа
  (декларативность, git — истина, непрерывная реконсиляция, изменения
  через git). «kubectl apply из CI ≠ GitOps».
- **Argo CD** (CNCF Graduated, ~60 % кластеров 2026): Application,
  sync/self-heal, OutOfSync; откат = git revert. Flux — те же принципы
  без UI. GitOps решает доставку, не стратегию выкатки.
- Стратегии: rolling / blue-green / canary / feature flags — выбор по
  цене ошибки.
- **Progressive delivery** (Argo Rollouts / Flagger): setWeight → pause
  → analysis (метрики из Prometheus) → автооткат без человека. Ответ на
  крючок CrowdStrike.
- Supply chain кратко: Cosign (подпись), SBOM (опись), OIDC в CI
  (короткие токены) — тизер л. 25.

## Слоты

- **Крючок:** CrowdStrike 19.07.2024 — дефектный контент-файл на весь
  парк без canary, BSOD на 8,5 млн Windows —
  `sources/Веб-находки_Лекция_22.md`; замыкается на слайде progressive
  delivery.
- **Квиз-извлечение:** по л. 21 (state/drift, plan, суперсилы,
  OpenTofu).
- **PI-1:** «CI делает kubectl apply — это GitOps?»; верный B (push:
  нет агента и реконсиляции, ключи у CI); дистракторы: «из git =
  GitOps», «если из main», «нужен Argo CD с UI».
- **Живой сеанс:** путь коммита — mermaid sequence: push → Actions →
  GHCR → PR в infra-репо (единственный человек) → Argo CD pull/sync →
  Rollouts 10→100 %.
- **Мост к лабе 7 (стартует):** стенд кодом + Argo CD + конвейер
  Actions + эксперимент self-heal.

## Примеры «СмартДома»

Workflow telemetry-ci (pytest, образ ghcr.io/smartdom/telemetry:sha),
canary-шаги Rollout телеметрии, два репозитория (код + infra).

## Студенты знают после

CI/CD/CD, DORA, конвейер, артефакт/immutability, push/pull, GitOps-
принципы, Argo CD/Flux, OutOfSync/self-heal, rolling/blue-green/canary/
flags, progressive delivery, Rollouts/Flagger, Cosign/SBOM/OIDC. НЕ
знают ещё: метрики для analysis (л. 24), supply chain подробно (л. 25).

## Презентация

`curriculum/Презентация_22_CI_CD_и_GitOps.pptx`, 24 слайда,
build_pres22.js. PI-разбор A,C,D→B; пауза — слайд 15 (Argo CD «уже
починил»); живой сеанс — слайд 19. GATE: verify 0 (после урезания сл. 9),
OOXML PASS, COM 24 PNG, все просмотрены; находки (переполнение сл. 9,
контраст подписи сл. 19) исправлены.
