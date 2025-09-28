import { DefaultSession, DefaultUser } from 'next-auth';
import { Role } from '@prisma/client';

declare module 'next-auth' {
  interface Session extends DefaultSession {
    user?: {
      id: string;
      role: Role;
      orgId: string;
    } & DefaultSession['user'];
    expires: DefaultSession['expires'];
  }

  interface User extends DefaultUser {
    role: Role;
    orgId: string;
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    userId: string;
    role: Role;
    orgId: string;
  }
}
