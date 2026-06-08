@echo off
chcp 65001 >nul
title Docker Lab - Прибышеня Д.А. (Вариант 17)
color 0A

:menu
cls
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                        ║
echo ║     ЛАБОРАТОРНАЯ РАБОТА - ВАРИАНТ 17                  ║
echo ║                                                        ║
echo ║     Студент:  Прибышеня Дмитрий Александрович         ║
echo ║     Группа:   АС-576                                  ║
echo ║     ID:       220245                                  ║
echo ║     Slug:     as-576-220245-v17                       ║
echo ║                                                        ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo ╔════════════════════════════════════════╗
echo ║           ГЛАВНОЕ МЕНЮ                 ║
echo ╠════════════════════════════════════════╣
echo ║  [1] Собрать образ                     ║
echo ║  [2] Запустить сервисы                 ║
echo ║  [3] Собрать и запустить (рекоменд.)   ║
echo ║  [4] Пересобрать (без кэша)            ║
echo ║  [5] Остановить (graceful shutdown)    ║
echo ║  [6] Перезапустить                     ║
echo ║  [7] Показать логи (приложение)        ║
echo ║  [8] Показать логи (все)              ║
echo ║  [9] Проверить статус                 ║
echo ║ [10] Тестировать API                  ║
echo ║ [11] Открыть в браузере              ║
echo ║ [12] Размер образа                   ║
echo ║ [13] Очистить всё                     ║
echo ║  [0] Выход                            ║
echo ╚════════════════════════════════════════╝
echo.
set /p choice="Выберите действие (0-13): "

if "%choice%"=="1" goto build
if "%choice%"=="2" goto run
if "%choice%"=="3" goto build_and_run
if "%choice%"=="4" goto rebuild
if "%choice%"=="5" goto stop
if "%choice%"=="6" goto restart
if "%choice%"=="7" goto logs_app
if "%choice%"=="8" goto logs_all
if "%choice%"=="9" goto status
if "%choice%"=="10" goto test
if "%choice%"=="11" goto browser
if "%choice%"=="12" goto size
if "%choice%"=="13" goto clean
if "%choice%"=="0" goto exit
echo Неверный выбор!
timeout /t 2 >nul
goto menu

:build
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║        СБОРКА DOCKER ОБРАЗА           ║
echo ╚════════════════════════════════════════╝
echo.
echo 🔨 Сборка образа flask-student-app:stu-220245-v17...
echo.
docker build -t flask-student-app:stu-220245-v17 .
echo.
echo ════════════════════════════════════════
echo 📦 РАЗМЕР ОБРАЗА:
echo ════════════════════════════════════════
docker images flask-student-app:stu-220245-v17 --format "Образ: {{.Repository}}:{{.Tag}} | Размер: {{.Size}} | Создан: {{.CreatedAt}}"
echo.
echo ✅ Сборка завершена!
pause
goto menu

:run
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║        ЗАПУСК СЕРВИСОВ               ║
echo ╚════════════════════════════════════════╝
echo.
echo 🚀 Запуск контейнеров...
docker-compose up -d
echo.
echo ⏳ Ожидание инициализации (10 секунд)...
timeout /t 10 /nobreak >nul
echo.
echo ════════════════════════════════════════
echo 📋 СТАТУС КОНТЕЙНЕРОВ:
echo ════════════════════════════════════════
docker-compose ps
echo.
echo ════════════════════════════════════════
echo 🏥 HEALTH CHECK:
echo ════════════════════════════════════════
curl -s http://localhost:9051/ready
echo.
echo.
echo ════════════════════════════════════════
echo ✅ Сервисы запущены!
echo 🌐 http://localhost:9051
echo ════════════════════════════════════════
echo.
set /p open="Открыть в браузере? (y/n): "
if /i "%open%"=="y" start http://localhost:9051
pause
goto menu

:build_and_run
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║     СБОРКА И ЗАПУСК (ПОЛНЫЙ ЦИКЛ)    ║
echo ╚════════════════════════════════════════╝
echo.
echo 🔨 Шаг 1/2: Сборка образа...
docker build -t flask-student-app:stu-220245-v17 .
echo.
echo 🚀 Шаг 2/2: Запуск сервисов...
docker-compose up -d
echo.
echo ⏳ Ожидание инициализации...
timeout /t 8 /nobreak >nul
echo.
echo ════════════════════════════════════════
echo 📋 СТАТУС:
echo ════════════════════════════════════════
docker-compose ps
echo.
echo ════════════════════════════════════════
echo 🏥 HEALTH CHECK:
echo ════════════════════════════════════════
curl -s http://localhost:9051/ready
echo.
echo.
echo ✅ Готово! Открываю браузер...
timeout /t 2 /nobreak >nul
start http://localhost:9051
echo.
pause
goto menu

:rebuild
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║     ПЕРЕСБОРКА (БЕЗ КЭША)            ║
echo ╚════════════════════════════════════════╝
echo.
echo ⚠️  Это удалит кэш Docker и пересоберёт образ с нуля
echo.
set /p confirm="Продолжить? (y/n): "
if /i not "%confirm%"=="y" goto menu
echo.
echo 🛑 Остановка сервисов...
docker-compose down
echo.
echo 🔨 Пересборка образа без кэша...
docker build --no-cache -t flask-student-app:stu-220245-v17 .
echo.
echo 🚀 Запуск...
docker-compose up -d
echo.
echo ⏳ Ожидание...
timeout /t 8 /nobreak >nul
echo ✅ Готово!
pause
goto menu

:stop
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║     ОСТАНОВКА (GRACEFUL SHUTDOWN)    ║
echo ╚════════════════════════════════════════╝
echo.
echo 🛑 Отправка SIGTERM...
echo 📜 Ожидание завершения запросов...
echo 🔌 Закрытие соединения с Redis...
echo.
docker-compose down
echo.
echo ✅ Сервисы остановлены корректно
echo.
pause
goto menu

:restart
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║        ПЕРЕЗАПУСК СЕРВИСОВ           ║
echo ╚════════════════════════════════════════╝
echo.
echo 🔄 Перезапуск контейнеров...
docker-compose restart
echo.
timeout /t 5 /nobreak >nul
echo ✅ Готово!
docker-compose ps
pause
goto menu

:logs_app
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║     ЛОГИ ПРИЛОЖЕНИЯ (Ctrl+C выход)   ║
echo ╚════════════════════════════════════════╝
echo.
docker-compose logs -f app
goto menu

:logs_all
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║     ВСЕ ЛОГИ (Ctrl+C выход)          ║
echo ╚════════════════════════════════════════╝
echo.
docker-compose logs -f
goto menu

:status
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║        СТАТУС СЕРВИСОВ              ║
echo ╚════════════════════════════════════════╝
echo.
echo 📋 Контейнеры:
echo ════════════════════════════════════════
docker-compose ps
echo.
echo 📦 Образ:
echo ════════════════════════════════════════
docker images flask-student-app:stu-220245-v17 --format "{{.Repository}}:{{.Tag}} | {{.Size}} | {{.CreatedAt}}"
echo.
echo 📁 Тома:
echo ════════════════════════════════════════
docker volume ls --filter name=data_w17
echo.
echo 🌐 Сети:
echo ════════════════════════════════════════
docker network ls --filter name=net-as-576-220245-v17
echo.
pause
goto menu

:test
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║       ТЕСТИРОВАНИЕ API               ║
echo ╚════════════════════════════════════════╝
echo.
echo 1️⃣  Health Check (/ready):
echo ════════════════════════════════════════
curl -s http://localhost:9051/ready
echo.
echo.
echo 2️⃣  Информация о студенте (/api/info):
echo ════════════════════════════════════════
curl -s http://localhost:9051/api/info
echo.
echo.
echo 3️⃣  Тест Redis кэша (запись):
echo ════════════════════════════════════════
curl -s -X POST http://localhost:9051/api/cache/test-key-17 -H "Content-Type: application/json" -d "{\"value\":\"test-value-17\"}"
echo.
echo.
echo 4️⃣  Тест Redis кэша (чтение):
echo ════════════════════════════════════════
curl -s http://localhost:9051/api/cache/test-key-17
echo.
echo.
echo 5️⃣  Главная страница (HTTP статус):
echo ════════════════════════════════════════
curl -s -o nul -w "HTTP Status: %%{http_code}" http://localhost:9051/
echo.
echo.
echo ════════════════════════════════════════
echo ✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО
echo ════════════════════════════════════════
echo.
pause
goto menu

:browser
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║       ОТКРЫТИЕ В БРАУЗЕРЕ           ║
echo ╚════════════════════════════════════════╝
echo.
echo 🌐 Открываю страницы...
start http://localhost:9051
timeout /t 1 /nobreak >nul
start http://localhost:9051/ready
timeout /t 1 /nobreak >nul
start http://localhost:9051/api/info
echo.
echo ✅ Открыты:
echo    • Главная страница
echo    • Health Check
echo    • API Info
echo.
pause
goto menu

:size
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║        РАЗМЕР DOCKER ОБРАЗА          ║
echo ╚════════════════════════════════════════╝
echo.
echo 📦 Информация об образе:
echo ════════════════════════════════════════
docker images flask-student-app:stu-220245-v17
echo.
echo 📊 Детальная информация по слоям:
echo ════════════════════════════════════════
docker history flask-student-app:stu-220245-v17
echo.
echo ⚠️  Требование: образ должен быть ≤ 150MB
echo.
pause
goto menu

:clean
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║          ОЧИСТКА ВСЕГО               ║
echo ╚════════════════════════════════════════╝
echo.
echo ⚠️  ВНИМАНИЕ! Будут удалены:
echo    • Все контейнеры
echo    • Том data_w17 (все данные Redis!)
echo    • Образ flask-student-app:stu-220245-v17
echo.
set /p confirm="Вы уверены? Напишите YES для подтверждения: "
if not "%confirm%"=="YES" (
    echo Отмена.
    timeout /t 2 >nul
    goto menu
)
echo.
echo 🧹 Остановка и удаление контейнеров...
docker-compose down -v
echo.
echo 🗑️  Удаление образа...
docker rmi flask-student-app:stu-220245-v17 2>nul
echo.
echo 🧹 Очистка неиспользуемых ресурсов Docker...
docker system prune -f
echo.
echo ✅ Полная очистка завершена!
pause
goto menu

:exit
cls
echo.
echo ╔════════════════════════════════════════╗
echo ║          ДО СВИДАНИЯ!                ║
echo ╚════════════════════════════════════════╝
echo.
echo Студент: Прибышеня Д.А.
echo Группа: АС-576
echo Вариант: 17
echo.
timeout /t 2 >nul
exit