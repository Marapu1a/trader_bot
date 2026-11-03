# Наш Binance Grid Bot на Hummingbot

> Актуальное состояние на 2026-11-03: [CURRENT_STATE.md](docs/CURRENT_STATE.md).
> Hummingbot собран на VPS; 46 выбранных тестов и сетевые прогоны BinanceExchange/GridExecutor прошли. Торговые процессы остановлены. Telegram и полный цикл сетки ещё не готовы.
> Совместное ревью: [обращение к ChatGPT](docs/CHATGPT_REQUEST.md), [ответ ChatGPT](docs/CHATGPT_RESPONSE.md).


2026-11-03: выбран Hummingbot как основа. После импорта выполнена первая очистка примеров/контроллеров и добавлен Binance Spot Testnet. README.md оставлен оригинальным; примеры удалённых стратегий в нём больше не являются инструкциями для нашего проекта.

Текущий порядок: подготовка и прогон на тестовом VPS → простой Telegram → показ заказчику → дальнейшее выделение ядра. WSL не используем. См. [Testnet runbook](docs/TESTNET_RUNBOOK.md).

- [Рабочее ТЗ](docs/GRID_BOT_SPEC.md)
- [Карта интеграции и результаты осмотра](docs/HUMMINGBOT_INTEGRATION.md)
- [Предыдущее сравнение основ](docs/OPEN_SOURCE_REVIEW.md)

Источник: https://github.com/hummingbot/hummingbot

Снимок ветки master: `9af100d6822da7d2d0291a906c730ef172284ee2`. Это закреплённый снимок исходников, не утверждение о последнем стабильном релизе.

Старая история Git проекта сохранена в текущем `.git`; upstream импортирован как файлы, без замены origin и без вложенного `.git`. Коммит и push не выполнялись.

Прежний TypeScript-каркас, node_modules и dist перемещены в `D:\bots\trader_bot_archive_20261103`. Там же копия прежних проектных документов, проверенный `previous-history.bundle` и исходный `hummingbot-upstream.tar`. Перемещение проверено: 4141 файл, 67672257 байт. Текущие документы находятся в docs/.

Торговые настройки и ключи не созданы; движок не запущен. Upstream docker-compose использует latest: до запуска нужно выбрать воспроизводимый образ или сборку нашего снимка. `make build` содержит `git clean -xdf`, поэтому его нельзя использовать для обычной подготовки этого рабочего дерева: он удаляет неотслеживаемые файлы, включая наши пока не закоммиченные документы.

VPS setup and build status: [VPS_TESTNET.md](docs/VPS_TESTNET.md).
