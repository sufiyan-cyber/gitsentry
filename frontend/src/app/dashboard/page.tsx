"use client";

import React, { useState } from "react";
import Link from "next/link";
import { BauhausLogo } from "@/components/ui/BauhausLogo";
import { BauhausButton } from "@/components/ui/BauhausButton";
import { BauhausBadge } from "@/components/ui/BauhausBadge";
import { PrAuditSimulator } from "@/components/dashboard/PrAuditSimulator";
import { MemoryBankViewer } from "@/components/dashboard/MemoryBankViewer";
import {
  ArrowLeft,
  ShieldCheck,
  Cpu,
  Database,
  Terminal,
  Activity,
  Layers,
} from "lucide-react";

export default function DashboardPage() {
  const [activeView, setActiveView] = useState<"simulator" | "memory">("simulator");

  return (
    <div className="min-h-screen bg-[#F0F0F0] text-[#121212] flex flex-col selection:bg-[#F0C020] selection:text-[#121212]">
      {/* Dashboard Sticky Top Nav */}
      <header className="sticky top-0 z-50 bg-[#F0F0F0] border-b-2 md:border-b-4 border-[#121212]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 md:h-20">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="p-2 border-2 border-black bg-white shadow-[2px_2px_0px_0px_#121212] hover:bg-[#F0C020] transition-colors"
                title="Back to Landing Page"
              >
                <ArrowLeft className="w-4 h-4 stroke-[3]" />
              </Link>
              <BauhausLogo size="sm" />
            </div>

            {/* View Switcher Pills */}
            <div className="flex items-center p-1 bg-white border-2 border-black shadow-[3px_3px_0px_0px_#121212]">
              <button
                onClick={() => setActiveView("simulator")}
                className={`px-3 py-1.5 text-xs font-black uppercase tracking-wider transition-all cursor-pointer flex items-center gap-1.5 ${
                  activeView === "simulator"
                    ? "bg-[#D02020] text-white shadow-[2px_2px_0px_0px_#121212]"
                    : "text-[#121212] hover:bg-neutral-100"
                }`}
              >
                <Cpu className="w-3.5 h-3.5" />
                <span>PR Triage Simulator</span>
              </button>

              <button
                onClick={() => setActiveView("memory")}
                className={`px-3 py-1.5 text-xs font-black uppercase tracking-wider transition-all cursor-pointer flex items-center gap-1.5 ${
                  activeView === "memory"
                    ? "bg-[#1040C0] text-white shadow-[2px_2px_0px_0px_#121212]"
                    : "text-[#121212] hover:bg-neutral-100"
                }`}
              >
                <Database className="w-3.5 h-3.5" />
                <span>Memory Bank</span>
              </button>
            </div>

            {/* Live Status Pill */}
            <div className="hidden sm:flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse border border-black" />
              <span className="text-[11px] font-black uppercase tracking-widest text-[#121212]">
                GEMINI 3.7 FLASH // LIVE
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Console Body */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12 w-full space-y-8">
        {activeView === "simulator" ? (
          <PrAuditSimulator />
        ) : (
          <MemoryBankViewer />
        )}
      </main>

      {/* Minimal Constructivist Dashboard Footer */}
      <footer className="border-t-2 md:border-t-4 border-black bg-white py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-extrabold uppercase tracking-wider">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#D02020]" />
            <span className="w-2.5 h-2.5 rounded-none bg-[#1040C0]" />
            <span className="w-2.5 h-2.5 clip-triangle bg-[#F0C020]" />
            <span className="ml-1 text-black">GITSENTRY SECURITY CONSOLE</span>
          </div>

          <div className="flex items-center gap-4 text-neutral-600">
            <span>FIRESTORE: CONNECTED</span>
            <span>OSV.DEV: SYNCED</span>
            <span>HMAC-SHA256: ARMED</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
