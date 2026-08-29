// Презентация 21 РСиОТ — «Инфраструктура как код (IaC)»
// Стандарт university-teacher: assertion-evidence, палитра «Океан».
// Запуск: node build_pres21.js [выходной_файл.pptx]
const { C, newDeck, darkSlide, lightSlide, chip, arrow, slideQuiz, slideOutcomes, slideRoadmap, slidePI, slidesPIFeedback, slidePause, slideFinal } = require("./deck_common");

const OUT = process.argv[2] || "C:/d/Bstu/repos/RSIOT-2026-AC-576/curriculum/Презентация_21_IaC_и_автоматизация.pptx";
const pres = newDeck();
const M = C.M;

// ---------- 1. Титул ----------
let s = darkSlide(pres, "Распределённые системы и облачные технологии", { y: 1.15, h: 0.9, fontSize: 30 });
s.addText("Лекция 21. Инфраструктура как код — чертежи вместо устных преданий", {
  x: M, y: 2.15, w: 9, h: 0.75, fontFace: C.BODY, fontSize: 19, color: C.CAP_D, margin: 0,
});
s.addText("БрГТУ · АС-576 · 2026 · сквозной пример — IoT-платформа «СмартДом»", {
  x: M, y: 4.7, w: 9, h: 0.4, fontFace: C.BODY, fontSize: 12, color: C.SUB_D, margin: 0,
});
s.addNotes("Титул · ~1 мин · Кластеры из лекций 16–20 кто-то должен создавать — и кликать в консоли перестаёт работать после второго окружения. Первая половина лабы 7. § титул лекции.");

// ---------- 2. Крючок ----------
s = darkSlide(pres, "Одна опечатка в команде — и половина интернета без файлов", { fontSize: 24 });
s.addText("~4 часа", { x: 0.7, y: 1.7, w: 4.2, h: 1.2, fontFace: C.HEAD, fontSize: 50, bold: true, color: C.ACCENT, align: "center", margin: 0 });
s.addText("AWS S3, 28.02.2017: опечатка в параметре штатной\nкоманды вывела огромный пласт серверов;\nGitHub, Trello, Medium — лежат; ущерб ~$150 млн", { x: 0.7, y: 3.0, w: 4.2, h: 1.2, fontFace: C.BODY, fontSize: 13.5, color: C.CAP_D, align: "center", margin: 0 });
s.addText("Опечатка — человеческая\nнеизбежность или\nпроектный дефект?", {
  x: 5.3, y: 2.2, w: 4.0, h: 1.5, fontFace: C.BODY, fontSize: 19, italic: true, color: C.WHITE, margin: 0,
});
s.addNotes("Крючок · ~3 мин · Инженер выводил НЕСКОЛЬКО серверов, опечатка вывела пласт с двумя несущими подсистемами; их не перезапускали годами — холодный старт съел большую часть 4 часов. Ответ Amazon: не уволить, а починить инструмент — guardrails. Ответ пары: убрать руки из консоли, код + план + ревью. § Крючок; sources/Веб-находки_Лекция_21.md");

// ---------- 3. Квиз-извлечение ----------
slideQuiz(pres, "Вспоминаем прошлую пару: сеть и сервис-меш", [
  "1. Почему apply NetworkPolicy ≠ «политика исполняется»?",
  "2. Три ресурса Gateway API — кто каким владеет?",
  "3. Что меш выносит из кода приложения?",
  "4. Canary по весам против RollingUpdate — в чём разница?",
], "Квиз-извлечение · ~5 мин · Молча в конспект, короткий разбор. Ответы в конце лекции. § Квиз-извлечение (лекция 20).");

// ---------- 4. Чему научимся ----------
slideOutcomes(pres, [
  ["Зачем IaC", "история, ревью, откат"],
  ["HCL", "провайдеры, ресурсы, переменные"],
  ["plan → apply", "дифф до катастрофы"],
  ["State и drift", "реестр и цена ручных правок"],
  ["Команда", "remote state, lock, окружения"],
  ["Ландшафт 2026", "Terraform · OpenTofu · Pulumi"],
], "Результаты обучения · ~2 мин · Шесть плиток; вместе со следующей парой (CI/CD+GitOps) — фундамент лабы 7. § Результаты обучения.");

// ---------- 5. Дорожная карта ----------
slideRoadmap(pres, "Маршрут: от кликов и Витиной памяти — к чертежам", [
  "Зачем\nIaC", "HCL +\nplan/apply", "State\nи дрейф", "Команда\nи модули", "Ландшафт +\nживой сеанс",
], "Дорожная карта · ~1 мин · Clickops: «галочку важную ставили, какую — Витя знал, а он уволился». IaC = чертежи здания: правишь чертёж, не стену. Декларативность знакома с л. 18. § Картина мира.");

// ---------- 6. Зачем IaC ----------
s = lightSlide(pres, "Текст в git даёт инфраструктуре четыре суперсилы");
const powers = [
  ["История", "git log вместо «Витя помнил»"],
  ["Ревью", "второй глаз между опечаткой и катастрофой"],
  ["Воспроизводимость", "dev/stage/prod из одних файлов"],
  ["Откат", "git revert + apply вместо археологии"],
];
powers.forEach((p, i) => {
  const x = M + (i % 2) * 4.6, y = 1.5 + Math.floor(i / 2) * 1.5;
  chip(s, x, y, 4.4, 1.3, [
    { text: p[0] + "\n", options: { bold: true, fontSize: 16, color: C.DEEP } },
    { text: p[1], options: { fontSize: 13, color: C.TXT_MUT } },
  ], { align: "left" });
});
s.addText("clickops — состояние без истории; IaC — история, из которой выводится состояние", { x: M, y: 4.6, w: 9, h: 0.4, fontFace: C.BODY, fontSize: 13.5, italic: true, color: C.TXT_MUT, align: "center", margin: 0 });
s.addNotes("§ Ядро-1 · ~4 мин · Связка с крючком: план изменений показал бы «−пласт серверов» ДО Enter. Формулу внизу — прожать. § Зачем IaC.");

// ---------- 7. HCL ----------
s = lightSlide(pres, "HCL: описываем желаемое — и три команды цикла");
s.addText([
  { text: 'resource "kubernetes_namespace" "smartdom" {\n  metadata {\n    name = "smartdom"\n  }\n}\n\nvariable "replicas" {\n  type    = number\n  default = 2\n}', options: {} },
], { x: M, y: 1.45, w: 5.4, h: 3.0, fontFace: "Consolas", fontSize: 13, color: C.INK, fill: { color: C.PANEL }, line: { color: C.LINEC }, margin: 0.12, valign: "top" });
const cycle = [["init", "скачать провайдеры"], ["plan", "ДИФФ: что изменится"], ["apply", "применить"]];
cycle.forEach((p, i) => {
  chip(s, 6.2, 1.55 + i * 1.0, 3.2, 0.85, [
    { text: p[0] + "  ", options: { bold: true, fontSize: 16, color: C.DEEP } },
    { text: "· " + p[1], options: { fontSize: 12, color: C.TXT_MUT } },
  ], { align: "left" });
});
s.addText("plan на неизменном коде = No changes — идемпотентность встроена в цикл", { x: M, y: 4.65, w: 9, h: 0.4, fontFace: C.BODY, fontSize: 13.5, italic: true, color: C.TXT_MUT, align: "center", margin: 0 });
s.addNotes("§ Ядро-2 · ~5 мин · Блоки terraform (версии — никаких latest), provider, resource, variable; граф зависимостей строится сам. Terraform и OpenTofu говорят на одном HCL. § HCL и цикл plan → apply.");

// ---------- 8. State ----------
s = lightSlide(pres, "State — третья вершина: код, реальность и реестр между ними");
chip(s, 0.9, 1.5, 2.5, 1.05, "КОД\nкак должно быть", { fs: 13, bold: true });
chip(s, 6.7, 1.5, 2.5, 1.05, "РЕАЛЬНОСТЬ\nкак есть", { fs: 13, bold: true });
chip(s, 3.8, 2.9, 2.5, 1.05, "STATE\nчто из реальности —\nнаше", { fs: 12, bold: true, fill: C.DEEP, color: C.WHITE, line: C.DEEP });
arrow(s, 3.5, 1.95, 3.1);
chip(s, M, 4.2, 9, 0.85, "потеря state = амнезия (apply создаст дубликаты) · дрейф = ручные правки;\napply вернёт реальность к коду — источник истины всегда код", { fs: 13 });
s.addNotes("§ Ядро-3 · ~5 мин · Plan сравнивает три вершины и печатает дифф. State не удалять, руками не править (state mv/rm, import). Параллель: «kubectl edit сотрёт reconcile» из л. 18. Сейчас голосуем. § State: реестр.");

// ---------- 9. PI ----------
slidePI(pres, "Голосуем: ночью лимит памяти подняли руками; утром plan + apply без правок кода", [
  "A. Ничего: Terraform не заметит ручное изменение",
  "B. Terraform вернёт лимит к значению из кода — ночная правка исчезнет",
  "C. Terraform обновит код и state под новое значение — правка сохранится",
  "D. Apply упадёт с конфликтом — чинить state руками",
], "Peer instruction · ~6 мин · Голос → 90 сек спора → голос. Подсказка после первого голоса: где источник истины и что вы знаете про «правки мимо git» из л. 18? § PI-1.");

// ---------- 10-13. PI разборы ----------
slidesPIFeedback(pres, [
  ["A — мимо: plan сверяет реальность при каждом запуске", "Refresh считывает фактическое состояние ресурсов —\nручное изменение Terraform прекрасно видит.", false],
  ["C — мимо: направление всегда код → реальность", "Terraform никогда не «подгоняет код под реальность»:\nобновится только снимок фактов в state, план вернёт код.", false],
  ["D — мимо: дрейф — штатная ситуация, не конфликт", "Plan его показывает, apply устраняет.\nЧинить state руками не нужно (и вообще не нужно).", false],
  ["B — да: источник истины — код", "Ночная правка исчезнет при первом же apply — может, через неделю,\nкогда о ней все забыли. Горячий фикс обязан немедленно попасть в код.", true],
]);

// ---------- 14. Пауза ----------
slidePause(pres, [
  "Дежурный: «Я же только чуть-чуть подкрутил руками, никто не заметит…»",
  "terraform plan: «Заметил. Записал. Верну как было.»",
], "дрейф не прощает — и это лучшее его свойство", "Слайд-пауза · 30–60 сек · Выдохнули. Прочитать как встречу в коридоре. Связка: «а теперь — как жить с этим в команде» — едем к remote state. § граница блоков, ~45-я минута.");

// ---------- 15. Команда ----------
s = lightSlide(pres, "Команде нужны: удалённый state, замок и раздельные окружения");
const team = [
  ["Remote backend", "state в шифрованном бакете, не в git: там секреты"],
  ["Locking", "два инженера не сделают apply одновременно"],
  ["Окружения", "dev/stage/prod — отдельные каталоги и state"],
];
team.forEach((p, i) => {
  chip(s, M, 1.5 + i * 1.0, 9, 0.85, [
    { text: p[0] + "  ", options: { bold: true, fontSize: 15, color: C.DEEP } },
    { text: "· " + p[1], options: { fontSize: 12.5, color: C.TXT_MUT } },
  ], { align: "left" });
});
s.addText("workspaces — для простых вариаций; явные каталоги читаются лучше и ломаются реже", { x: M, y: 4.55, w: 9, h: 0.4, fontFace: C.BODY, fontSize: 13.5, italic: true, color: C.TXT_MUT, align: "center", margin: 0 });
s.addNotes("§ Ядро-4 · ~4 мин · «State на ноутбуке» заканчивается с приходом второго инженера. Один state на все окружения = опечатка в dev сносит prod. § Удалённый state, блокировка, окружения.");

// ---------- 16. Модули ----------
s = lightSlide(pres, "Модуль — функция для инфраструктуры: интерфейс важнее нутра");
s.addText([
  { text: 'module "telemetry_prod" {\n  source   = "./modules/smartdom-app"\n  name     = "telemetry"\n  image    = "ghcr.io/smartdom/telemetry:1.2.0"\n  replicas = 3\n}', options: {} },
], { x: M, y: 1.5, w: 5.6, h: 2.2, fontFace: "Consolas", fontSize: 13, color: C.INK, fill: { color: C.PANEL }, line: { color: C.LINEC }, margin: 0.12, valign: "top" });
const modr = [["variables → outputs", "чистый интерфейс"], ["версии ?ref=v1.2.3", "никаких latest"], ["validation + README", "входы проверены, пример есть"]];
modr.forEach((p, i) => {
  chip(s, 6.4, 1.5 + i * 1.0, 3.0, 0.85, [
    { text: p[0] + "\n", options: { bold: true, fontSize: 12.5, color: C.DEEP } },
    { text: p[1], options: { fontSize: 11, color: C.TXT_MUT } },
  ], { align: "left" });
});
s.addNotes("§ Ядро-5 · ~3 мин · Три окружения ≠ трижды скопированный код: один модуль — три вызова с параметрами. Минимум обязательных переменных. § Модули.");

// ---------- 17. Ландшафт ----------
s = lightSlide(pres, "2023: смена лицензии → форк. 2026: один язык — два инструмента");
chip(s, M, 1.45, 4.3, 2.55, "Terraform\n\n· HashiCorp (с 2025 — IBM), BSL\n· крупнейшая доля рынка\n· канон документации и модулей", { fs: 13, align: "left" });
chip(s, 5.15, 1.45, 4.15, 2.55, "OpenTofu\n\n· форк 2023, Linux Foundation/CNCF\n· ~12 % практиков и растёт\n· шифрование state, for_each\n  для провайдеров", { fs: 13, align: "left", fill: C.DEEP, color: C.WHITE, line: C.DEEP });
s.addText("общие HCL, plan/apply, state — выучили одно, умеете оба · соседи: Pulumi (код), Ansible (внутри ОС), Crossplane (CRD)", { x: M, y: 4.3, w: 9, h: 0.55, fontFace: C.BODY, fontSize: 12.5, italic: true, color: C.TXT_MUT, align: "center", margin: 0 });
s.addNotes("§ Ядро-6 · ~4 мин · История: 08.2023 MPL→BSL, сообщество форкнуло 1.5 → OpenTofu; 2025 IBM купила HashiCorp; Fidelity мигрировала 50 тыс. state. В лабе 7 — любой из двух. § Ландшафт 2026.");

// ---------- 18. Живой сеанс ----------
s = lightSlide(pres, "Живой сеанс: «СмартДом» кодом — и лечение дрейфа");
const ls21 = [["main.tf\nns + deploy", ""], ["plan\n«+2 ресурса»", ""], ["apply\n→ кластер", ""], ["руками\nscale 5", ""], ["plan: 5 → 2\napply чинит", ""]];
ls21.forEach((p, i) => {
  chip(s, M + i * 1.92, 1.7, 1.6, 1.1, p[0], { fs: 12, bold: true }, );
  if (i < ls21.length - 1) arrow(s, M + i * 1.92 + 1.62, 2.1, 0.28);
});
chip(s, M, 3.2, 9, 1.0, "те же манифесты лабы 5 — но с историей, ревью и переменными;\nповторный plan без правок = No changes (идемпотентность)", { fs: 13.5 });
s.addText("мораль: реальность подчиняется коду, а не наоборот — и это исполняется автоматически", { x: M, y: 4.5, w: 9, h: 0.4, fontFace: C.BODY, fontSize: 13, italic: true, color: C.ACCENT, align: "center", margin: 0 });
s.addNotes("Живой сеанс · ~8 мин · Писать main.tf на глазах (kubernetes-провайдер), цикл init/plan/apply, затем устроить дрейф kubectl scale --replicas=5 и показать план «5 -> 2». Полный код — в лекции. § Живой сеанс.");

// ---------- 19. Секреты и политики ----------
s = lightSlide(pres, "Два взрослых вопроса: секреты не в коде, политика — на план");
chip(s, M, 1.5, 4.3, 2.5, "Секреты\n\n· не в .tf и не в git\n· ВНИМАНИЕ: state тоже их содержит\n  → шифрованный backend\n· источники: Vault, SOPS, KMS\n  (подробно — лекция 25)", { fs: 12.5, align: "left" });
chip(s, 5.15, 1.5, 4.15, 2.5, "Policy as code\n\n· план — это данные: проверяем\n  автоматикой до apply (OPA)\n· «бакеты не публичные»,\n  «prod только из main»\n· те же guardrails, что у Amazon\n  после крючка", { fs: 12.5, align: "left" });
s.addNotes("§ Ядро-7 · ~3 мин · Сгенерированный пароль БД окажется в state открытым текстом — поэтому backend шифруют. Policy as code замыкает крючок: guardrails как часть конвейера. § Секреты и политики.");

// ---------- 20. Типичные ошибки ----------
s = lightSlide(pres, "Пять привычек, за которые платят простоем");
const errs21 = [
  "гибрид «код + руки»  →  plan врёт, apply сносит чужое",
  "state в git / на ноутбуке  →  гонки, потери, секреты наружу",
  "apply без чтения plan  →  «-destroy 47 resources» узнаете постфактум",
  "один state на все окружения  →  опечатка в dev сносит prod",
  "секрет в коде «временно»  →  git помнит вечно; ротация дешевле чистки истории",
];
errs21.forEach((t, i) => chip(s, M, 1.45 + i * 0.78, 9, 0.66, t, { align: "left", fs: 13.5 }));
s.addNotes("Типичные ошибки · ~3 мин · Все пять уже звучали — закрепление узнаванием; зал называет опровергающий раздел. § Типичные ошибки.");

// ---------- 21. Квиз-закрепление ----------
slideQuiz(pres, "Закрепление: четыре вопроса по сегодняшней паре", [
  "1. Четыре суперсилы инфраструктуры-как-текста?",
  "2. Что такое state и почему его потеря — амнезия?",
  "3. Цикл plan → apply: почему plan обязателен к чтению?",
  "4. Что случилось в августе 2023 и что общего у Terraform и OpenTofu?",
], "Квиз-закрепление · ~5 мин · Молча в конспект, сверка с соседом, разбор. Ответы в конце лекции. § Квиз-закрепление.");

// ---------- 22. Мост к лабе ----------
s = lightSlide(pres, "Лаба 7 ждёт вторую половину: завтра — CI/CD и GitOps");
chip(s, M, 1.55, 4.3, 2.9, "В лабу 7 из этой пары:\n\n· цикл plan → review → apply\n· дисциплина «менять только\n  через код»\n· заготовка сеанса: namespace +\n  deployment кодом — первая\n  часть лабы\n· Terraform или OpenTofu — на выбор", { align: "left", fs: 12.5 });
chip(s, 5.15, 1.55, 4.15, 2.9, "Домашка на одно предложение:\n\n«Правило „менять инфраструктуру\nтолько через код“ пригодится\nлично мне, потому что…»\n\nБез общих слов. Спрошу троих.", { align: "left", fs: 13, fill: C.DEEP, color: C.WHITE, line: C.DEEP });
s.addNotes("Мост к лабе · ~2 мин · Лаба 7 стартует после лекции 22 (CI/CD + GitOps): опишете стенд кодом, Argo CD покатит приложение из git. Домашка — utility-value, трое зачитают. § Мост к лабораторной № 7.");

// ---------- 23. Финал ----------
slideFinal(pres,
  "Почитать: developer.hashicorp.com/terraform  ·  opentofu.org  ·  Brikman, «Terraform: Up & Running»",
  "Полный текст лекции, квизы, ответы и источники крючка — в репозитории курса",
  "Финал · ~2 мин · Вопросы. Напомнить домашку. Следующая пара — CI/CD и GitOps: робот, который катит за вас. § Список литературы.");

pres.writeFile({ fileName: OUT }).then((f) => console.log("written:", f));
