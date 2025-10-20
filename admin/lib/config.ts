import { randomUUID } from "node:crypto";

const DEFAULT_BASE_URL = "http://localhost:3000";
const DEFAULT_REVIEWER_ID = "admin-service";
const DEFAULT_REVIEWER_NAME = "Admin Service";
const DEFAULT_REVIEWER_EMAIL = "admin@example.com";

export function getAtticusBaseUrl(): string {
  const raw = process.env.ATTICUS_MAIN_BASE_URL ?? DEFAULT_BASE_URL;
  return raw.endsWith("/") ? raw.slice(0, -1) : raw;
}

export function getReviewerIdentity() {
  return {
    id: process.env.ATTICUS_REVIEWER_ID?.trim() || DEFAULT_REVIEWER_ID,
    name: process.env.ATTICUS_REVIEWER_NAME?.trim() || DEFAULT_REVIEWER_NAME,
    email: process.env.ATTICUS_REVIEWER_EMAIL?.trim() || DEFAULT_REVIEWER_EMAIL,
  };
}

export function buildUpstreamHeaders(additional?: HeadersInit): Headers {
  const reviewer = getReviewerIdentity();
  const headers = new Headers(additional);
  headers.set("x-atticus-user-id", reviewer.id);
  headers.set("x-atticus-user-name", reviewer.name);
  headers.set("x-atticus-user-email", reviewer.email);
  headers.set("x-atticus-org-id", "org-atticus");
  const adminToken = process.env.ADMIN_API_TOKEN?.trim();
  if (adminToken) {
    headers.set("x-admin-token", adminToken);
    headers.set("X-Admin-Token", adminToken);
  }
  const requestId = headers.get("x-request-id") ?? randomUUID();
  const traceId = headers.get("x-trace-id") ?? requestId;
  headers.set("x-request-id", requestId);
  headers.set("x-trace-id", traceId);
  return headers;
}
