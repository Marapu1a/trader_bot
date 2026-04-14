# Bybit Trading Controller

TypeScript-приложение, которое выступает как контроллер поверх аккаунта Bybit: хранит локальную проекцию состояния, подготавливает слой проверок и дальнейшую оркестрацию действий, но не реализует стратегию на старте.

Текущий статус: **итерация 1 — каркас и инфраструктура**.

На этом этапе проект:

- поднимает локальное CLI/server-style приложение;
- безопасно загружает конфиг из `.env`;
- инициализирует единый логгер;
- фиксирует стартовую модульную структуру под exchange, state, domain и services;
- содержит минимальный `state`-каркас для локального снимка аккаунта и рынка.

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
      createStateStore.ts
      state.ts
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

`npm run start` перед запуском автоматически собирает проект, чтобы свежий клон стартовал предсказуемо.

## Переменные окружения

Создайте локальный `.env` на основе `.env.example`.

Реальные ключи и секреты должны храниться только в `.env` и не коммитятся в репозиторий.

## Архитектурная идея

- `config/` отвечает за env, логирование и runtime-настройки.
- `app/` собирает bootstrap приложения.
- `exchange/` зарезервирован под интеграцию с Bybit, но пока остается без REST/WS логики.
- `state/` фиксирует основу локального нормализованного состояния и будущей синхронизации с биржей.
- `domain/` хранит предметные срезы, которые будут наполняться по мере развития контроллера.
- `services/` останется слоем orchestration-логики над domain/state/exchange.
- `guards/`, `engine/`, `modes/` подготовлены под manual/semi-auto/auto развитие без преждевременной реализации.
