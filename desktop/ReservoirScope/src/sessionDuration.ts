export interface SessionDurationParts { hours: string; minutes: string; seconds: string }

/** Display only: fractional elapsed seconds remain available in exact measurements. */
export function formatSessionDuration(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return 'Unavailable';
  let remaining = Math.floor(seconds);
  const hours = Math.floor(remaining / 3600); remaining %= 3600;
  const minutes = Math.floor(remaining / 60), wholeSeconds = remaining % 60;
  return [[hours, 'hour'], [minutes, 'minute'], [wholeSeconds, 'second']]
    .filter(([value]) => Number(value) > 0)
    .map(([value, unit]) => `${value} ${unit}${value === 1 ? '' : 's'}`)
    .join(' ') || '0 seconds';
}

export function splitSessionDuration(seconds: number): SessionDurationParts {
  if (!Number.isInteger(seconds) || seconds < 1 || seconds > 86400) return { hours: '', minutes: '', seconds: '' };
  return { hours: String(Math.floor(seconds / 3600)), minutes: String(Math.floor(seconds / 60) % 60), seconds: String(seconds % 60) };
}

/** Invalid drafts are rejected, never rounded, clamped or normalized into another duration. */
export function parseSessionDuration(parts: SessionDurationParts): number | null {
  const values = [parts.hours, parts.minutes, parts.seconds];
  if (values.some(value => !/^[0-9]{1,2}$/.test(value))) return null;
  const [hours, minutes, seconds] = values.map(Number);
  if (hours > 24 || minutes > 59 || seconds > 59) return null;
  const total = hours * 3600 + minutes * 60 + seconds;
  return total >= 1 && total <= 86400 ? total : null;
}
