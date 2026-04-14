import pino, { type LevelWithSilent, type Logger } from "pino";

export function createLogger(level: LevelWithSilent): Logger {
  const isDevelopment = process.env.NODE_ENV !== "production";

  return pino({
    level,
    ...(isDevelopment
      ? {
          transport: {
            target: "pino-pretty",
            options: {
              colorize: true,
              translateTime: "SYS:standard",
            },
          },
        }
      : {}),
  });
}
