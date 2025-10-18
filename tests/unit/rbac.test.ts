import { describe, expect, it } from "vitest";
import { Role } from "@prisma/client";
import {
  canEditGlossary,
  canReviewGlossary,
  ensureRole,
  requireUser,
  ForbiddenError,
  UnauthorizedError,
} from "@/lib/rbac";
import type { RequestUser } from "@/lib/request-context";

const baseUser: RequestUser = {
  id: "user-1",
  role: Role.ADMIN,
  orgId: "org-1",
  email: "admin@example.com",
  name: "Admin",
};

describe("RBAC helpers", () => {
  it("requires a user context", () => {
    expect(() => requireUser(null)).toThrow(UnauthorizedError);
    expect(requireUser(baseUser)).toBe(baseUser);
  });

  it("checks allowed roles", () => {
    expect(ensureRole(baseUser, [Role.ADMIN, Role.REVIEWER])).toBe(baseUser);
    const userContext: RequestUser = {
      ...baseUser,
      role: Role.USER,
    };
    expect(() => ensureRole(userContext, [Role.ADMIN])).toThrow(ForbiddenError);
  });

  it("allows reviewers to view glossary but not edit", () => {
    const reviewerContext: RequestUser = {
      ...baseUser,
      role: Role.REVIEWER,
    };
    expect(canReviewGlossary(reviewerContext)).toBe(reviewerContext);
    expect(() => canEditGlossary(reviewerContext)).toThrow(ForbiddenError);
  });

  it("allows admins to edit glossary", () => {
    expect(canEditGlossary(baseUser)).toBe(baseUser);
  });
});
