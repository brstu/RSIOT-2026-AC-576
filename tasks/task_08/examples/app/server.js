// «СмартДом»: сервис приёма показаний (ingest-reading) с метриками Prometheus.
// Вариант 0: prefix=smarthome_. Node.js 22, Express 5, prom-client 15.
import express from "express";
import client from "prom-client";

const app = express();
app.use(express.json());

const register = new client.Registry();
client.collectDefaultMetrics({ register });

// Counter: сколько показаний принято (метка status — ограниченный словарь!)
const readingsTotal = new client.Counter({
  name: "smarthome_readings_total",
  help: "Total readings ingested",
  labelNames: ["type", "status"],
});

// Histogram: длительность обработки показания (секунды)
const ingestDuration = new client.Histogram({
  name: "smarthome_ingest_duration_seconds",
  help: "Reading ingest latency",
  labelNames: ["type"],
  buckets: [0.05, 0.1, 0.2, 0.3, 0.5, 1, 2, 5],
});

// Gauge: сколько Hub'ов сейчас на связи
const hubConnections = new client.Gauge({
  name: "smarthome_hub_connections",
  help: "Currently connected hubs",
});

register.registerMetric(readingsTotal);
register.registerMetric(ingestDuration);
register.registerMetric(hubConnections);

// Идентификация студента (требование лабы): логируем при старте
console.log(
  `start STU_ID=${process.env.STU_ID || "?"} STU_VARIANT=${process.env.STU_VARIANT || "0"}`
);

// Имитация подключённых Hub'ов
setInterval(() => hubConnections.set(40 + Math.floor(Math.random() * 20)), 5000);

app.get("/health", (_req, res) => res.json({ ok: true }));

app.post("/readings", async (req, res) => {
  const type = ["temperature", "humidity", "smoke"].includes(req.body?.type)
    ? req.body.type
    : "other"; // нормализуем метку — не даём кардинальности взорваться
  const end = ingestDuration.startTimer({ type });
  try {
    if (!req.body?.deviceId || req.body?.value === undefined) {
      readingsTotal.inc({ type, status: "400" });
      return res.status(400).json({ error: "deviceId and value required" });
    }
    // FAULT=1 — имитация деградации для демонстрации алерта
    if (process.env.FAULT === "1" && Math.random() < 0.3) {
      readingsTotal.inc({ type, status: "503" });
      return res.status(503).json({ error: "storage unavailable (simulated)" });
    }
    await new Promise((r) => setTimeout(r, 20 + Math.random() * 80)); // "запись"
    readingsTotal.inc({ type, status: "200" });
    res.status(200).json({ accepted: true });
  } finally {
    end();
  }
});

app.get("/metrics", async (_req, res) => {
  res.set("Content-Type", register.contentType);
  res.end(await register.metrics());
});

app.listen(8080, () => console.log("smarthome ingest on :8080"));
