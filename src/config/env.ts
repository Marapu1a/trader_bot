import dotenv from "dotenv";
import { z } from "zod";

dotenv.config();

const envSchema = z.object({
  BYBIT_API_KEY: z.string().trim().default(""),
  BYBIT_API_SECRET: z.string().trim().default(""),
  BYBIT_TESTNET: z
    .enum(["true", "false"])
    .default("false")
    .transform((value) => value === "true"),
  LOG_LEVEL: z.enum(["fatal", "error", "warn", "info", "debug", "trace", "silent"]).default("info"),
});

const parsedEnv = envSchema.safeParse(process.env);

if (!parsedEnv.success) {
  throw new Error(`Invalid environment configuration: ${parsedEnv.error.message}`);
}

export const env = parsedEnv.data;

export type Env = typeof env;
