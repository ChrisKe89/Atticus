import { headers } from "next/headers";

export type RequestUser = {
  id: string;
  orgId: string;
  email: string | null;
  name: string | null;
};

export type RequestContext = {
  user: RequestUser;
};

function normalize(value: string | null): string | null {
  if (value === null || value === undefined) {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

const FALLBACK_USER_ID = "upstream-user";
const FALLBACK_ORG_ID = "org-atticus";

export function getRequestContext(): RequestContext {
  const headerBag = headers();

  const userId = normalize(headerBag.get("x-atticus-user-id")) ?? FALLBACK_USER_ID;
  const orgId = normalize(headerBag.get("x-atticus-org-id")) ?? FALLBACK_ORG_ID;
  const email = normalize(headerBag.get("x-atticus-user-email"));
  const name = normalize(headerBag.get("x-atticus-user-name"));

  return {
    user: {
      id: userId,
      orgId,
      email,
      name,
    },
  };
}

export function getRequestUser(): RequestUser {
  return getRequestContext().user;
}
