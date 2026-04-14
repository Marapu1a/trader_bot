# Bybit Trading Controller

TypeScript-приложение для управления торговым аккаунтом Bybit как контроллером состояния и действий, а не как готовой стратегией.

Текущий статус: **итерация 1 — каркас и инфраструктура**.

На этом этапе проект:

- поднимает локальное CLI/server-style приложение;
- безопасно загружает конфиг из `.env`;
- инициализирует единый логгер;
- фиксирует базовую модульную структуру под exchange, state, domain и services.

На этом этапе проект не включает:

- стратегии;
- торговую логику;
- REST/WS интеграцию с Bybit;
- Telegram-бота, веб-панель, ML, Docker, CI/CD.

## Структура

```text
src/
  app/
  config/
  domain/
  engine/
  exchange/
    bybit/
      adapters/
      rest/
      ws/
  guards/
  modes/
  services/
    account-service/
    market-service/
    order-service/
    position-service/
  state/
    reducers/
    selectors/
    store/
    sync/
  types/
  utils/
```

## Команды

```bash
npm install
npm run dev
npm run build
npm run start
npm run typecheck
npm run lint
npm run format
```

## Переменные окружения

Создайте локальный `.env` на основе `.env.example`.

Реальные ключи и секреты должны храниться только в `.env` и не коммитятся в репозиторий.

## Архитектурная идея

- `config/` отвечает за env, логирование и runtime-настройки.
- `app/` собирает bootstrap приложения.
- `exchange/` будет содержать интеграцию с Bybit, но пока остается пустым каркасом.
- `state/` зарезервирован под локальное нормализованное состояние и синхронизацию.
- `domain/` хранит типы и модели предметной области.
- `services/` станет точкой orchestration-логики над domain/state/exchange.
- `guards/`, `engine/`, `modes/` подготовлены под manual/semi-auto/auto эволюцию без преждевременной реализации.
