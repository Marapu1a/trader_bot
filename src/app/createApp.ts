import { env } from "../config/env.js";
import { createLogger } from "../config/logger.js";
import { createRuntimeContext } from "../modes/runtimeMode.js";
import { createStateStore } from "../state/store/createStateStore.js";

export interface App {
  start: () => Promise<void>;
}

export function createApp(): App {
  const logger = createLogger(env.LOG_LEVEL);
  const runtime = createRuntimeContext();
  const stateStore = createStateStore();

  return {
    start() {
      logger.info(
        {
          mode: runtime.mode,
          exchange: runtime.exchange,
          testnet: env.BYBIT_TESTNET,
          stateRevision: stateStore.getSnapshot().meta.revision,
        },
        "Application started",
      );

      return Promise.resolve();
    },
  };
}
