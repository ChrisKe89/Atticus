import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";
import type { NextRequestWithAuth } from "next-auth/middleware";

function hasSessionCookie(req: NextRequestWithAuth): boolean {
  // Database session strategy uses a non-JWT cookie; allow it here.
  const names = [
    "next-auth.session-token",
    "__Secure-next-auth.session-token",
  ];
  return names.some((n) => Boolean(req.cookies.get(n)?.value));
}

export default withAuth(
  function middleware(request: NextRequestWithAuth) {
    const isAuthenticated = Boolean(request.nextauth.token) || hasSessionCookie(request);

    if (!isAuthenticated) {
      const signinUrl = new URL("/signin", request.url);
      signinUrl.searchParams.set("from", request.nextUrl.pathname);
      return NextResponse.redirect(signinUrl);
    }

    // Allow authenticated users (ADMIN/REVIEWER/USER) to reach /admin.
    // The UI and route handlers enforce role-based capabilities.
    return NextResponse.next();
  },
  {
    callbacks: {
      // Always run the handler; we perform our own auth checks.
      authorized: () => true,
    },
  }
);

export const config = {
  matcher: ["/admin/:path*"],
};
