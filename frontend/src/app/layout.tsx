import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800", "900"],
  variable: "--font-outfit",
  display: "swap",
});

export const metadata: Metadata = {
  title: "GitSentry — Stateful AI Security Co-Pilot for GitHub (Bauhaus Edition)",
  description:
    "Autonomous security co-pilot for GitHub with stateful architectural memory, two-tier Gemini 3.7 Flash triage, OSV.dev CVE patching, and commit status gating.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={outfit.variable}>
      <body className="min-h-screen bg-[#F0F0F0] text-[#121212] antialiased selection:bg-[#F0C020] selection:text-[#121212]">
        {children}
      </body>
    </html>
  );
}
