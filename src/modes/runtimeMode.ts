export type RuntimeMode = "manual" | "semi-auto" | "auto";

export interface RuntimeContext {
  exchange: "bybit";
  mode: RuntimeMode;
}

export function createRuntimeContext(): RuntimeContext {
  return {
    exchange: "bybit",
    mode: "manual",
  };
}
