import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from './providers';
import { Toaster } from '@/components/shadcn-ui/sonner';

// Viewport configuration (Next.js 15+ - themeColor moved here)
export const viewport: Viewport = {
  themeColor: "#000000",
};

export const metadata: Metadata = {
  title: "Huzilaz Camp",
  description: "For all business  owners and upcomming entrepreneurs",
  manifest: "/manifest.json",
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
        <Providers>
          {children}
          <Toaster position="top-right" richColors closeButton />
        </Providers>
      </body>
    </html>
  );
}