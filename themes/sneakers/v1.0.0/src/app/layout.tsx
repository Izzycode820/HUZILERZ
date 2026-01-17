import type { Metadata } from "next";

import "./globals.css";
import { ApolloProviderWrapper } from "@/lib/apollo-provider";
import { SessionProvider } from "@/lib/session/SessionProvider";
import { Header } from "@/components/shared/Header";
import { Toaster } from "@/components/shadcn-ui/sonner";
import { ThemeProvider } from "next-themes";



export const metadata: Metadata = {
  title: "Sneakers Store",
  description: "Premium sneakers and streetwear",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className="antialiased flex min-h-screen flex-col"
      >
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <ApolloProviderWrapper>
            <SessionProvider>
              <Header />
              <main className="flex-1">
                {children}
              </main>
              <Toaster />
            </SessionProvider>
          </ApolloProviderWrapper>
        </ThemeProvider>
      </body>
    </html>
  );
}


