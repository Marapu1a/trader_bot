export interface BalanceSnapshot {
  asset: string;
  total: number;
  available: number;
}

export interface PositionSnapshot {
  symbol: string;
  side: "long" | "short";
  size: number;
}

export interface OrderSnapshot {
  id: string;
  symbol: string;
  status: "new" | "partially-filled" | "filled" | "cancelled" | "rejected";
}

export interface InstrumentSnapshot {
  symbol: string;
  status: "active" | "inactive";
}
