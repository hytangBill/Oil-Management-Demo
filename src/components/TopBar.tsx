import { Clock, Filter, RotateCcw } from 'lucide-react';
import type { VatsMap } from '../types/dify';
import { resolveStatusPalette } from '../utils/statusStyles';

interface TopBarProps {
  clock?: string;
  vats?: VatsMap;
  disclaimer?: string | null;
  isLoading: boolean;
  onReset: () => void;
}

export function TopBar({ clock, vats, disclaimer, isLoading, onReset }: TopBarProps) {
  const vatEntries = vats ? Object.entries(vats) : [];

  return (
    <div className="sticky top-0 z-30">
      <header className="bg-[#D62300] text-white shadow-sm">
        <div className="max-w-[1440px] mx-auto px-4 sm:px-6 min-h-[76px] py-2 flex flex-wrap items-center justify-between gap-3">
          {/* Left: Brand Name + Reset */}
          <div className="flex items-center gap-4">
            <span className="font-display font-extrabold text-2xl sm:text-[28px] tracking-tight whitespace-nowrap">
              FryWise
            </span>

            <button
              type="button"
              disabled={isLoading}
              onClick={onReset}
              className="min-h-[56px] px-4 py-2 rounded-2xl bg-white/15 hover:bg-white/25 active:scale-[0.98] text-white font-semibold text-sm flex items-center gap-2 transition-colors whitespace-nowrap shrink-0 cursor-pointer disabled:opacity-50"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Reset</span>
            </button>
          </div>

          {/* Right: Clock Pill + Vat TPM Pills */}
          <div className="flex flex-wrap items-center gap-2.5 sm:gap-3">
            {clock && (
              <div className="min-h-[56px] px-4 rounded-2xl bg-white/15 border border-white/25 flex items-center gap-2 shrink-0">
                <Clock className="w-4 h-4 text-[#FFC72C]" />
                <span className="font-semibold text-base sm:text-lg tabular-nums whitespace-nowrap">
                  {clock}
                </span>
              </div>
            )}

            {vatEntries.map(([vatKey, vat]) => {
              if (!vat) return null;
              const palette = resolveStatusPalette(vat.status);

              return (
                <div
                  key={vatKey}
                  className={`min-h-[56px] px-4 rounded-2xl border-2 flex items-center gap-2.5 shrink-0 ${palette.pillBgClass} ${palette.pillBorderClass}`}
                >
                  <span className="font-display font-bold text-base tabular-nums whitespace-nowrap">
                    {vatKey} {vat.tpm} %
                  </span>
                  <span className="text-xs font-bold uppercase tracking-wide bg-black/15 px-2 py-0.5 rounded-lg whitespace-nowrap">
                    {palette.label}
                  </span>
                  {vat.filter_active && (
                    <span
                      className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-white/20"
                      title="Filter active"
                    >
                      <Filter className="w-3.5 h-3.5" />
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </header>

      {/* Thin yellow banner under header */}
      {disclaimer && (
        <div className="bg-[#FFC72C] text-[#27251F] border-b border-[#E2AD1A]">
          <div className="max-w-[1440px] mx-auto px-4 sm:px-6 py-1.5 text-xs sm:text-sm font-medium text-center">
            {disclaimer}
          </div>
        </div>
      )}
    </div>
  );
}
