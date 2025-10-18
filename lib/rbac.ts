import { Role } from "@prisma/client";
import type { RequestUser } from "@/lib/request-context";

export class ForbiddenError extends Error {
  constructor(message = "Forbidden") {
    super(message);
    this.name = "ForbiddenError";
  }
}

export class UnauthorizedError extends Error {
  constructor(message = "Unauthorized") {
    super(message);
    this.name = "UnauthorizedError";
  }
}

export function requireUser(user: RequestUser | null | undefined): RequestUser {
  if (!user?.id) {
    throw new UnauthorizedError();
  }
  return user;
}

export function ensureRole(user: RequestUser | null | undefined, allowed: Role[]): RequestUser {
  const activeUser = requireUser(user);
  if (!allowed.includes(activeUser.role)) {
    throw new ForbiddenError("Insufficient role");
  }
  return activeUser;
}

export function canReviewGlossary(user: RequestUser | null | undefined): RequestUser {
  return ensureRole(user, [Role.ADMIN, Role.REVIEWER]);
}

export function canEditGlossary(user: RequestUser | null | undefined): RequestUser {
  return ensureRole(user, [Role.ADMIN]);
}
