// Презентация 18 РСиОТ — «Kubernetes: основы»
// Стандарт university-teacher: assertion-evidence, палитра «Океан».
// Запуск: node build_pres18.js [выходной_файл.pptx]
const { C, newDeck, darkSlide, lightSlide, chip, arrow, slideQuiz, slideOutcomes, slideRoadmap, slidePI, slidesPIFeedback, slidePause, slideFinal } = require("./deck_common");

const OUT = process.argv[2] || "C:/d/Bstu/repos/RSIOT-2026-AC-576/curriculum/Презентация_18_Kubernetes_основы.pptx";
const pres = newDeck();
const M = C.M;

// ---------- 1. Титул ----------
let s = darkSlide(pres, "Распределённые системы и облачные технологии", { y: 1.15, h: 0.9, fontSize: 30 });
s.addText("Лекция 18. Kubernetes — или кто перезапустит контейнер в три часа ночи", {
  x: M, y: 2.15, w: 9, h: 0.75, fontFace: C.BODY, fontSize: 19, color: C.CAP_D, margin: 0,
});
s.addText("БрГТУ · АС-576 · 2026 · сквозной пример — IoT-платформа «СмартДом»", {
  x: M, y: 4.7, w: 9, h: 0.4, fontFace: C.BODY, fontSize: 12, color: C.SUB_D, margin: 0,
});
s.addNotes("Титул · ~1 мин · Контейнеры упакованы в лабе 1 — теперь кто-то должен их перезапускать, обновлять и балансировать. Третий кит лабы 5. § титул лекции.");

// ---------- 2. Крючок ----------
s = darkSlide(pres, "Сборщик метрик уложил ChatGPT на четыре часа", { fontSize: 25 });
s.addText("4 часа", { x: 0.7, y: 1.7, w: 4.2, h: 1.2, fontFace: C.HEAD, fontSize: 54, bold: true, color: C.ACCENT, align: "center", margin: 0 });
s.addText("11.12.2024: телеметрия завалила kube-apiserver\nвсех кластеров OpenAI; DNS-кэш 20 минут\nмаскировал катастрофу", { x: 0.7, y: 3.05, w: 4.2, h: 1.2, fontFace: C.BODY, fontSize: 14, color: C.CAP_D, align: "center", margin: 0 });
s.addText("Как «безобидные метрики» убили\nсистему, спроектированную\nпереживать смерть серверов?", {
  x: 5.3, y: 2.2, w: 4.0, h: 1.5, fontFace: C.BODY, fontSize: 19, italic: true, color: C.WHITE, margin: 0,
});
s.addNotes("Крючок · ~3 мин · Рассказать: деплой телеметрии за 30 мин на все кластеры; стейджинг не поймал (кластеры маленькие, цена запросов росла с размером); control plane умер, поды жили, пока не протух DNS; откат — через мёртвый apiserver. Разобрать по винтикам сможем к слайду 8. § Крючок; sources/Веб-находки_Лекция_18.md");

// ---------- 3. Квиз-извлечение ----------
slideQuiz(pres, "Вспоминаем прошлую пару: сетевые основы", [
  "1. Почему смена DNS-записи не мгновенна и что делать при переезде?",
  "2. L4 против L7 — в чём разница?",
  "3. Что проверяет клиент в TLS-рукопожатии?",
  "4. За счёт чего HTTP/3 быстрее на сети с потерями?",
], "Квиз-извлечение · ~5 мин · Молча в конспект, короткий устный разбор. Вопросы 1–2 сегодня вернутся: Service = L4, дискавери = DNS. Ответы в конце лекции. § Квиз-извлечение (лекция 17).");

// ---------- 4. Чему научимся ----------
slideOutcomes(pres, [
  ["Зачем оркестратор", "и чего K8s не делает"],
  ["Архитектура", "control plane и ноды"],
  ["Матрёшка", "Pod → ReplicaSet → Deployment"],
  ["Service / Ingress", "публикация сервиса"],
  ["Пробы и ресурсы", "без рестарт-штормов"],
  ["Rollout", "обновление и откат"],
], "Результаты обучения · ~2 мин · Шесть плиток. После пары стартует лаба 5 — всё из списка понадобится руками. § Результаты обучения.");

// ---------- 5. Дорожная карта ----------
slideRoadmap(pres, "Маршрут: от зоопарка серверов к декларативному кластеру", [
  "Зачем +\nreconcile", "Архитектура\nкластера", "Deployment\nService", "Пробы\nресурсы", "Живой сеанс\n+ rollout",
], "Дорожная карта · ~1 мин · Открыть болью: 5 серверов, адреса в LB руками, сервер умер ночью — телефон. K8s автоматизирует ровно эту рутину. § Картина мира.");

// ---------- 6. Зачем оркестратор ----------
s = lightSlide(pres, "Оркестратор забирает четыре ночные обязанности");
const duties = [
  ["Размещает", "поды по нодам с учётом ресурсов"],
  ["Лечит", "перезапуск упавших, переезд с мёртвых нод"],
  ["Масштабирует", "больше нагрузки — больше реплик"],
  ["Обновляет", "без даунтайма, с откатом"],
];
duties.forEach((p, i) => {
  const x = M + (i % 2) * 4.6, y = 1.5 + Math.floor(i / 2) * 1.5;
  chip(s, x, y, 4.4, 1.3, [
    { text: p[0] + "\n", options: { bold: true, fontSize: 16, color: C.DEEP } },
    { text: p[1], options: { fontSize: 13, color: C.TXT_MUT } },
  ], { align: "left" });
});
s.addText("не делает: сборку образов (CI), мониторинг из коробки, базу данных — это конструктор, не готовая платформа", { x: M, y: 4.6, w: 9, h: 0.4, fontFace: C.BODY, fontSize: 13, italic: true, color: C.TXT_MUT, align: "center", margin: 0 });
s.addNotes("§ Ядро-1 · ~4 мин · Пройти четыре обязанности на «зоопарке» из вступления. Честность: K8s — не бесплатная надёжность, внутри etcd тот самый Raft (лекция 7), а крючок показал, как умирает перегруженный control plane. § Зачем оркестратор.");

// ---------- 7. Reconcile ----------
s = lightSlide(pres, "Kubernetes — термостат, а не сценарий");
chip(s, M, 1.5, 4.3, 2.5, "Императивно (сценарий)\n\n«сделай A, потом B, потом C»\n\nшаг B упал ночью —\nсценарий мёртв, вы разбужены", { fs: 14, align: "left" });
chip(s, 5.15, 1.5, 4.15, 2.5, "Декларативно (термостат)\n\n«должно быть 22°»\n\nцикл: желаемое → реальное →\nмаленький шаг к цели", { fs: 14, align: "left", fill: C.DEEP, color: C.WHITE, line: C.DEEP });
s.addText("сбой — не событие для обработки, а очередное расхождение; источник истины — манифест, не руки", { x: M, y: 4.35, w: 9, h: 0.4, fontFace: C.BODY, fontSize: 13.5, italic: true, color: C.TXT_MUT, align: "center", margin: 0 });
s.addNotes("§ Ядро-2 · ~4 мин · Reconcile loop: читать желаемое из API → сверить с реальностью → шаг. Убитый вручную под контроллер вернёт через секунды — антипаттерн № 5 курса «правки мимо git». § Декларативность и reconcile loop.");

// ---------- 8. Архитектура ----------
s = lightSlide(pres, "Мозг и мышцы: apiserver — единственная дверь");
s.addText("Control plane", { x: M, y: 1.4, w: 4.3, h: 0.35, fontFace: C.BODY, fontSize: 14, bold: true, color: C.INK, margin: 0 });
const cp = [["kube-apiserver", "дверь: всё через него"], ["etcd", "состояние; Raft (л. 7)"], ["scheduler", "куда ставить поды"], ["controller-manager", "пачка reconcile-циклов"]];
cp.forEach((p, i) => {
  chip(s, M, 1.8 + i * 0.78, 4.3, 0.66, [
    { text: p[0] + "  ", options: { bold: true, fontSize: 13, color: C.DEEP } },
    { text: "· " + p[1], options: { fontSize: 11.5, color: C.TXT_MUT } },
  ], { align: "left" });
});
s.addText("Нода (×N)", { x: 5.15, y: 1.4, w: 4.15, h: 0.35, fontFace: C.BODY, fontSize: 14, bold: true, color: C.INK, margin: 0 });
const nd = [["kubelet", "запускает поды, гоняет пробы"], ["kube-proxy", "правила Service (L4)"], ["runtime", "containerd — Docker не нужен"]];
nd.forEach((p, i) => {
  chip(s, 5.15, 1.8 + i * 0.78, 4.15, 0.66, [
    { text: p[0] + "  ", options: { bold: true, fontSize: 13, color: C.DEEP } },
    { text: "· " + p[1], options: { fontSize: 11.5, color: C.TXT_MUT } },
  ], { align: "left" });
});
chip(s, 5.15, 4.14, 4.15, 0.75, "OpenAI: дверь заперта → менять и чинить нечем; поды жили, пока не протух DNS", { fs: 12, fill: C.PANEL, align: "left" });
s.addNotes("§ Ядро-3 · ~6 мин · Пройти компоненты; kubelet автономен — поэтому пользователи OpenAI заметили не сразу, DNS-кэш добавил 20 минут иллюзии. Урок: data plane переживает смерть мозга, но недолго. Версии: 3 релиза/год, актуальны 1.34–1.36. § Архитектура: мозг и мышцы.");

// ---------- 9. Матрёшка ----------
s = lightSlide(pres, "Под смертен — поэтому им управляет матрёшка контроллеров");
chip(s, M, 2.0, 2.9, 1.6, "Deployment\nверсии, раскатки,\nоткаты", { fs: 14, bold: true });
arrow(s, 3.5, 2.65, 0.4);
chip(s, 4.0, 2.0, 2.9, 1.6, "ReplicaSet\n«держи N подов\nживыми»", { fs: 14, bold: true });
arrow(s, 7.0, 2.65, 0.4);
chip(s, 7.5, 2.0, 2.0, 1.6, "Pod ×N\nэфемерный IP", { fs: 14, bold: true, fill: C.DEEP, color: C.WHITE, line: C.DEEP });
s.addText("новая версия = новый ReplicaSet; Deployment переливает реплики постепенно", { x: M, y: 4.0, w: 9, h: 0.4, fontFace: C.BODY, fontSize: 14, italic: true, color: C.TXT_MUT, align: "center", margin: 0 });
s.addNotes("§ Ядро-4 · ~3 мин · Поды напрямую не создают: они смертны, и это норма. Матрёшка нужна для обновлений и откатов. § Матрёшка: Pod → ReplicaSet → Deployment.");

// ---------- 10. Манифест ----------
s = lightSlide(pres, "Весь деплой телеметрии — неполных двадцать строк YAML");
s.addText([
  { text: "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: telemetry\n  namespace: smartdom\nspec:\n  replicas: 3\n  selector:\n    matchLabels: { app: telemetry }\n  template:\n    metadata:\n      labels: { app: telemetry }\n    spec:\n      containers:\n        - name: api\n          image: ghcr.io/smartdom/telemetry:1.2.0", options: {} },
], { x: M, y: 1.45, w: 5.6, h: 3.7, fontFace: "Consolas", fontSize: 12.5, color: C.INK, fill: { color: C.PANEL }, line: { color: C.LINEC }, margin: 0.12, valign: "top" });
const yamlNotes = [
  ["selector = labels", "иначе ReplicaSet «не видит» поды"],
  ["replicas: 3", "желаемое, не команда"],
  ["тег версии", "никогда :latest в проде"],
];
yamlNotes.forEach((p, i) => {
  chip(s, 6.4, 1.6 + i * 1.15, 2.95, 0.95, [
    { text: p[0] + "\n", options: { bold: true, fontSize: 13, color: C.DEEP } },
    { text: p[1], options: { fontSize: 11, color: C.TXT_MUT } },
  ], { align: "left" });
});
s.addNotes("§ Ядро-4, манифест · ~4 мин · Пройти поля; kubectl apply -f; проверка get deploy,rs,pods. Ошибки: ImagePullBackOff (опечатка в образе), CrashLoopBackOff (падает на старте — kubectl logs). Namespace — папка-изолятор. § Первый манифест.");

// ---------- 11. Service ----------
s = lightSlide(pres, "Service — вчерашний L4-балансировщик, но автоматический");
chip(s, M, 1.5, 4.3, 2.6, "У подов эфемерные IP —\nумирают вместе с подом\n\nService даёт группе подов\n(по меткам) стабильное имя,\nVIP и DNS-запись:\ntelemetry.smartdom.svc.cluster.local", { fs: 13, align: "left" });
const svcT = [["ClusterIP", "изнутри кластера (по умолчанию)"], ["NodePort", "порт на каждой ноде — стенды"], ["LoadBalancer", "внешний L4 от облака"]];
svcT.forEach((p, i) => {
  chip(s, 5.15, 1.5 + i * 0.92, 4.15, 0.78, [
    { text: p[0] + "  ", options: { bold: true, fontSize: 14, color: C.DEEP } },
    { text: "· " + p[1], options: { fontSize: 11.5, color: C.TXT_MUT } },
  ], { align: "left" });
});
s.addText("kubectl get endpoints telemetry — пусто? селектор не совпал или нет готовых подов", { x: M, y: 4.45, w: 9, h: 0.4, fontFace: C.BODY, fontSize: 13.5, italic: true, color: C.TXT_MUT, align: "center", margin: 0 });
s.addNotes("§ Ядро-5 · ~4 мин · Ровно L4 + DNS-дискавери из лекции 17, только автоматически: CoreDNS создаёт записи, kube-proxy — правила. Endpoints наполняются только готовыми (readiness!) подами. § Service.");

// ---------- 12. Ingress ----------
s = lightSlide(pres, "Ingress — вчерашний L7: правила отдельно, исполнитель отдельно");
chip(s, M, 1.6, 2.8, 1.1, "Ingress\nправила: хост/путь →\nService", { fs: 13, bold: true });
arrow(s, 3.4, 2.0, 0.5);
chip(s, 4.0, 1.6, 2.8, 1.1, "Ingress Controller\ningress-nginx —\nставится отдельно", { fs: 13, bold: true });
arrow(s, 6.9, 2.0, 0.5);
chip(s, 7.5, 1.6, 2.0, 1.1, "Service →\nподы", { fs: 13, bold: true });
chip(s, M, 3.2, 9, 0.95, "api.smartdom.local/telemetry → Service telemetry:80\nбез установленного контроллера правила Ingress — просто записи в etcd", { fs: 13.5 });
s.addText("наследник — Gateway API: подробнее в лекции 20", { x: M, y: 4.45, w: 9, h: 0.4, fontFace: C.BODY, fontSize: 13.5, italic: true, color: C.TXT_MUT, align: "center", margin: 0 });
s.addNotes("§ Ядро-5, Ingress · ~3 мин · L7-маршрутизация из лекции 17 в кластере. Типичная ошибка: Ingress создан, контроллер не установлен; забытый hosts/DNS. § Ingress.");

// ---------- 13. ConfigMap/Secret ----------
s = lightSlide(pres, "Один образ — все окружения: конфигурация живёт отдельно");
chip(s, M, 1.5, 4.3, 2.4, "ConfigMap\n\nнастройки:\nALERT_THRESHOLD_C: \"60\"\n\nв env или файлом в под", { fs: 13.5, align: "left" });
chip(s, 5.15, 1.5, 4.15, 2.4, "Secret\n\nпароли и токены\n\nbase64 — КОДИРОВАНИЕ,\nне шифрование (лекция 25)", { fs: 13.5, align: "left", fill: C.DEEP, color: C.WHITE, line: C.DEEP });
s.addText("env-переменные читаются на старте: сменили ConfigMap — перезапустите поды", { x: M, y: 4.2, w: 9, h: 0.4, fontFace: C.BODY, fontSize: 13.5, italic: true, color: C.TXT_MUT, align: "center", margin: 0 });
s.addNotes("§ Ядро-6 · ~3 мин · Правило лабы 1: конфиг не запекается в образ. Secret: encryption at rest + внешние менеджеры — лекция 25. § Конфигурация: ConfigMap и Secret.");

// ---------- 14. Пробы ----------
s = lightSlide(pres, "Три пробы — три разных вопроса kubelet'а");
const probes = [
  ["readiness", "«слать трафик?» — провал = под выведен из Service"],
  ["liveness", "«процесс безнадёжно завис?» — провал = ПЕРЕЗАПУСК"],
  ["startup", "«инициализация закончена?» — пока ждёт, остальные молчат"],
];
probes.forEach((p, i) => {
  chip(s, M, 1.5 + i * 0.95, 9, 0.8, [
    { text: p[0] + "  ", options: { bold: true, fontSize: 15, color: C.DEEP } },
    { text: "· " + p[1], options: { fontSize: 13, color: C.TXT_MUT } },
  ], { align: "left" });
});
s.addText("золотое правило: liveness проверяет только сам процесс; readiness — полезную работу (и зависимости)", { x: M, y: 4.5, w: 9, h: 0.4, fontFace: C.BODY, fontSize: 13.5, italic: true, color: C.ACCENT, align: "center", margin: 0 });
s.addNotes("§ Ядро-7 · ~4 мин · Путать пробы — главный способ устроить рестарт-шторм здоровому приложению. Liveness с проверкой БД перезапускает здоровые контейнеры, когда болеет сосед. Сейчас проверим голосованием. § Пробы.");

// ---------- 15. PI ----------
slidePI(pres, "Голосуем: сервис греется 60 с, при мёртвой БД жив, но отвечает ошибками", [
  "A. liveness проверяет БД — перезапуск всё починит",
  "B. readiness — «могу работать» (и БД), liveness — «процесс жив», startup — 60 с",
  "C. только liveness с initialDelaySeconds: 5 — раньше проверим, раньше найдём",
  "D. пробы не нужны: K8s и так перезапускает упавшее",
], "Peer instruction · ~6 мин · Голос → 90 сек спора → голос. Подсказка после первого голоса: перезапуск лечит только то, что лечится перезапуском. § PI-1.");

// ---------- 16-19. PI разборы ----------
slidesPIFeedback(pres, [
  ["A — мимо: рестарт вашего пода не оживит чужую БД", "Liveness, зависящая от внешней системы, перезапускает здоровые\nконтейнеры, когда болеет сосед, — рестарт-шторм в довесок к инциденту.", false],
  ["C — мимо: проба убьёт контейнер до первого запуска", "Приложение стартует минуту, проверка приходит через 5 секунд:\nвечный CrashLoopBackOff руками собственного мониторинга.", false],
  ["D — мимо: «перезапускает упавшее» ≠ «не шлёт трафик неготовым»", "Без readiness Service льёт запросы в под, который греется\nили отвечает ошибками. Пользователь видит 500-е.", false],
  ["B — да: каждой пробе — свой вопрос", "Readiness выводит под из трафика, пока БД лежит, — и вернёт сам.\nLiveness — только про зависший процесс. Startup покрывает прогрев.", true],
]);

// ---------- 20. Пауза ----------
slidePause(pres, [
  "Манифест: «Хочу три реплики.»",
  "Кластер: «Понял. Держу три. Всегда. Даже если ты передумал руками.»",
], "reconcile loop не спит, не устаёт и не читает ваши горячие правки на сервере", "Слайд-пауза · 30–60 сек · Выдохнули. Прочитать как диалог с очень исполнительным джинном. Связка: «джинн держит реплики — но сколько им можно есть?» — едем к ресурсам. § граница блоков, ~55-я минута.");

// ---------- 21. Ресурсы и rollout ----------
s = lightSlide(pres, "Requests — бронь для планировщика, limits — потолок с OOMKill");
chip(s, M, 1.45, 4.3, 1.6, "requests\ncpu: 100m · memory: 128Mi\nгарантия при размещении", { fs: 13.5 });
chip(s, 5.15, 1.45, 4.15, 1.6, "limits\nmemory: 256Mi → OOMKill\ncpu → троттлинг", { fs: 13.5 });
chip(s, M, 3.3, 9, 1.0, "RollingUpdate: поднять нового → дождаться readiness → погасить старого;\nплохая версия не проходит readiness — раскатка замирает; rollout undo — откат", { fs: 13.5 });
s.addNotes("§ Ядро-8 · ~5 мин · Без requests планирование вслепую; низкий limit памяти = OOMKill под нагрузкой. Калибровка — по метрикам (л. 24), HPA — л. 26. maxUnavailable: 0, maxSurge: 1. Blue/green и canary — л. 22. § Ресурсы и обновления.");

// ---------- 22. Живой сеанс ----------
s = lightSlide(pres, "Живой сеанс: «Хочу 3 реплики!» — строим вместе");
const flow = [["kubectl\napply", ""], ["apiserver\n→ etcd", ""], ["контроллер:\nRS + поды", ""], ["scheduler:\nвыбор нод", ""], ["kubelet:\nзапуск", ""]];
flow.forEach((p, i) => {
  chip(s, M + i * 1.92, 1.7, 1.6, 1.0, p[0], { fs: 12.5, bold: true });
  if (i < flow.length - 1) arrow(s, M + i * 1.92 + 1.62, 2.06, 0.28);
});
chip(s, M, 3.05, 9, 1.2, "шаг 2: нода умерла → «желаемое 3, реальных 2» → контроллер доздал под\nшаг 3: обновление 1.3.0 → второй ReplicaSet → readiness сломана? раскатка замерла → undo", { fs: 13.5 });
s.addText("эталон для сверки — sequence-диаграмма в тексте лекции", { x: M, y: 4.5, w: 9, h: 0.4, fontFace: C.BODY, fontSize: 13, italic: true, color: C.TXT_MUT, align: "center", margin: 0 });
s.addNotes("Живой сеанс · ~8 мин · Строить mermaid в редакторе по шагам, проговаривая: кто с кем говорит (всё — через apiserver), где reconcile. Три сценария: создание, смерть ноды, обновление с откатом. Во всех трёх — руками только желаемое состояние. § Живой сеанс.");

// ---------- 23. Типичные ошибки ----------
s = lightSlide(pres, "Пять ошибок, за которые кластер отомстит");
const errs18 = [
  "Состояние внутри пода  →  умирает вместе с подом; PVC — следующая пара",
  "image: latest  →  что запущено — загадка, откат невозможен",
  "liveness проверяет БД  →  рестарт-шторм здоровых контейнеров",
  "нет requests/limits  →  планирование вслепую, внезапные OOMKill",
  "kubectl edit на проде  →  контроллер сотрёт; git — источник истины (л. 22)",
];
errs18.forEach((t, i) => chip(s, M, 1.45 + i * 0.78, 9, 0.66, t, { align: "left", fs: 13.5 }));
s.addNotes("Типичные ошибки · ~3 мин · Все пять уже звучали в паре — закрепление узнаванием; попросить зал назвать «какой раздел это опровергает». § Типичные ошибки.");

// ---------- 24. Квиз-закрепление ----------
slideQuiz(pres, "Закрепление: четыре вопроса по сегодняшней паре", [
  "1. Что такое reconcile loop и почему убитый под вернулся?",
  "2. Компоненты control plane — и что легло у OpenAI?",
  "3. Зачем матрёшка Deployment → ReplicaSet → Pod?",
  "4. readiness против liveness: что будет, если перепутать?",
], "Квиз-закрепление · ~5 мин · Молча в конспект, сверка с соседом, разбор. Ответы в конце лекции. § Квиз-закрепление.");

// ---------- 25. Мост к лабе ----------
s = lightSlide(pres, "Лаба 5 стартует: «СмартДом» едет в кластер");
chip(s, M, 1.55, 4.3, 2.9, "В лабе 5 руками:\n\n· kind/minikube — свой кластер\n· Deployment с пробами и ресурсами\n· Service + Ingress\n· ConfigMap/Secret\n· RollingUpdate + rollout undo", { align: "left", fs: 13.5 });
chip(s, 5.15, 1.55, 4.15, 2.9, "Домашка на одно предложение:\n\n«Умение читать reconcile loop\nпригодится лично мне,\nпотому что…»\n\nБез общих слов. Спрошу троих.", { align: "left", fs: 13.5, fill: C.DEEP, color: C.WHITE, line: C.DEEP });
s.addNotes("Мост к лабе · ~2 мин · Три кита лабы 5 собраны: модели облака (л. 16), сеть (л. 17), K8s (сегодня). Стейт и PVC — следующая пара и лаба 6. § Мост к лабораторной № 5.");

// ---------- 26. Финал ----------
slideFinal(pres,
  "Почитать: kubernetes.io/docs (Workloads, Services)  ·  «Kubernetes: Up and Running», гл. 1–7",
  "Полный текст лекции, квизы, ответы и источники крючка — в репозитории курса",
  "Финал · ~2 мин · Вопросы. Напомнить домашку и старт лабы 5. Следующая пара — состояние и хранение в K8s. § Список литературы.");

pres.writeFile({ fileName: OUT }).then((f) => console.log("written:", f));
