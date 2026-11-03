# Binance Spot Testnet: подготовка и приёмочный прогон

> Обновление 2026-11-03: фактический статус и ближайший план — [CURRENT_STATE.md](CURRENT_STATE.md), результаты прогонов — [VPS_TESTNET.md](VPS_TESTNET.md). Ранние формулировки ниже о неподготовленном окружении относятся к этапу до сборки.
> На текущем VPS используется /opt/trader-bot/env, Docker не установлен. Docker-команды ниже — альтернативный непроверенный вариант, не текущий runbook сервера.


2026-11-03. Запуск — на предоставляемом тестовом VPS. WSL не используется.

## Статус

Подготовлено, но не собрано и не запущено: контейнер нашего снимка Hummingbot, отдельный connector `binance_testnet`, его регистрация, REST/public WS/private WS маршруты, preflight конфигурации.

Локально прошли 5 независимых проверок маршрутизации и AST-проверка 12 Python-файлов. Полные connector/GridExecutor tests, сборка контейнера и реальная проверка Testnet ожидают VPS. Подтверждения работы бота пока нет.

## Первая очистка

61 upstream-файл перемещён в `D:\bots\trader_bot_archive_20261103\upstream-extras`, проверен SHA-256 каждого файла, есть manifest.json. Убраны upstream CI, чужие контроллеры, DEX/арбитражные/индикаторные примеры, Windows compile.bat, contributor-материалы.

Сохранены Grid Strike, runner v2_with_controllers, backtest_grid_strike, движок, коннекторы, библиотеки и тесты. Зависимые пакеты и нерелевантные exchange connectors пока не вырезаем вслепую: их проверка и окончательное сокращение — после успешной сборки/демонстрации. Старый Compose с gateway сохранён в архиве; новый содержит только наш сервис.

## Сервер

Нужны адрес, SSH-пользователь/порт, путь к SSH-ключу и каталог проекта. Сначала проверить сервер и наличие Docker/Compose. Не менять уже работающие сервисы. Ключи должны быть именно Binance Spot Testnet, не production и не Futures Testnet.

Ключи вводить через защищённый hbot connect либо stdin JSON, хранить в encrypted keystore. Не класть секреты в Docker image, параметры командной строки или репозиторий. Пароль keystore нужен при работе с CLI; способ передачи настроим при подключении к VPS.

## Сборка и тесты на VPS

Из каталога проекта:

```bash
docker compose build hummingbot
docker compose up -d hummingbot
docker compose exec hummingbot hbot --help
docker compose exec hummingbot python -m pytest test/hummingbot/connector/exchange/binance/test_binance_web_utils.py test/hummingbot/connector/exchange/binance/test_binance_utils.py test/hummingbot/connector/exchange/binance/test_binance_user_stream_data_source.py test/hummingbot/strategy_v2/executors/grid_executor/test_grid_executor.py -q
```

Compose строит локальный образ из нашего кода, без gateway, открытых портов и автоторговли. Upstream Dockerfile по-прежнему использует изменяемую базу Miniconda и диапазоны зависимостей: это экспериментальная сборка, не воспроизводимый production release. При успешной сборке записать digest/версии. В builder явно выбирается conda env hummingbot для pip и Cython.

`make build` не использовать: upstream target содержит `git clean -xdf`.

## Подключение и конфигурация

```bash
docker compose exec hummingbot hbot connect binance_testnet
```

Создать конфигурацию Grid Strike через hbot create, уточнив интерфейс через `hbot create --help`. Цены выбираются по текущим данным Testnet на момент прогона, не берутся из учебного примера.

Обязательные параметры экспериментального запуска:

- connector_name: binance_testnet;
- trading_pair: BTC-USDT либо другая доступная тестовая пара;
- start_price/end_price: актуальный диапазон вокруг тестовой цены;
- total_amount_quote: небольшой виртуальный бюджет, проходящий фильтры;
- leverage: 1 (Spot);
- limit_price: 0;
- keep_position: true;
- triple_barrier_config: stop_loss=null, time_limit=null, trailing_stop=null; take_profit задан как выход отдельного цикла;
- max_open_orders: небольшое число для наблюдаемого прогона.

До запуска выполнить:

```bash
docker compose exec hummingbot python tools/testnet_preflight.py conf/controllers/<имя>.yml
```

Preflight не подключается к сети и не создаёт ордеров; проверяет конфигурацию и регистрацию коннектора. Это отдельная проверка, а не встроенный запрет любых live-команд Hummingbot.

Grid Strike не объявляется готовым аналогом биржевого Spot Grid: фиксированное N, геометрическая сетка, стартовый инвентарь, поведение вне диапазона и сохранение актива на всех путях остановки ещё проверяются/адаптируются. Первый запуск — проверка подключения и исполнения, а не окончательная приёмка продукта.

## Сценарий и доказательства

1. Получить тестовые балансы, exchangeInfo, стакан и private stream; сохранить обезличенный результат.
2. Стартовать один бот, записать clientOrderId/exchangeOrderId, проверить цены, количества и бюджет.
3. Дождаться исполнения и последующего выхода; сопоставить REST и private WS, количество и комиссии. Не форсировать цикл сделкой против собственного ордера.
4. Проверить, что повтор события/команды не создаёт дополнительную сетку.
5. Применить ручную остановку, сверить отмены и оба актива; отсутствие рыночной продажи нужно подтвердить историей исполнений, а не наличием keep_position в YAML.
6. Отдельно проверить перезапуск и выход/возврат в диапазон. Если готовый Grid Strike делает иначе, зафиксировать расхождение и минимально исправить до показа.
7. После каждого сценария сверить фактические открытые заявки на бирже. Процесс, который завершился, не является доказательством отсутствия ордеров.

Сохранить отчёт в docs/ с датой, ревизией, параметрами без секретов, результатами тестов, ID тестовых заявок и найденными ограничениями. Не обозначать сценарий прошедшим без наблюдаемого результата.

После успешного прогона: простой Telegram-интерфейс → показ заказчику → уточнение поведения → окончательное сокращение ядра и развитие восстановления/масштабируемости.

Источники маршрутов: [Binance Testnet general info](https://developers.binance.com/en/docs/products/spot/testnet/general-info), [Spot Testnet raw WebSocket streams](https://github.com/binance/binance-spot-api-docs/blob/master/testnet/web-socket-streams.md). Для котировок используется /ws, чтобы сохранить raw event format ожидаемый коннектором.
