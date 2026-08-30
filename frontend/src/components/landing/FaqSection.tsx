"use client";

import React from "react";
import { FAQ_ITEMS } from "@/lib/mockData";
import { BauhausAccordion } from "@/components/ui/BauhausAccordion";
import { HelpCircle } from "lucide-react";

export const FaqSection: React.FC = () => {
  return (
    <section
      id="faq"
      className="bg-[#F0F0F0] border-b-2 md:border-b-4 border-[#121212] py-16 md:py-24"
    >
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center space-y-4 mb-12 md:mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-white border-2 border-black shadow-[2px_2px_0px_0px_#121212]">
            <HelpCircle className="w-4 h-4 text-[#D02020]" />
            <span className="text-xs font-black uppercase tracking-widest text-[#121212]">
              KNOWLEDGE BASE // FAQ
            </span>
          </div>

          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-black uppercase tracking-tighter text-[#121212] leading-[0.9]">
            FREQUENTLY ASKED
            <br />
            TECHNICAL QUESTIONS<span className="text-[#D02020]">.</span>
          </h2>

          <p className="text-sm md:text-base font-semibold text-[#121212]/80 max-w-xl mx-auto">
            Everything you need to know about two-tier Gemini thinking, stateful
            Firestore memory persistence, and commit gating.
          </p>
        </div>

        {/* Accordion Component */}
        <BauhausAccordion
          items={FAQ_ITEMS}
          defaultOpenId="faq-1"
          allowMultiple={false}
        />
      </div>
    </section>
  );
};
