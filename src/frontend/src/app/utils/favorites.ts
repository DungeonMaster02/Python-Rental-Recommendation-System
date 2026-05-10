const FAVORITES_KEY = 'usc_housing_favorites_v1';

export function readFavoriteIds(): number[] {
  if (typeof window === 'undefined') {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(FAVORITES_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .map((value) => Number(value))
      .filter((value) => Number.isFinite(value) && value > 0)
      .map((value) => Math.trunc(value));
  } catch {
    return [];
  }
}

export function writeFavoriteIds(ids: Iterable<number>): void {
  if (typeof window === 'undefined') {
    return;
  }
  const normalized = Array.from(new Set(Array.from(ids).map((id) => Math.trunc(id)))).filter((id) => id > 0);
  window.localStorage.setItem(FAVORITES_KEY, JSON.stringify(normalized));
}
