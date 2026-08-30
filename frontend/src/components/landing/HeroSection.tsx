"use client";

import React from "react";
import Link from "next/link";
import { BauhausButton } from "@/components/ui/BauhausButton";
import { BauhausBadge } from "@/components/ui/BauhausBadge";
import {
  ShieldAlert,
  Sparkles,
  ArrowRight,
  GitPullRequest,
  CheckCircle2,
  Lock,
  Cpu,
} from "lucide-react";

export const HeroSection: React.FC = () => {
  return (
    <section className="relative overflow-hidden bg-[#F0F0F0] border-b-2 md:border-b-4 border-[#121212] py-12 md:py-20 lg:py-28">
      {/* Background Dot Grid */}
      <div className="absolute inset-0 bg-dot-grid opacity-30 pointer-events-none" />

      {/* Decorative Large Background Geometric Watermarks */}
      <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full border-4 border-black/10 pointer-events-none" />
      <div className="absolute top-1/2 -right-20 w-80 h-80 rotate-45 border-4 border-black/10 pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
          {/* Left Column: Massive Constructivist Typography */}
          <div className="lg:col-span-7 space-y-6 md:space-y-8">
            {/* Pill Badge */}
            <div className="inline-flex items-center gap-2">
              <BauhausBadge
                variant="yellow"
                shape="square"
                size="md"
                icon={<Sparkles className="w-3.5 h-3.5" />}
              >
                Gemini 3.7 Flash Engine
              </BauhausBadge>
              <span className="hidden sm:inline-block text-xs font-black uppercase tracking-widest text-[#121212]/70">
                // Dual-Tier Thinking
              </span>
            </div>

            {/* Colossal Display Headline */}
            <div className="space-y-1">
              <h1 className="text-5xl sm:text-7xl lg:text-8xl font-black uppercase tracking-tighter text-[#121212] leading-[0.88]">
                STATEFUL
                <br />
                <span className="text-[#D02020] underline decoration-[#121212] decoration-4 underline-offset-4">
                  SECURITY
                </span>
                <br />
                CO-PILOT<span className="text-[#1040C0]">.</span>
              </h1>
            </div>

            {/* Subheading & Explanation */}
            <p className="text-base sm:text-xl font-medium text-[#121212] leading-relaxed max-w-2xl">
              Unlike stateless scanners that drop noisy comments, GitSentry
              remembers architectural decisions in Firestore, audits pull
              requests with dual-tier Gemini intelligence, and autonomously
              submits precision remediation PRs while gating merges.
            </p>

            {/* Primary Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 pt-2">
              <Link href="/dashboard">
                <BauhausButton
                  variant="primary"
                  shape="square"
                  size="lg"
                  icon={<ArrowRight className="w-5 h-5 stroke-[3]" />}
                >
                  Enter Security Console
                </BauhausButton>
              </Link>
              <Link href="#architecture">
                <BauhausButton
                  variant="outline"
                  shape="square"
                  size="lg"
                  icon={<Cpu className="w-5 h-5 stroke-[2.5]" />}
                >
                  Explore Architecture
                </BauhausButton>
              </Link>
            </div>

            {/* Key Assurance Signals */}
            <div className="pt-4 border-t-2 border-black/30 flex flex-wrap items-center gap-y-3 gap-x-6 text-xs sm:text-sm font-bold uppercase tracking-wider text-[#121212]">
              <div className="flex items-center gap-2">
                <div className="w-3.5 h-3.5 rounded-full bg-[#D02020] border border-black" />
                <span>Zero Secret Leaks</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3.5 h-3.5 rounded-none bg-[#1040C0] border border-black" />
                <span>Decoupled Pub/Sub</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3.5 h-3.5 clip-triangle bg-[#F0C020]" />
                <span>OSV.dev CVE Database</span>
              </div>
            </div>
          </div>

          {/* Right Column: Bauhaus Geometric Poster Composition */}
          <div className="lg:col-span-5 relative flex items-center justify-center">
            {/* Main Blue Color-Blocked Container */}
            <div className="relative w-full max-w-md aspect-square bg-[#1040C0] border-2 md:border-4 border-[#121212] shadow-[6px_6px_0px_0px_#121212] md:shadow-[10px_10px_0px_0px_#121212] p-6 flex flex-col justify-between overflow-hidden">
              {/* White Dot Grid on Blue */}
              <div className="absolute inset-0 bg-dot-grid-white opacity-20 pointer-events-none" />

              {/* Composition Shapes */}
              {/* Top-Right Large Yellow Rotated Square */}
              <div className="absolute -top-10 -right-10 w-36 h-36 bg-[#F0C020] border-4 border-black rotate-45 shadow-[4px_4px_0px_0px_#121212] transition-transform duration-500 hover:rotate-90 pointer-events-none" />

              {/* Bottom-Left Red Circle */}
              <div className="absolute -bottom-12 -left-12 w-40 h-40 rounded-full bg-[#D02020] border-4 border-black shadow-[4px_4px_0px_0px_#121212] pointer-events-none" />

              {/* Diagonal Decorative Strip */}
              <div className="absolute top-1/2 left-0 right-0 h-1 bg-black/40 -translate-y-1/2" />

              {/* Top Banner inside Poster */}
              <div className="relative z-10 flex items-center justify-between">
                <div className="flex items-center gap-2 px-3 py-1 bg-white border-2 border-black shadow-[2px_2px_0px_0px_#121212]">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#D02020]" />
                  <span className="text-[11px] font-black uppercase tracking-widest text-black">
                    PR #42 AUDIT
                  </span>
                </div>
                <div className="w-6 h-6 clip-triangle bg-[#F0C020] border border-black" />
              </div>

              {/* Center Floating Constructivist Card (Live Security Gate) */}
              <div className="relative z-10 bg-white border-2 md:border-4 border-[#121212] shadow-[6px_6px_0px_0px_#121212] p-4 my-auto">
                <div className="flex items-center justify-between pb-2 border-b-2 border-black">
                  <div className="flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4 text-[#D02020] stroke-[3]" />
                    <span className="text-xs font-black uppercase tracking-wider text-black">
                      Commit Gate Blocked
                    </span>
                  </div>
                  <span className="text-[10px] font-black px-2 py-0.5 bg-[#D02020] text-white">
                    HIGH RISK
                  </span>
                </div>

                <div className="py-2.5 space-y-1.5 text-left">
                  <p className="text-xs font-extrabold uppercase tracking-tight text-black line-clamp-1">
                    SQL Injection in find_user_by_email()
                  </p>
                  <div className="text-[11px] font-mono bg-black text-[#F0C020] p-2 border border-black/50">
                    <code>- query = f&quot;SELECT * WHERE email = &apos;&#123;email&#125;&apos;&quot;</code>
                    <br />
                    <code>+ query = &quot;SELECT * WHERE email = %s&quot;</code>
                  </div>
                </div>

                <div className="pt-2 border-t-2 border-black flex items-center justify-between text-[10px] font-black uppercase tracking-wider text-black/80">
                  <span>Branch: gitsentry/fix-pr-42</span>
                  <span className="text-[#1040C0]">Auto Remediation Ready</span>
                </div>
              </div>

              {/* Bottom Footer inside Poster */}
              <div className="relative z-10 flex items-center justify-between text-white font-black text-xs uppercase tracking-widest">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-[#F0C020] stroke-[3]" />
                  HMAC SHA-256 Verified
                </span>
                <span className="bg-black text-[#F0C020] px-2 py-0.5 border border-white/40">
                  CLOUD RUN
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
