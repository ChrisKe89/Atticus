const timestampFormatter = new Intl.DateTimeFormat("en-GB", {
  timeZone: "UTC",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: false,
});

export function formatTimestamp(
  iso: string | null | undefined,
  fallback: string = "Unknown timestamp"
): string {
  if (!iso) {
    return fallback;
  }
  try {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) {
      return iso;
    }
    return timestampFormatter.format(date).replace(",", "");
  } catch {
    return iso;
  }
}

