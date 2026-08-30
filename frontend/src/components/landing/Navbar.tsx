"use client";

import React, { useState } from "react";
import Link from "next/link";
import { BauhausLogo } from "@/components/ui/BauhausLogo";
import { BauhausButton } from "@/components/ui/BauhausButton";
import { BauhausBadge } from "@/components/ui/BauhausBadge";
import { Menu, X, ShieldCheck, ArrowRight, Github } from "lucide-react";

export const Navbar: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full bg-[#F0F0F0] border-b-2 md:border-b-4 border-[#121212]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 md:h-20">
          {/* Brand Logo */}
          <div className="flex items-center gap-4">
            <BauhausLogo size="md" />
            <div className="hidden lg:flex items-center gap-2 pl-4 border-l-2 border-black/30">
              <span className="w-2.5 h-2.5 rounded-full bg-[#D02020] animate-pulse" />
              <span className="text-[11px] font-black uppercase tracking-wider text-[#121212]/80">
                ACTIVE GATE: v2.4
              </span>
            </div>
          </div>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-6 lg:gap-8">
            <Link
              href="#architecture"
              className="text-xs lg:text-sm font-extrabold uppercase tracking-widest text-[#121212] hover:text-[#D02020] transition-colors relative py-1 hover:border-b-2 hover:border-[#D02020]"
            >
              Architecture
            </Link>
            <Link
              href="#features"
              className="text-xs lg:text-sm font-extrabold uppercase tracking-widest text-[#121212] hover:text-[#1040C0] transition-colors relative py-1 hover:border-b-2 hover:border-[#1040C0]"
            >
              Capabilities
            </Link>
            <Link
              href="#threat-stream"
              className="text-xs lg:text-sm font-extrabold uppercase tracking-widest text-[#121212] hover:text-[#D02020] transition-colors relative py-1 hover:border-b-2 hover:border-[#D02020]"
            >
              Threat Stream
            </Link>
            <Link
              href="#faq"
              className="text-xs lg:text-sm font-extrabold uppercase tracking-widest text-[#121212] hover:text-[#1040C0] transition-colors relative py-1 hover:border-b-2 hover:border-[#1040C0]"
            >
              FAQ
            </Link>
            <Link
              href="/dashboard"
              className="text-xs lg:text-sm font-extrabold uppercase tracking-widest text-[#121212] flex items-center gap-1.5 px-2.5 py-1 bg-[#F0C020] border-2 border-black shadow-[2px_2px_0px_0px_#121212] hover:bg-[#F0C020]/90 transition-all"
            >
              <ShieldCheck className="w-3.5 h-3.5 stroke-[2.5]" />
              Live Console
            </Link>
          </nav>

          {/* CTA & GitHub Actions */}
          <div className="hidden sm:flex items-center gap-3">
            <Link href="/dashboard">
              <BauhausButton
                variant="primary"
                shape="square"
                size="sm"
                icon={<ArrowRight className="w-4 h-4 stroke-[3]" />}
              >
                Launch Simulator
              </BauhausButton>
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden flex items-center gap-2">
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="p-2 border-2 border-black bg-white shadow-[2px_2px_0px_0px_#121212] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none"
              aria-label="Toggle navigation menu"
            >
              {mobileOpen ? (
                <X className="w-6 h-6 stroke-[2.5]" />
              ) : (
                <Menu className="w-6 h-6 stroke-[2.5]" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="md:hidden bg-[#F0F0F0] border-t-2 border-black px-4 pt-4 pb-6 space-y-3 animate-in slide-in-from-top-2 duration-200">
          <Link
            href="#architecture"
            onClick={() => setMobileOpen(false)}
            className="block px-3 py-2 text-sm font-black uppercase tracking-wider text-[#121212] hover:bg-black hover:text-white border-2 border-transparent hover:border-black"
          >
            Architecture
          </Link>
          <Link
            href="#features"
            onClick={() => setMobileOpen(false)}
            className="block px-3 py-2 text-sm font-black uppercase tracking-wider text-[#121212] hover:bg-[#D02020] hover:text-white border-2 border-transparent hover:border-black"
          >
            Capabilities
          </Link>
          <Link
            href="#threat-stream"
            onClick={() => setMobileOpen(false)}
            className="block px-3 py-2 text-sm font-black uppercase tracking-wider text-[#121212] hover:bg-[#1040C0] hover:text-white border-2 border-transparent hover:border-black"
          >
            Threat Stream
          </Link>
          <Link
            href="#faq"
            onClick={() => setMobileOpen(false)}
            className="block px-3 py-2 text-sm font-black uppercase tracking-wider text-[#121212] hover:bg-black hover:text-white border-2 border-transparent hover:border-black"
          >
            FAQ
          </Link>
          <Link
            href="/dashboard"
            onClick={() => setMobileOpen(false)}
            className="block px-3 py-2 text-sm font-black uppercase tracking-wider bg-[#F0C020] text-black border-2 border-black shadow-[2px_2px_0px_0px_#121212]"
          >
            Open Live Security Console →
          </Link>
        </div>
      )}
    </header>
  );
};
