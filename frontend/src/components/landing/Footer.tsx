"use client";

import React from "react";
import Link from "next/link";
import { BauhausLogo } from "@/components/ui/BauhausLogo";
import { Github, Shield, Terminal, Heart, Sparkles } from "lucide-react";

export const Footer: React.FC = () => {
  return (
    <footer className="bg-[#121212] text-white border-t-4 border-black py-12 md:py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-8 lg:gap-12 pb-12 border-b-2 border-neutral-800">
          {/* Brand Col */}
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5">
                <div className="w-4 h-4 rounded-full bg-[#D02020] border border-white" />
                <div className="w-4 h-4 rounded-none bg-[#1040C0] border border-white" />
                <div className="w-4 h-4 clip-triangle bg-[#F0C020]" />
              </div>
              <span className="text-2xl font-black uppercase tracking-tighter text-white">
                SENTINEL<span className="text-[#D02020]">.</span>AI
              </span>
            </div>

            <p className="text-sm font-medium text-neutral-400 max-w-sm leading-relaxed">
              Stateful AI Security Co-Pilot for GitHub built on Gemini 3.7 Flash,
              Cloud Run, Pub/Sub, and Firestore Memory Banks.
            </p>

            <div className="flex items-center gap-2 pt-2">
              <span className="px-2 py-0.5 text-[10px] font-black uppercase bg-[#D02020] text-white">
                GCP CLOUD RUN
              </span>
              <span className="px-2 py-0.5 text-[10px] font-black uppercase bg-[#1040C0] text-white">
                FIRESTORE
              </span>
              <span className="px-2 py-0.5 text-[10px] font-black uppercase bg-[#F0C020] text-black">
                GEMINI 3.7 FLASH
              </span>
            </div>
          </div>

          {/* Quick Nav */}
          <div className="lg:col-span-2 space-y-3">
            <h4 className="text-xs font-black uppercase tracking-widest text-[#F0C020]">
              NAVIGATION
            </h4>
            <ul className="space-y-2 text-sm font-bold uppercase tracking-wider text-neutral-300">
              <li>
                <Link
                  href="#architecture"
                  className="hover:text-[#D02020] transition-colors"
                >
                  Architecture
                </Link>
              </li>
              <li>
                <Link
                  href="#features"
                  className="hover:text-[#1040C0] transition-colors"
                >
                  Capabilities
                </Link>
              </li>
              <li>
                <Link
                  href="#threat-stream"
                  className="hover:text-[#F0C020] transition-colors"
                >
                  Threat Stream
                </Link>
              </li>
              <li>
                <Link
                  href="#faq"
                  className="hover:text-white transition-colors"
                >
                  FAQ
                </Link>
              </li>
            </ul>
          </div>

          {/* Console / Resources */}
          <div className="lg:col-span-2 space-y-3">
            <h4 className="text-xs font-black uppercase tracking-widest text-[#D02020]">
              CONSOLE
            </h4>
            <ul className="space-y-2 text-sm font-bold uppercase tracking-wider text-neutral-300">
              <li>
                <Link
                  href="/dashboard"
                  className="hover:text-[#F0C020] transition-colors"
                >
                  PR Simulator
                </Link>
              </li>
              <li>
                <Link
                  href="/dashboard"
                  className="hover:text-[#D02020] transition-colors"
                >
                  Memory Bank
                </Link>
              </li>
              <li>
                <Link
                  href="/dashboard"
                  className="hover:text-[#1040C0] transition-colors"
                >
                  Audit Logs
                </Link>
              </li>
              <li>
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white transition-colors flex items-center gap-1"
                >
                  <Github className="w-3.5 h-3.5" />
                  GitHub Repo
                </a>
              </li>
            </ul>
          </div>

          {/* Constructivist Design Badge */}
          <div className="lg:col-span-3 space-y-3">
            <h4 className="text-xs font-black uppercase tracking-widest text-[#1040C0]">
              DESIGN STYLE
            </h4>
            <div className="bg-neutral-900 border-2 border-neutral-700 p-4 space-y-2">
              <p className="text-xs font-extrabold uppercase text-white tracking-wider">
                BAUHAUS CONSTRUCTIVIST
              </p>
              <p className="text-[11px] text-neutral-400 leading-normal">
                Form follows function. Geometric purity, primary color theory,
                thick 4px borders, hard offset shadows, and Outfit typography.
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-bold uppercase tracking-wider text-neutral-500">
          <div>
            © 2026 GITSENTRY CO-PILOT. ALL RIGHTS RESERVED.
          </div>
          <div className="flex items-center gap-2">
            <span>BUILT FOR ALL THINGS AGENTIC HACKATHON</span>
            <span className="w-1.5 h-1.5 rounded-full bg-[#D02020]" />
            <span className="text-[#F0C020]">GEMINI 3.7 FLASH</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
