import type { Metadata } from "next";
import { Inter, Noto_Sans_JP } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { ThemeProvider } from "@/components/providers/ThemeProvider";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const notoSansJP = Noto_Sans_JP({
  variable: "--font-noto-sans-jp",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "AI Company Dojo - 4 Sages System",
  description: "AI Company management system powered by the 4 Sages architecture",
  keywords: ["AI Company", "4 Sages", "Knowledge Management", "Task Management"],
  authors: [{ name: "AI Company" }],
  creator: "AI Company",
  openGraph: {
    title: "AI Company Dojo",
    description: "4 Sages System for AI-powered company management",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" className="h-full">
      <body
        className={`${inter.variable} ${notoSansJP.variable} font-sage antialiased h-full bg-sage-50 text-sage-900 dark:bg-sage-950 dark:text-sage-50`}
      >
        <ThemeProvider>
          <div className="flex min-h-full flex-col">
            <Header />
            <main className="flex-1">
              {children}
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
