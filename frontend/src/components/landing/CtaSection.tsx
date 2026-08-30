"use client";

import React from "react";
import Link from "next/link";
import { BauhausButton } from "@/components/ui/BauhausButton";
import { ShieldCheck, ArrowRight, Github, Terminal } from "lucide-react";

export const CtaSection: React.FC = () => {
  return (
    <section className="bg-[#F0C020] border-b-2 md:border-b-4 border-[#121212] py-16 md:py-24 relative overflow-hidden">
      {/* Bauhaus Decorative Corner Shapes at 50% opacity */}
      <div className="absolute -top-16 -left-16 w-64 h-64 rounded-full bg-[#D02020] opacity-50 border-4 border-black pointer-events-none" />
      <div className="absolute -bottom-16 -right-16 w-64 h-64 bg-[#1040C0] opacity-50 rotate-45 border-4 border-black pointer-events-none" />
      <div className="absolute inset-0 bg-dot-grid opacity-10 pointer-events-none" />

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center space-y-8">
        {/* Top Tag */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-black text-white border-2 border-black shadow-[3px_3px_0px_0px_#FFFFFF]">
          <ShieldCheck className="w-4 h-4 text-[#F0C020]" />
          <span className="text-xs font-black uppercase tracking-widest">
            STATEFUL DEFENSE READY
          </span>
        </div>

        {/* Massive Constructivist Headline */}
        <h2 className="text-5xl sm:text-7xl lg:text-8xl font-black uppercase tracking-tighter text-[#121212] leading-[0.88]">
          DEFEND YOUR
          <br />
          PULL REQUESTS<span className="text-[#D02020]">.</span>
        </h2>

        <p className="text-base sm:text-xl font-bold text-[#121212] max-w-2xl mx-auto leading-relaxed">
          Install GitSentry on your GitHub repositories in seconds. Zero noisy
          stateless warnings—only precision audits, stateful memory, and
          automatic remediation diffs.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link href="/dashboard" className="w-full sm:w-auto">
            <BauhausButton
              variant="primary"
              shape="square"
              size="xl"
              icon={<ArrowRight className="w-6 h-6 stroke-[3]" />}
              className="w-full sm:w-auto shadow-[6px_6px_0px_0px_black]"
            >
              Launch Live Console
            </BauhausButton>
          </Link>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="w-full sm:w-auto"
          >
            <BauhausButton
              variant="outline"
              shape="square"
              size="xl"
              icon={<Github className="w-5 h-5 stroke-[2.5]" />}
              className="w-full sm:w-auto shadow-[6px_6px_0px_0px_black]"
            >
              Install GitHub App
            </BauhausButton>
          </a>
        </div>

        {/* CLI Quickstart Tip */}
        <div className="pt-6">
          <div className="inline-flex items-center gap-3 bg-white border-2 md:border-4 border-black px-4 py-2 text-xs md:text-sm font-mono font-bold shadow-[4px_4px_0px_0px_#121212]">
            <Terminal className="w-4 h-4 text-[#D02020]" />
            <span>git clone https://github.com/gitsentry/copilot.git</span>
          </div>
        </div>
      </div>
    </section>
  );
};
