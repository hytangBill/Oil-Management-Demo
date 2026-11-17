import {
  ChevronDown,
  ChevronUp,
  Clock,
  MessageSquare,
  Sparkles,
} from 'lucide-react';
import { useState } from 'react';
import type { DifyResultResponse, VatResult } from '../types/dify';
import { formatSignedPct, resolveStatusPalette } from '../utils/statusStyles';
import { OperatorActionsBar } from './OperatorActionsBar';
import { TpmGauge } from './TpmGauge';

interface ResultScreenProps {
  data: DifyResultResponse;
  isLoading: boolean;
  onCommand: (cmd: string) => void;
}

function getSlotBadgeStyle(label?: string): string {
  const upper = (label || '').trim().toUpperCase();
  if (upper.includes('PEAK')) {
    return 'bg-[#C8102E] text-white';
  }
  if (upper.includes('QUIET')) {
    return 'bg-[#FFC72C] text-[#27251F]';
  }
  return 'bg-[#E7E2D8] text-[#27251F]';
}

function formatFamilyLabel(family: string | null | undefined): string {
  if (!family) return 'No fryer';
  const lower = family.trim().toLowerCase();
  if (lower === 'fries') return 'Fries vat';
  if (lower === 'chicken') return 'Chicken vat';
  return family;
}

function formatNonFriedList(nonFried: DifyResultResponse['order']['non_fried']): string {
  if (!nonFried) return 'None';
  if (Array.isArray(nonFried)) {
    return nonFried.length > 0 ? nonFried.join(', ') : 'None';
  }
  return String(nonFried);
}

function VatResultCard({
  vatKey,
  vatName,
  res,
}: {
  vatKey: string;
  vatName?: string;
  res: VatResult;
}) {
  const [compareOpen, setCompareOpen] = useState(false);
  const palette = resolveStatusPalette(res.status);
  const loadSign = formatSignedPct(res.load_vs_usual_pct);
  const deltaSign = formatSignedPct(res.delta);

  return (
    <div className="bg-white border border-[#E5DDD0] rounded-2xl p-5 sm:p-6 flex flex-col gap-5">
      <div className="flex items-center justify-between gap-3">
        <h2 className="font-display font-bold text-xl sm:text-2xl text-[#27251F]">
          {vatName ? `${vatKey} — ${vatName}` : vatKey}
        </h2>
        <span
          className={`px-3 py-1 rounded-xl text-xs font-bold uppercase tracking-wide ${palette.pillBgClass}`}
        >
          {palette.label}
        </span>
      </div>

      {/* Semicircle Gauge 0-30% */}
      <TpmGauge tpmBefore={res.tpm_before} tpmNow={res.tpm_now} />

      {/* Summary & Load vs Usual */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-[#FFF8E7] border border-[#E5DDD0] rounded-2xl p-4">
        <div className="font-display font-bold text-lg text-[#27251F] tabular-nums">
          {res.tpm_before} % → {res.tpm_now} % ({deltaSign})
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="px-3 py-1 rounded-xl bg-white border border-[#D8CFC0] text-xs font-semibold text-[#27251F] tabular-nums">
            Load vs usual: {loadSign} %
          </span>
          {res.capacity_reached && (
            <span className="px-3 py-1 rounded-xl bg-[#C8102E] text-white text-xs font-bold">
              capacity reached
            </span>
          )}
        </div>
      </div>

      {/* Coloured Action Banner */}
      <div className={`rounded-2xl border-2 p-4 space-y-2.5 ${palette.bannerBgClass} ${palette.bannerBorderClass}`}>
        <div className={`font-display font-extrabold text-lg sm:text-xl ${palette.bannerTextClass}`}>
          {res.action_label}
        </div>

        <div className="space-y-1 text-sm text-[#27251F]">
          {res.action_time !== null && res.action_time !== undefined && res.action_time !== '' && (
            <div className="flex justify-between gap-3">
              <span className="text-[#6B6459] font-medium">When</span>
              <span className="font-semibold text-right">{res.action_time}</span>
            </div>
          )}
          <div className="flex justify-between gap-3">
            <span className="text-[#6B6459] font-medium">Measure again</span>
            <span className="font-semibold tabular-nums text-right">{res.measure_again}</span>
          </div>
          <div className="flex justify-between gap-3">
            <span className="text-[#6B6459] font-medium">Remaining useful life</span>
            <span className="font-semibold tabular-nums text-right">
              median {res.rul_median} (range {res.rul_range})
            </span>
          </div>
        </div>
      </div>

      {/* Why Speech Bubble labelled "AI explanation" */}
      {res.why && (
        <div className="relative bg-[#FFF8E7] border border-[#E5DDD0] rounded-2xl p-4 space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-[#D62300]">
            <MessageSquare className="w-3.5 h-3.5" />
            <span>AI explanation</span>
          </div>
          <p className="text-sm text-[#27251F] leading-relaxed">{res.why}</p>
        </div>
      )}

      {/* Collapsible Compare Actions Table */}
      {Array.isArray(res.comparison) && res.comparison.length > 0 && (
        <div className="border border-[#E5DDD0] rounded-2xl overflow-hidden">
          <button
            type="button"
            onClick={() => setCompareOpen((prev) => !prev)}
            className="w-full min-h-[56px] px-4 py-3 bg-[#FFF8E7] hover:bg-[#F3EDE3] flex items-center justify-between gap-3 text-left font-display font-bold text-sm text-[#27251F] cursor-pointer"
          >
            <span>Compare actions</span>
            {compareOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>

          {compareOpen && (
            <div className="overflow-x-auto border-t border-[#E5DDD0]">
              <table className="w-full text-left border-collapse text-xs sm:text-sm">
                <thead className="bg-[#F9F3E9] text-[#6B6459]">
                  <tr>
                    <th className="py-2.5 px-3 font-semibold">Action</th>
                    <th className="py-2.5 px-3 font-semibold text-center">Allowed</th>
                    <th className="py-2.5 px-3 font-semibold">Safe until</th>
                    <th className="py-2.5 px-3 font-semibold text-right">Median RUL</th>
                    <th className="py-2.5 px-3 font-semibold text-right">Oil (L)</th>
                    <th className="py-2.5 px-3 font-semibold text-right">Labor (min)</th>
                    <th className="py-2.5 px-3 font-semibold text-right">Cost (€)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F3EDE3]">
                  {res.comparison.map((row, idx) => (
                    <tr
                      key={`${row.action}-${idx}`}
                      className={row.recommended ? 'bg-[#FFE8A3] font-semibold' : 'bg-white'}
                    >
                      <td className="py-2.5 px-3 text-[#27251F]">{row.action}</td>
                      <td className="py-2.5 px-3 text-center font-bold">
                        {row.allowed ? (
                          <span className="text-[#2E9E5B]">✓</span>
                        ) : (
                          <span className="text-[#C8102E]">✗</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 tabular-nums text-[#27251F]">
                        {row.safe_until ?? '—'}
                      </td>
                      <td className="py-2.5 px-3 text-right tabular-nums text-[#27251F]">
                        {row.median_rul}
                      </td>
                      <td className="py-2.5 px-3 text-right tabular-nums text-[#27251F]">
                        {row.oil_l}
                      </td>
                      <td className="py-2.5 px-3 text-right tabular-nums text-[#27251F]">
                        {row.labor_min}
                      </td>
                      <td className="py-2.5 px-3 text-right tabular-nums text-[#27251F]">
                        €{row.cost_eur}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ResultScreen({ data, isLoading, onCommand }: ResultScreenProps) {
  const f1Result = data.result?.F1;
  const c1Result = data.result?.C1;

  return (
    <div className="max-w-[1440px] mx-auto px-4 sm:px-6 py-6 space-y-6">
      {/* Card: Order processed */}
      <section className="bg-white border border-[#E5DDD0] rounded-2xl p-5 sm:p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-display font-bold text-xl sm:text-2xl text-[#27251F]">
              Order processed
            </h1>
            {data.slot && (
              <span className="inline-flex items-center gap-1.5 font-semibold text-base tabular-nums text-[#27251F]">
                <Clock className="w-4 h-4 text-[#6B6459]" />
                <span>
                  {data.slot.from} – {data.slot.to}
                </span>
              </span>
            )}
            {data.slot?.label && (
              <span
                className={`px-3 py-1 rounded-xl text-xs font-bold uppercase tracking-wide ${getSlotBadgeStyle(
                  data.slot.label
                )}`}
              >
                {data.slot.label}
              </span>
            )}
          </div>

          <button
            type="button"
            disabled={isLoading}
            onClick={() => onCommand('MENU')}
            className="min-h-[56px] px-6 py-3 rounded-2xl bg-[#D62300] hover:bg-[#B81D00] text-white font-display font-bold text-base cursor-pointer active:scale-[0.98] whitespace-nowrap disabled:opacity-50"
          >
            Next order
          </button>
        </div>

        {data.order && (
          <div className="space-y-3">
            <div className="border border-[#E5DDD0] rounded-2xl overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead className="bg-[#FFF8E7] text-[#6B6459] text-xs">
                  <tr>
                    <th className="py-3 px-4 font-semibold">Item</th>
                    <th className="py-3 px-4 font-semibold text-right">Qty</th>
                    <th className="py-3 px-4 font-semibold">Fryer</th>
                    <th className="py-3 px-4 font-semibold text-right">Fried kg</th>
                    <th className="py-3 px-4 font-semibold">Basis</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F3EDE3]">
                  {(data.order.lines || []).map((line, idx) => (
                    <tr key={`${line.name}-${idx}`}>
                      <td className="py-3 px-4 font-semibold text-[#27251F]">{line.name}</td>
                      <td className="py-3 px-4 text-right tabular-nums text-[#27251F]">
                        {line.qty}
                      </td>
                      <td className="py-3 px-4 text-[#27251F]">
                        {formatFamilyLabel(line.family)}
                      </td>
                      <td className="py-3 px-4 text-right font-semibold tabular-nums text-[#27251F]">
                        {line.fried_kg}
                      </td>
                      <td className="py-3 px-4 text-[#6B6459]">{line.basis}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 text-sm px-1">
              <span className="text-[#6B6459]">
                Filtered out — no fryer load: {formatNonFriedList(data.order.non_fried)}
              </span>
              <span className="font-display font-bold text-base text-[#27251F] tabular-nums">
                Total: {data.order.total_fried_kg} kg
              </span>
            </div>
          </div>
        )}
      </section>

      {/* Two Vat Cards Side by Side */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {f1Result && (
          <VatResultCard vatKey="F1" vatName={data.vats?.F1?.name} res={f1Result} />
        )}
        {c1Result && (
          <VatResultCard vatKey="C1" vatName={data.vats?.C1?.name} res={c1Result} />
        )}
      </section>

      {/* Quiet Window, Shift Summary & LLM Fallback Note */}
      <section className="bg-white border border-[#E5DDD0] rounded-2xl p-5 sm:p-6 space-y-3">
        {data.quiet_window && (
          <div className="flex items-center gap-2 font-display font-bold text-base text-[#27251F]">
            <Sparkles className="w-5 h-5 text-[#FFC72C] shrink-0" />
            <span>Next quiet window: {data.quiet_window}</span>
          </div>
        )}

        {data.shift_summary && (
          <p className="text-sm sm:text-base text-[#27251F] leading-relaxed">
            {data.shift_summary}
          </p>
        )}

        {data.llm_fallback_used && (
          <p className="text-xs text-[#6B6459]">Standard explanation used</p>
        )}

        <div className="pt-2">
          <button
            type="button"
            disabled={isLoading}
            onClick={() => onCommand('MENU')}
            className="min-h-[56px] px-8 py-3 rounded-2xl bg-[#D62300] hover:bg-[#B81D00] text-white font-display font-bold text-lg cursor-pointer active:scale-[0.98] disabled:opacity-50"
          >
            Next order
          </button>
        </div>
      </section>

      {/* Operator Action Buttons */}
      <OperatorActionsBar vats={data.vats} isLoading={isLoading} onCommand={onCommand} />
    </div>
  );
}
