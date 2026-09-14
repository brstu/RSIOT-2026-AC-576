# chaos_demo.ps1 — мини-chaos эксперимент лабы 3 (Windows PowerShell 5.1).
#
# Канон лекции 09: steady state -> гипотеза -> впрыск сбоя -> наблюдение ->
# откат. Скрипт замораживает (pause) или останавливает (stop) alerts, шлёт
# серию показаний в devices, печатает таблицу задержек и состояний breaker'а,
# затем возвращает alerts и ждёт догона очереди.
#
# Прогон 1 (стенд «сломан из коробки», breaker выключен):
#     powershell -ExecutionPolicy Bypass -File .\chaos_demo.ps1
# Прогон 2 (с breaker'ом — сравните таблицы):
#     $env:BREAKER = "on"
#     docker compose up -d devices
#     powershell -ExecutionPolicy Bypass -File .\chaos_demo.ps1
#
# Режим сбоя: -Mode pause (по умолчанию, «завис») или -Mode stop («умер»).

param(
    [ValidateSet("pause", "stop")]
    [string]$Mode = "pause",
    [int]$Requests = 6,
    [string]$DevicesUrl = "http://localhost:8080",
    [string]$AlertsUrl = "http://localhost:8081"
)

$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot

function Send-Reading {
    param([double]$Value)
    $body = '{"device_id":"chaos-1","sensor":"temperature","value":' + $Value + '}'
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $resp = Invoke-RestMethod -Method Post -Uri "$DevicesUrl/readings" -ContentType "application/json" -Body $body
        $sw.Stop()
        $delivered = "-"
        $breaker = "-"
        if ($null -ne $resp.alert) {
            if ($resp.alert.delivered) { $delivered = "delivered" } else { $delivered = "DEGRADED->queue" }
            $breaker = $resp.alert.breaker
        }
        New-Object PSObject -Property @{ ms = [int]$sw.ElapsedMilliseconds; http = "2xx"; outcome = $delivered; breaker = $breaker }
    } catch {
        $sw.Stop()
        $code = "ERR"
        if ($null -ne $_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
        New-Object PSObject -Property @{ ms = [int]$sw.ElapsedMilliseconds; http = "$code"; outcome = "rejected"; breaker = "-" }
    }
}

function Get-Health {
    try { Invoke-RestMethod "$DevicesUrl/health" } catch { $null }
}

function Get-AlertCount {
    try { (Invoke-RestMethod "$AlertsUrl/alerts").count } catch { "?" }
}

# ---- Шаг 0. Steady state: обе службы живы, тревога доставляется быстро ----
Write-Host ""
Write-Host "=== Шаг 0. Steady state ===" -ForegroundColor Cyan
$health = Get-Health
if ($null -eq $health) {
    Write-Host "devices не отвечает — поднимите стенд: docker compose up --build -d" -ForegroundColor Red
    Pop-Location
    exit 1
}
Write-Host ("breaker: " + $health.breaker.state + ", очередь fallback: " + $health.fallback_queue)
$alertsBefore = Get-AlertCount
$r = Send-Reading -Value 71.5
Write-Host ("контрольная тревога: " + $r.ms + " ms, " + $r.outcome)
Write-Host ("ГИПОТЕЗА: при сбое alerts devices продолжит отвечать быстро, тревоги не потеряются")

# ---- Шаг 1. Впрыск сбоя (минимальный blast radius: один контейнер) ----
Write-Host ""
Write-Host "=== Шаг 1. Впрыск: docker compose $Mode alerts ===" -ForegroundColor Cyan
docker compose $Mode alerts | Out-Null

# ---- Шаг 2. Наблюдение: серия показаний выше порога ----
Write-Host ""
Write-Host "=== Шаг 2. $Requests показаний при лежащем alerts ===" -ForegroundColor Cyan
$table = @()
for ($i = 1; $i -le $Requests; $i++) {
    $r = Send-Reading -Value (70 + $i)
    $table += $r
    Write-Host ("{0,2}: {1,6} ms  HTTP {2,-4} {3,-16} breaker={4}" -f $i, $r.ms, $r.http, $r.outcome, $r.breaker)
}
$slow = @($table | Where-Object { $_.ms -ge 1000 })
Write-Host ""
Write-Host ("медленных запросов (>= 1 c): " + $slow.Count + " из " + $Requests)
$health = Get-Health
if ($null -ne $health) {
    Write-Host ("breaker: " + $health.breaker.state + ", очередь fallback: " + $health.fallback_queue)
}

# ---- Шаг 3. Откат: вернуть alerts и дождаться догона очереди ----
Write-Host ""
Write-Host "=== Шаг 3. Откат и восстановление ===" -ForegroundColor Cyan
if ($Mode -eq "pause") { docker compose unpause alerts | Out-Null } else { docker compose start alerts | Out-Null }
Write-Host "ждём догон очереди (breaker: OPEN -> HALF_OPEN -> CLOSED)..."
$deadline = (Get-Date).AddSeconds(40)
do {
    Start-Sleep -Seconds 2
    $health = Get-Health
    $queue = -1
    if ($null -ne $health) { $queue = $health.fallback_queue }
    Write-Host ("  breaker=" + $health.breaker.state + " очередь=" + $queue)
} while ($queue -gt 0 -and (Get-Date) -lt $deadline)

$alertsAfter = Get-AlertCount
Write-Host ""
Write-Host "=== Итог ===" -ForegroundColor Cyan
Write-Host ("тревог в alerts до сбоя : " + $alertsBefore)
Write-Host ("тревог в alerts после   : " + $alertsAfter)
if ($Mode -eq "stop") {
    Write-Host "  режим stop: контейнер alerts ПЕРЕЗАПУЩЕН, его память обнулилась -"
    Write-Host "  тревоги до сбоя исчезли (антипаттерн курса: состояние в контейнере),"
    Write-Host "  а серия доехала догоном из очереди fallback."
} else {
    Write-Host ("  = тревоги до сбоя + " + $Requests + " из серии, доставленных догоном; дублей нет")
}
if ($null -ne $health -and $null -ne $health.breaker.recent_transitions) {
    Write-Host "переходы breaker'а (из /health):"
    foreach ($t in $health.breaker.recent_transitions) { Write-Host ("  " + $t) }
}
Write-Host ""
Write-Host "ВЫВОД пишете сами: подтвердилась ли гипотеза? Сравните прогоны BREAKER=off / on."
Pop-Location
