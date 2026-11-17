import { Droplets, Filter, RefreshCw } from 'lucide-react';
import type { VatActionType, VatId, VatsMap } from '../types/dify';

interface OperatorActionsBarProps {
  vats?: VatsMap;
  isLoading: boolean;
  onCommand: (cmd: string) => void;
}

const VAT_IDS: VatId[] = ['F1', 'C1'];

const ACTIONS: Array<{ action: VatActionType; label: string; icon: typeof Filter }> = [
  { action: 'FILTER', label: 'Filtered', icon: Filter },
  { action: 'TOPUP', label: '+2 L top-up', icon: Droplets },
  { action: 'CHANGE', label: 'Oil changed', icon: RefreshCw },
];

export function OperatorActionsBar({ vats, isLoading, onCommand }: OperatorActionsBarProps) {
  const keysToRender: string[] = vats
    ? Object.keys(vats)
    : VAT_IDS;

  return (
    <section className="bg-white border border-[#E5DDD0] rounded-2xl p-5 space-y-4">
      <h2 className="font-display font-bold text-lg text-[#27251F]">Operator actions</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {keysToRender.map((vatKey) => {
          const vat = vats?.[vatKey];
          const title = vat?.name ? `${vatKey} — ${vat.name}` : vatKey;

          return (
            <div
              key={vatKey}
              className="bg-[#FFF8E7] border border-[#E5DDD0] rounded-2xl p-4 space-y-3"
            >
              <div className="font-display font-bold text-sm text-[#27251F]">{title}</div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {ACTIONS.map(({ action, label, icon: Icon }) => (
                  <button
                    key={action}
                    type="button"
                    disabled={isLoading}
                    onClick={() => onCommand(`ACT:${vatKey}:${action}`)}
                    className="min-h-[56px] px-3 py-2.5 rounded-2xl bg-white hover:bg-[#FFC72C]/35 border border-[#D8CFC0] text-[#27251F] font-semibold text-sm flex items-center justify-center gap-2 transition-colors active:scale-[0.98] cursor-pointer whitespace-nowrap disabled:opacity-50"
                  >
                    <Icon className="w-4 h-4 text-[#D62300] shrink-0" />
                    <span>{label}</span>
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
