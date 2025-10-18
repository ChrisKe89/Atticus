import type { ReviewChat } from "./types";
import { buildUpstreamHeaders, getAtticusBaseUrl } from "./config";

function mergeHeaders(base: Headers, extra?: HeadersInit): Headers {
  if (!extra) {
    return base;
  }
  const merged = new Headers(base);
  const temp = new Headers(extra);
  temp.forEach((value, key) => merged.set(key, value));
  return merged;
}

export async function atticusFetch(
  path: string,
  init: RequestInit = {}
): Promise<Response> {
  const target = path.startsWith("/") ? path : `/${path}`;
  const headers = mergeHeaders(buildUpstreamHeaders(), init.headers);
  return fetch(`${getAtticusBaseUrl()}${target}`, {
    ...init,
    headers,
    cache: "no-store",
  });
}

export async function fetchReviewQueue(): Promise<ReviewChat[]> {
  const response = await atticusFetch("/api/admin/uncertain");
  if (!response.ok) {
    throw new Error(`Upstream returned ${response.status} while loading review queue.`);
  }
  const data = (await response.json()) as unknown;
  if (!Array.isArray(data)) {
    throw new Error("Unexpected response when loading review queue.");
  }
  return data as ReviewChat[];
}
