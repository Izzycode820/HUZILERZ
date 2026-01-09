import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from '@/utils/ThemeContext';
import { AuthInitializer } from '@/components/authentication/shared/AuthInitializer';
import { TokenManager } from '@/components/authentication/shared/TokenManager';
import { Toaster } from '@/components/shadcn-ui/sonner';

export const metadata: Metadata = {
  title: "Huzilaz Camp",
  description: "For all business  owners and upcomming entrepreneurs",
  manifest: "/manifest.json",
  themeColor: "#000000",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Huzilaz",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className="font-sans antialiased bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 transition-colors"
      >
        <ThemeProvider>
          <AuthInitializer>
            <TokenManager>
              {children}
            </TokenManager>
          </AuthInitializer>
          <Toaster position="top-right" richColors closeButton />
        </ThemeProvider>
      </body>
    </html>
  );
}