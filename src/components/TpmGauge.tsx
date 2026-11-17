interface TpmGaugeProps {
  tpmBefore: number;
  tpmNow: number;
}

const CX = 150;
const CY = 138;
const R = 102;
const MAX_TPM = 30;

function valueToPoint(value: number, radius: number) {
  const clamped = Math.max(0, Math.min(MAX_TPM, Number(value) || 0));
  const deg = 180 - (clamped / MAX_TPM) * 180;
  const rad = (deg * Math.PI) / 180;
  return {
    x: CX + radius * Math.cos(rad),
    y: CY - radius * Math.sin(rad),
  };
}

function describeArc(startVal: number, endVal: number, radius: number): string {
  const start = valueToPoint(startVal, radius);
  const end = valueToPoint(endVal, radius);
  // Sweep clockwise along top semicircle
  return `M ${start.x.toFixed(2)} ${start.y.toFixed(2)} A ${radius} ${radius} 0 0 1 ${end.x.toFixed(2)} ${end.y.toFixed(2)}`;
}

export function TpmGauge({ tpmBefore, tpmNow }: TpmGaugeProps) {
  const greenArc = describeArc(0, 21, R);
  const amberArc = describeArc(21, 24, R);
  const redArc = describeArc(24, 30, R);

  const ghostTip = valueToPoint(tpmBefore, R - 14);
  const nowTip = valueToPoint(tpmNow, R - 10);

  const ticks = [0, 21, 24, 30];

  return (
    <div className="flex flex-col items-center">
      <svg
        viewBox="0 0 300 170"
        className="w-full max-w-[300px] h-auto overflow-visible"
        role="img"
        aria-label={`TPM gauge showing before ${tpmBefore}% and now ${tpmNow}%`}
      >
        {/* Colored Zone Arcs: Green <21, Amber 21-24, Red >=24 */}
        <path d={greenArc} fill="none" stroke="#2E9E5B" strokeWidth="18" strokeLinecap="butt" />
        <path d={amberArc} fill="none" stroke="#F28C00" strokeWidth="18" strokeLinecap="butt" />
        <path d={redArc} fill="none" stroke="#C8102E" strokeWidth="18" strokeLinecap="butt" />

        {/* Tick labels */}
        {ticks.map((t) => {
          const outer = valueToPoint(t, R + 22);
          const inner = valueToPoint(t, R + 9);
          const tickEnd = valueToPoint(t, R - 9);
          return (
            <g key={t}>
              <line
                x1={tickEnd.x}
                y1={tickEnd.y}
                x2={inner.x}
                y2={inner.y}
                stroke="#FFF8E7"
                strokeWidth="2"
              />
              <text
                x={outer.x}
                y={outer.y}
                textAnchor="middle"
                dominantBaseline="middle"
                className="fill-[#6B6459] text-[11px] font-semibold tabular-nums"
              >
                {t}%
              </text>
            </g>
          );
        })}

        {/* Ghost Needle (tpm_before) */}
        <line
          x1={CX}
          y1={CY}
          x2={ghostTip.x}
          y2={ghostTip.y}
          stroke="#9E9589"
          strokeWidth="3"
          strokeDasharray="5 4"
          strokeLinecap="round"
        />
        <circle cx={ghostTip.x} cy={ghostTip.y} r="4" fill="#9E9589" opacity="0.75" />

        {/* Current Needle (tpm_now) */}
        <line
          x1={CX}
          y1={CY}
          x2={nowTip.x}
          y2={nowTip.y}
          stroke="#27251F"
          strokeWidth="4.5"
          strokeLinecap="round"
        />
        <circle cx={CX} cy={CY} r="9" fill="#27251F" />
        <circle cx={CX} cy={CY} r="4" fill="#FFC72C" />
      </svg>

      <div className="flex items-center gap-5 text-xs text-[#6B6459] -mt-2">
        <span className="inline-flex items-center gap-1.5">
          <span className="w-4 border-t-2 border-dashed border-[#9E9589] inline-block" />
          <span>Before ({tpmBefore} %)</span>
        </span>
        <span className="inline-flex items-center gap-1.5 font-semibold text-[#27251F]">
          <span className="w-4 border-t-[3px] border-[#27251F] inline-block" />
          <span>Now ({tpmNow} %)</span>
        </span>
      </div>
    </div>
  );
}
