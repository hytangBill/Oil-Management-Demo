import { Clock, Info } from 'lucide-react';
import type { DifyStateResponse } from '../types/dify';

interface StartScreenProps {
  data: DifyStateResponse;
  isLoading: boolean;
  onCommand: (cmd: string) => void;
}

export function StartScreen({ data, isLoading, onCommand }: StartScreenProps) {
  return (
    <div className="max-w-[1440px] mx-auto px-4 sm:px-6 py-6 space-y-6">
      {data.note && (
        <div className="bg-white border border-[#E5DDD0] rounded-2xl px-5 py-4 flex items-start gap-3 text-[#27251F]">
          <Info className="w-5 h-5 text-[#D62300] shrink-0 mt-0.5" />
          <p className="text-base font-medium leading-relaxed">{data.note}</p>
        </div>
      )}

      <section className="space-y-4">
        <h1 className="font-display font-bold text-2xl sm:text-3xl text-[#27251F]">
          Select Time Slot
        </h1>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {(data.time_slots || []).map((slot) => {
            const isSelected = data.clock === slot.time;

            return (
              <button
                key={slot.time}
                type="button"
                disabled={isLoading}
                onClick={() => onCommand(`TIME:${slot.time}`)}
                className={`min-h-[112px] p-6 rounded-2xl border-2 text-left transition-all cursor-pointer active:scale-[0.98] flex flex-col justify-between gap-3 disabled:opacity-50 ${
                  isSelected
                    ? 'bg-[#FFC72C]/25 border-[#FFC72C] text-[#27251F]'
                    : 'bg-white border-[#E5DDD0] hover:border-[#FFC72C] text-[#27251F]'
                }`}
              >
                <div className="flex items-center justify-between gap-2 w-full">
                  <span className="inline-flex items-center gap-2 font-display font-extrabold text-2xl tabular-nums text-[#D62300]">
                    <Clock className="w-5 h-5" />
                    <span>{slot.time}</span>
                  </span>
                  {isSelected && (
                    <span className="px-2.5 py-1 rounded-lg bg-[#FFC72C] text-[#27251F] text-xs font-bold">
                      Active
                    </span>
                  )}
                </div>
                <span className="font-display font-bold text-lg text-[#27251F]">
                  {slot.label}
                </span>
              </button>
            );
          })}
        </div>
      </section>
    </div>
  );
}
