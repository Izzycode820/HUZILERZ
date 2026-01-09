import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ApolloProviderWrapper } from "@/lib/apollo-provider";
import { SessionProvider } from "@/lib/session/SessionProvider";
import { Header } from "@/components/shared/Header";
import { Toaster } from "@/components/shadcn-ui/sonner";
import { ThemeProvider } from "next-themes";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

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
        className={`${geistSans.variable} ${geistMono.variable} antialiased flex min-h-screen flex-col`}
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


