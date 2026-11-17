import { Check, Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';

interface LoadingOverlayProps {
  visible: boolean;
  command: string | null;
}

const SUBMIT_STEPS = [
  { num: '①', label: 'Recipe parser' },
  { num: '②', label: 'TPM model' },
  { num: '③', label: 'Policy & optimizer' },
  { num: '④', label: 'AI explanation' },
];

export function LoadingOverlay({ visible, command }: LoadingOverlayProps) {
  const [stepIndex, setStepIndex] = useState(0);
  const isSubmit = command === 'SUBMIT';

  useEffect(() => {
    if (!visible || !isSubmit) {
      setStepIndex(0);
      return;
    }

    setStepIndex(0);
    const interval = setInterval(() => {
      setStepIndex((prev) => (prev < SUBMIT_STEPS.length - 1 ? prev + 1 : prev));
    }, 1100);

    return () => clearInterval(interval);
  }, [visible, isSubmit]);

  if (!visible) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-[#27251F]/55 backdrop-blur-xs flex items-center justify-center p-4"
      role="status"
      aria-live="polite"
    >
      {isSubmit ? (
        <div className="bg-white border border-[#E5DDD0] rounded-2xl p-6 sm:p-8 max-w-2xl w-full shadow-xl space-y-6">
          <div className="flex items-center gap-3">
            <Loader2 className="w-7 h-7 animate-spin text-[#D62300] shrink-0" />
            <div>
              <h2 className="font-display font-bold text-xl text-[#27251F]">
                Calculating Oil Quality Forecast
              </h2>
              <p className="text-sm text-[#6B6459]">Running FryWise decision pipeline...</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            {SUBMIT_STEPS.map((step, idx) => {
              const isDone = idx < stepIndex;
              const isActive = idx === stepIndex;

              return (
                <div
                  key={step.label}
                  className={`rounded-2xl border p-4 flex flex-col gap-2 transition-all ${
                    isActive
                      ? 'bg-[#FFC72C]/25 border-[#FFC72C] text-[#27251F]'
                      : isDone
                        ? 'bg-[#E9F7EF] border-[#2E9E5B] text-[#1E7A44]'
                        : 'bg-[#FFF8E7] border-[#E5DDD0] text-[#6B6459]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-display font-bold text-lg">{step.num}</span>
                    {isDone && <Check className="w-4 h-4 text-[#2E9E5B]" />}
                    {isActive && <Loader2 className="w-4 h-4 animate-spin text-[#D62300]" />}
                  </div>
                  <span className="font-semibold text-sm leading-snug">{step.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="bg-white border border-[#E5DDD0] rounded-2xl px-8 py-6 shadow-xl flex items-center gap-4">
          <Loader2 className="w-7 h-7 animate-spin text-[#D62300]" />
          <span className="font-display font-semibold text-lg text-[#27251F]">
            Syncing with FryWise...
          </span>
        </div>
      )}
    </div>
  );
}
