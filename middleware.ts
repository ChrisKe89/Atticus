import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";
import type { NextRequestWithAuth } from "next-auth/middleware";

type TokenRole = "USER" | "REVIEWER" | "ADMIN" | undefined;

export default withAuth(
  function middleware(request: NextRequestWithAuth) {
    const role = request.nextauth.token?.role as TokenRole;
    const isAuthenticated = Boolean(request.nextauth.token);

    if (request.nextUrl.pathname.startsWith("/api/glossary")) {
      if (!isAuthenticated) {
        return NextResponse.json({ error: "unauthorized" }, { status: 401 });
      }
      if (role !== "ADMIN") {
        return NextResponse.json({ error: "forbidden" }, { status: 403 });
      }
      return NextResponse.next();
    }

    if (!isAuthenticated) {
      const signinUrl = new URL("/signin", request.url);
      signinUrl.searchParams.set("from", request.nextUrl.pathname);
      return NextResponse.redirect(signinUrl);
    }

    if (role !== "ADMIN") {
      return NextResponse.redirect(new URL("/", request.url));
    }

    return NextResponse.next();
  },
  {
    callbacks: {
      authorized: () => true,
    },
  }
);

export const config = {
  matcher: ["/admin/:path*", "/api/glossary/:path*"],
};
