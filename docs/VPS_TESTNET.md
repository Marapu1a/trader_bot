# Тестовый VPS — 2026-11-03

## Проверенный результат

### Реальный BinanceExchange + GridExecutor

Два ограниченных сетевых прогона завершены успешно (без подмены биржи; CLI и Grid Strike controller не участвовали). Скрипт `tools/testnet_grid_check.py` использует реальный Clock, BinanceExchange, GridExecutor и небольшой адаптер интерфейса стратегии с ограничением бюджета. Пик RAM 218 МБ и 207 МБ.

1. Maker-сетка: бюджет 45 тестовых USDT, 4 рассчитанных уровня, максимум 2 активных заявки. Созданы 2 BUY LIMIT_MAKER, получены события создания и отмены. Итог обеих заявок CANCELED, исполнений нет, балансы BTC/USDT не изменились. Доказательства `TESTNET_GRID_CHECK.json`.
2. Отдельный сценарий fill-and-hold: ровно одна MARKET BUY на 0.00014 BTC исполнена (orderId 10096855), GridExecutor выставил LIMIT_MAKER SELL (10096856). Вызов `early_stop(keep_position=True)` завершился POSITION_HOLD; продажа отменена без исполнения. BTC вырос с 1 до 1.00014, USDT снизился с 10000 до 9989.20291860. Рыночной продажи при остановке не было. Доказательства `TESTNET_GRID_HOLD_CHECK.json`. MARKET-вход здесь нужен для проверки исполненного состояния и не фиксирует торговую логику будущего продукта.

Не проверены: завершённая пара buy/sell с повторной постановкой, выход/возврат в диапазон, частичные исполнения, восстановление после перезапуска, CLI/controller stop path и Telegram. Параметр keep_position в конфигурации не заменяет явный keep_position=True в вызове остановки. Постоянный торговый процесс не оставлен.

Проверка одной заявки завершилась успешно: BTCUSDT BUY LIMIT_MAKER, цена 74772.30, количество 0.00014 BTC, номинал 10.468122 тестовых USDT. Order ID 10094768. REST создание и запрос дали NEW; приватный WebSocket доставил executionReport NEW. Отмена и повторный REST-запрос дали CANCELED, WebSocket доставил CANCELED. executedQty=0, среди открытых заявок этой заявки нет. Доказательства: `TESTNET_ORDER_CHECK.json`; скрипт `tools/testnet_order_check.py`. Это сетевой smoke-test с BinanceAuth и endpoints Hummingbot, не прогон полного BinanceExchange/GridExecutor и не проверка исполнения сделки или сеточной стратегии.

Последующая проверка ключей: файл принадлежит trader-bot, права 600. `tools/testnet_connection_check.py` под этим пользователем получил HTTP 200 от подписанного `/api/v3/account`, accountType=SPOT, canTrade=true, 517 записей активов в balances. Подписка `userDataStream.subscribe.signature` через Testnet WebSocket API также получила status=200. Использованы BinanceAuth и endpoints нашего Hummingbot. Ключи и подписи не выводились. Это проверка чтения аккаунта и принятия подписки; доставка событий исполнения и заявки ещё не проверены. На момент этой проверки файл ключей уже размещён (предыдущая запись об отсутствии относится к этапу сборки).

Собраны 61 Cython/C++ расширение. CLI `python bin/hbot --help` работает. Выбранные тесты Binance REST utils, регистрации Testnet, private stream и GridExecutor: **46 passed, 7 warnings**. Unit `trader-bot-check-20261103` завершилась успешно; лог `/opt/trader-bot/logs/check-20261103.log`. Версии пакетов сохранены в `VPS_PYTHON_FREEZE.txt` (снимок окружения, не полный lock-файл).

Первую build-unit остановили после успешной компиляции: editable pip-install начинал повторную сборку. Исходники подключены через `hummingbot-source.pth`, скрипт исправлен. Для CLI использовать `/opt/trader-bot/env/bin/python /opt/trader-bot/releases/testnet-20261103/bin/hbot` под пользователем trader-bot.

После проверки осталось 20 ГБ диска, доступно около 1.9 ГБ RAM. Список failed-сервисов совпал с исходным; nginx, PostgreSQL main, QIANQI API/bot, Telegram showcase API/bot активны. Торговый процесс не запущен, файл тестовых ключей ещё отсутствует. Авторизация, WS на реальной сети и ордера не проверены.

Хост: `201.51.22.244`, SSH root с существующим ключом QIANQI. Содержимое ключа в проект не копируется.

Размещение: отдельный системный пользователь `trader-bot`, корень `/opt/trader-bot` (750), исходники `/opt/trader-bot/releases/testnet-20261103`. Python 3.12.16 установлен в `/opt/trader-bot/env` через отдельный micromamba 2.10.0. Системный Python не изменён. Docker, WSL, изменения nginx и открытие портов не используются.

Архив исходников SHA256: `6ec3bec357665d829c24f3cb9548ddfa1694427e80cfbeacb2b670ac9d7aa8bb`. Совпадение проверено на сервере. Скрипт `tools/vps_build.sh` доставлен отдельно после архива.

Сборочная unit: `trader-bot-build-20261103.service`, пользователь trader-bot, MemoryMax=1400M, CPUQuota=70%, Nice=10, IOWeight=10, TasksMax=64, RuntimeMaxSec=3600. HBOT_BUILD_JOBS=1 ограничивает Cython и C++ одним процессом сборки. Скрипт устанавливает зависимости, собирает расширения и запускает выбранные тесты; торговлю не запускает. Это сборочная изоляция, не окончательный sandbox для торгового сервиса.

Проверка результата:

```bash
systemctl show trader-bot-build-20261103 -p ActiveState -p Result -p ExecMainStatus -p MemoryPeak
journalctl -u trader-bot-build-20261103 --no-pager
```

Ключи Spot Testnet: `/opt/trader-bot/shared/secrets/binance-testnet.json`, JSON с полями `api_key` и `api_secret`, владелец trader-bot, права 600; каталог secrets имеет права 700. Файл пока только место передачи ключей, автоматического импорта в Hummingbot ещё нет. Не выводить содержимое в логи или чат.

Перед изменениями: 22 ГБ свободного диска, около 1.9 ГБ доступной RAM, swap отсутствует. Уже находились в failed: crypto-launchpad-draw.service, crypto-launchpad-sandbox-check.service, pons-rpcfix-20261020-v4-activate.service, qianqi-public-automation.service. Эти сервисы не изменялись. Публичный REST ping Binance Spot Testnet ответил `{}`. Это не проверка авторизации и торговли.

На этом VPS команды Docker из TESTNET_RUNBOOK.md заменяются вызовами `/opt/trader-bot/env/bin/python` и CLI из того же окружения под пользователем trader-bot. Реальные ордера не разрешены; тестовые ордера требуют ключей и успешной проверки сборки/конфигурации.
