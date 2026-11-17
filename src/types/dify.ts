export type VatId = 'F1' | 'C1';

export type VatActionType = 'FILTER' | 'TOPUP' | 'CHANGE';

export interface VatInfo {
  name?: string;
  tpm: number;
  status: string;
  filter_active: boolean;
}

export type VatsMap = Record<string, VatInfo>;

export interface CartItem {
  sku: string;
  name: string;
  qty: number;
}

export interface MenuItem {
  sku: string;
  name: string;
}

export interface MenuSection {
  section: string;
  items: MenuItem[];
}

export interface TimeSlot {
  time: string;
  label: string;
}

export interface DifyStateResponse {
  type: 'state';
  screen: 'start' | 'menu';
  note?: string | null;
  clock: string;
  vats: VatsMap;
  cart: CartItem[];
  cart_count: number;
  min_items: number;
  can_submit: boolean;
  menu: MenuSection[];
  time_slots: TimeSlot[];
  disclaimer?: string | null;
}

export interface OrderLine {
  name: string;
  qty: number;
  family: string | null;
  fried_kg: number;
  basis: string;
}

export interface OrderBreakdown {
  lines: OrderLine[];
  non_fried: string[] | string | null;
  total_fried_kg: number;
}

export interface ResultSlot {
  from: string;
  to: string;
  label: string;
}

export interface ComparisonRow {
  action: string;
  allowed: boolean;
  safe_until: string | null;
  median_rul: string | number;
  oil_l: number | string;
  labor_min: number | string;
  cost_eur: number | string;
  recommended?: boolean;
}

export interface VatResult {
  status: string;
  tpm_before: number;
  delta: number | string;
  tpm_now: number;
  load_vs_usual_pct: number | string;
  capacity_reached?: boolean;
  action_label: string;
  action_time?: string | null;
  measure_again: string;
  rul_median: string | number;
  rul_range: string;
  why: string;
  comparison: ComparisonRow[];
}

export interface DifyResultResponse {
  type: 'result';
  clock: string;
  vats: VatsMap;
  slot: ResultSlot;
  order: OrderBreakdown;
  quiet_window: string | null;
  result: {
    F1?: VatResult;
    C1?: VatResult;
    [key: string]: VatResult | undefined;
  };
  shift_summary?: string | null;
  llm_fallback_used?: boolean;
  disclaimer?: string | null;
}

export type DifyData = DifyStateResponse | DifyResultResponse;

export interface DifyProxyResponse {
  conversation_id: string;
  data: DifyData;
  error?: string;
}
