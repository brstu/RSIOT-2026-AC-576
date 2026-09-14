# Лаба 03 — выжимка

**Тема:** отказоустойчивость: таймауты, circuit breaker, мини-chaos.
Написана с нуля 10.08.2026 (пересмотр лаб 09.08.2026: старое K8s-содержимое
task_03 — в `curriculum/archive_2025/task_03/` и `tasks/task_06/`).
Лекция-основа — 09 (+03 ретраи/ключи, +06 «мёртв или медленный»).

## Суть и артефакты

Продолжение лабы 2: та же пара caller → callee. Студент добавляет circuit
breaker на клиент (CLOSED/OPEN/HALF-OPEN, порог/окно/восстановление/пробы —
каждое число объяснить), fallback-очередь с лимитом (202 + degraded вместо
500) и автоматический догон без дублей (Idempotency-Key из ЛР2 хранится в
очереди), backpressure (семафор → честный 503 + Retry-After), chaos-канон:
steady state → письменная гипотеза → впрыск → два прогона (без/с breaker) →
вывод. Артефакты: каскад «до», лог цикла closed→open→half-open→closed,
таблица chaos, лог backpressure. Сдача: `students/<NameLatin>/task_03/{doc,src}`,
PR + 2 ревью.

## Критерии (100 + 15 бонусов)

Breaker 30 · fallback/догон 25 · chaos-эксперимент 15 (ключевые, 70) ·
backpressure 15 · отчёт 10 · документация 5. Бонусы: slow calls = ошибки 5,
приоритетный shedding 4, /metrics Prometheus 3, второй тип сбоя 3.
Пересдача: < 85 % по ключевым (< 60 из 70) → доработка и повторная защита.

## Варианты и примеры

`Варианты.md`: номер = номеру из ЛР2 (пара/стек/порты оттуда); pause
обязателен всем, вариантный сбой stop / slow N с / outage N с; параметры
breaker'а, вид очереди (файл jsonl / Redis-список — у кого Redis из ЛР2),
слоты 2–6, Retry-After. Вариант 0 = `examples/`: devices → alerts, breaker
~80 строк (`breaker.py`), fallback.py, pressure_demo.py, chaos_demo.ps1
(UTF-8 BOM!). Прогнано: pause без breaker — все запросы ~1.9 с; с breaker —
3 медленных → open → 5–45 мс fallback; unpause → half-open → closed, догон
6/6 без дублей; backpressure 12 клиентов: 4 слота висят, 8×503+Retry-After.

## Первый успех и связи

15 минут: поднять стенд, pause alerts, увидеть «висит ~2 с» на каждом
запросе, включить BREAKER=on — мгновенные 202. tc netem честно недоступен
(non-root, без NET_ADMIN) — задержки уровнем приложения (/slow). Мост:
лабы 5–6 (K8s сам убивает поды), лаба 8 (метрики breaker'а → SLO).
