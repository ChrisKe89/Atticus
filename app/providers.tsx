'use client';

import { SessionProvider } from 'next-auth/react';
import type { ReactNode } from 'react';
import type { SessionProviderProps } from 'next-auth/react';

interface ProvidersProps {
  children: ReactNode;
  session?: SessionProviderProps['session'];
}

export function Providers({ children, session }: ProvidersProps) {
  return <SessionProvider session={session}>{children}</SessionProvider>;
}
