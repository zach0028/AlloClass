import type { Metadata } from "next";
import { Poppins } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { Providers } from "@/components/layout/Providers";

const poppins = Poppins({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "AlloClass",
  description: "Classification intelligente par LLM — AlloBrain",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <body className={`${poppins.variable} font-sans antialiased`}>
        <Providers>
          <Sidebar />
          <main className="ml-[68px] min-h-screen">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
