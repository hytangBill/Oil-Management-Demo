export type StatusLevel = 'green' | 'amber' | 'red';

export interface StatusPalette {
  level: StatusLevel;
  label: string;
  hex: string;
  pillBgClass: string;
  pillBorderClass: string;
  bannerBgClass: string;
  bannerBorderClass: string;
  bannerTextClass: string;
}

export function resolveStatusPalette(rawStatus?: string | null): StatusPalette {
  const s = (rawStatus || '').trim();
  const lower = s.toLowerCase();

  if (
    lower.includes('red') ||
    lower.includes('crit') ||
    lower.includes('change') ||
    lower.includes('discard') ||
    lower.includes('danger') ||
    lower.includes('exceed')
  ) {
    return {
      level: 'red',
      label: s || 'CRITICAL',
      hex: '#C8102E',
      pillBgClass: 'bg-[#C8102E] text-white',
      pillBorderClass: 'border-white/80 pulse-red-border',
      bannerBgClass: 'bg-[#FDECEF]',
      bannerBorderClass: 'border-[#C8102E]',
      bannerTextClass: 'text-[#C8102E]',
    };
  }

  if (
    lower.includes('amber') ||
    lower.includes('warn') ||
    lower.includes('caution') ||
    lower.includes('filter') ||
    lower.includes('soon') ||
    lower.includes('yellow')
  ) {
    return {
      level: 'amber',
      label: s || 'WARNING',
      hex: '#F28C00',
      pillBgClass: 'bg-[#F28C00] text-white',
      pillBorderClass: 'border-white/50',
      bannerBgClass: 'bg-[#FFF4E0]',
      bannerBorderClass: 'border-[#F28C00]',
      bannerTextClass: 'text-[#B56500]',
    };
  }

  return {
    level: 'green',
    label: s || 'OK',
    hex: '#2E9E5B',
    pillBgClass: 'bg-[#2E9E5B] text-white',
    pillBorderClass: 'border-white/40',
    bannerBgClass: 'bg-[#E9F7EF]',
    bannerBorderClass: 'border-[#2E9E5B]',
    bannerTextClass: 'text-[#1E7A44]',
  };
}

export function formatSignedPct(val: number | string | null | undefined): string {
  if (val === null || val === undefined || val === '') return '—';
  if (typeof val === 'number') {
    const prefix = val > 0 ? '+' : '';
    return `${prefix}${val}`;
  }
  const trimmed = String(val).trim();
  if (trimmed.startsWith('+') || trimmed.startsWith('-')) return trimmed;
  return `+${trimmed}`;
}
