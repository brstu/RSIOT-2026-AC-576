// Общий каркас колод РСиОТ: палитра «Океан» (teal + коралловый сигнал),
// мастера с title-плейсхолдерами, хелперы chip/arrow.
// Стандарт скилла university-teacher (references/presentation.md).
const pptxgen = require("pptxgenjs");

const C = {
  DEEP: "0B3C49",   // доминирующий: фон тёмных слайдов, акцент-панели
  WHITE: "FFFFFF",
  ACCENT: "E76F51", // сигнальный (коралл): только «смотри сюда»
  OK: "12876F",     // бейдж «правильный ответ», успех
  INK: "10333C",    // текст на светлом
  TXT_MUT: "3E5C63",
  SUB_D: "9CC8CD",  // приглушённые подписи на тёмном
  CAP_D: "DFF2F4",  // основной текст на тёмном
  PANEL: "E8F3F4",  // карточки на светлом
  LINEC: "9CC8CD",  // обводки карточек
  MUTFILL: "4A7078",// заливка стрелок/нейтральных фигур
  HEAD: "Cambria", BODY: "Calibri", W: 10, M: 0.5,
};

function newDeck() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.defineSlideMaster({
    title: "LIGHT", background: { color: C.WHITE },
    objects: [{ placeholder: { options: { name: "title", type: "title", x: C.M, y: 0.32, w: C.W - 2 * C.M, h: 0.95, fontFace: C.HEAD, fontSize: 26, bold: true, color: C.INK, valign: "top", margin: 0 }, text: "" } }],
  });
  pres.defineSlideMaster({
    title: "DARK", background: { color: C.DEEP },
    objects: [{ placeholder: { options: { name: "title", type: "title", x: C.M, y: 0.5, w: C.W - 2 * C.M, h: 0.9, fontFace: C.HEAD, fontSize: 28, bold: true, color: C.WHITE, valign: "top", margin: 0 }, text: "" } }],
  });
  return pres;
}

function darkSlide(pres, title, tOpts = {}) {
  const s = pres.addSlide({ masterName: "DARK" });
  if (title !== undefined) s.addText(title, Object.assign({ placeholder: "title" }, tOpts));
  return s;
}
function lightSlide(pres, title) {
  const s = pres.addSlide({ masterName: "LIGHT" });
  s.addText(title, { placeholder: "title" });
  return s;
}
function chip(s, x, y, w, h, text, o = {}) {
  s.addText(text, { shape: "roundRect", rectRadius: 0.08, x, y, w, h,
    fill: { color: o.fill || C.PANEL }, line: { color: o.line || C.LINEC },
    fontFace: C.BODY, fontSize: o.fs || 16, color: o.color || C.INK,
    align: o.align || "center", valign: "middle", bold: !!o.bold, margin: 0.06 });
}
function arrow(s, x, y, w) { s.addShape("rightArrow", { x, y, w, h: 0.28, fill: { color: C.MUTFILL } }); }

// Стандартные слоты
function slideQuiz(pres, title, questions, notes) {
  const s = lightSlide(pres, title);
  questions.forEach((q, i) => chip(s, C.M, 1.45 + i * 0.95, 9, 0.8, q, { align: "left", fs: 17 }));
  s.addNotes(notes);
  return s;
}
function slideOutcomes(pres, items, notes) {
  const s = lightSlide(pres, "После пары вы сможете…");
  items.forEach((o, i) => {
    const x = C.M + (i % 3) * 3.07, y = 1.6 + Math.floor(i / 3) * 1.75;
    chip(s, x, y, 2.85, 1.5, [
      { text: o[0] + "\n", options: { bold: true, fontSize: 16 } },
      { text: o[1], options: { fontSize: 14, color: C.TXT_MUT } },
    ]);
  });
  s.addNotes(notes);
  return s;
}
function slideRoadmap(pres, title, stops, notes) {
  const s = lightSlide(pres, title);
  stops.forEach((r, i) => {
    chip(s, C.M + i * 1.92, 2.3, 1.62, 1.2, r, { fs: 14, bold: true });
    if (i < stops.length - 1) arrow(s, C.M + i * 1.92 + 1.64, 2.76, 0.26);
  });
  s.addNotes(notes);
  return s;
}
function slidePI(pres, title, options, notes) {
  const s = lightSlide(pres, title);
  options.forEach((v, i) => chip(s, C.M, 1.5 + i * 0.92, 9, 0.78, v, { align: "left", fs: 16 }));
  s.addNotes(notes);
  return s;
}
// Разбор PI: последовательные тёмные слайды, неверные -> верный с бейджем
function slidesPIFeedback(pres, items) {
  items.forEach((f, i) => {
    const s = darkSlide(pres, f[0], { fontSize: 24 });
    if (f[2]) chip(s, 3.5, 1.5, 3.0, 0.55, "ПРАВИЛЬНЫЙ ОТВЕТ", { fs: 14, bold: true, fill: C.OK, line: C.OK, color: C.WHITE });
    s.addText(f[1], { x: C.M, y: 2.25, w: 9, h: 1.7, fontFace: C.BODY, fontSize: 18, color: C.CAP_D, margin: 0 });
    s.addText(`разбор ${i + 1} из ${items.length}`, { x: C.M, y: 4.9, w: 9, h: 0.35, fontFace: C.BODY, fontSize: 13, color: C.SUB_D, align: "center", margin: 0 });
    s.addNotes(f[3] || (f[2]
      ? "Разбор PI, финал · Кульминация: правильный ответ. Спросить: кто поменял мнение после спора с соседом?"
      : "Разбор PI · 20-30 сек. Спросить поднятием рук, кто голосовал; почему вариант правдоподобен и где ломается."));
  });
}
function slidePause(pres, lines, footer, notes) {
  const s = darkSlide(pres, "Пауза · 60 секунд", { fontSize: 16, color: C.CAP_D, align: "center", charSpacing: 4, bold: false });
  chip(s, 1.6, 1.7, 6.8, 1.05, lines[0], { fs: 17, fill: C.PANEL, color: C.INK });
  chip(s, 1.6, 3.05, 6.8, 1.05, lines[1], { fs: 17, bold: true, fill: lines[2] || C.OK, color: C.WHITE, line: lines[2] || C.OK });
  s.addText(footer, { x: C.M, y: 4.45, w: 9, h: 0.4, fontFace: C.BODY, fontSize: 14, italic: true, color: C.CAP_D, align: "center", margin: 0 });
  s.addNotes(notes || "Слайд-пауза · 30–60 сек · Выдохнули, ничего не записываем. Прочитать с интонацией, дальше едем.");
  return s;
}
function slideFinal(pres, lit, extra, notes) {
  const s = darkSlide(pres, "Вопросы?", { y: 1.7, fontSize: 40, align: "center" });
  s.addText(lit, { x: C.M, y: 3.1, w: 9, h: 0.5, fontFace: C.BODY, fontSize: 14, color: C.SUB_D, align: "center", margin: 0 });
  s.addText(extra, { x: C.M, y: 3.7, w: 9, h: 0.4, fontFace: C.BODY, fontSize: 14, color: C.CAP_D, align: "center", margin: 0 });
  s.addNotes(notes);
  return s;
}

module.exports = { C, newDeck, darkSlide, lightSlide, chip, arrow, slideQuiz, slideOutcomes, slideRoadmap, slidePI, slidesPIFeedback, slidePause, slideFinal };
