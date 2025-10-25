export function createId(prefix?: string): string {
  const base = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
  return prefix ? `${prefix}-${base}` : base;
}
