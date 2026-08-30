"use client";

import React, { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

export interface AccordionItem {
  id: string;
  question: string;
  answer: string;
  tag?: string;
}

export interface BauhausAccordionProps {
  items: AccordionItem[];
  defaultOpenId?: string;
  allowMultiple?: boolean;
  className?: string;
}

export const BauhausAccordion: React.FC<BauhausAccordionProps> = ({
  items,
  defaultOpenId,
  allowMultiple = false,
  className,
}) => {
  const [openIds, setOpenIds] = useState<string[]>(
    defaultOpenId ? [defaultOpenId] : []
  );

  const toggleItem = (id: string) => {
    if (allowMultiple) {
      setOpenIds((prev) =>
        prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
      );
    } else {
      setOpenIds((prev) => (prev.includes(id) ? [] : [id]));
    }
  };

  return (
    <div className={cn("space-y-4 md:space-y-6", className)}>
      {items.map((item, index) => {
        const isOpen = openIds.includes(item.id);
        const shapeMod = index % 3;

        return (
          <div
            key={item.id}
            className={cn(
              "rounded-none border-2 md:border-4 border-[#121212] transition-all duration-200",
              isOpen
                ? "shadow-[6px_6px_0px_0px_#121212] md:shadow-[8px_8px_0px_0px_#121212]"
                : "shadow-[3px_3px_0px_0px_#121212] md:shadow-[4px_4px_0px_0px_#121212] hover:-translate-y-0.5 hover:shadow-[5px_5px_0px_0px_#121212]"
            )}
          >
            {/* Accordion Header */}
            <button
              type="button"
              onClick={() => toggleItem(item.id)}
              aria-expanded={isOpen}
              className={cn(
                "w-full text-left p-4 md:p-6 flex items-center justify-between gap-4 transition-colors duration-200 select-none cursor-pointer",
                isOpen
                  ? "bg-[#D02020] text-white"
                  : "bg-white text-[#121212] hover:bg-neutral-50"
              )}
            >
              <div className="flex items-center gap-3 md:gap-4 pr-2">
                {/* Geometric item bullet indicator */}
                <div className="shrink-0 flex items-center justify-center">
                  {shapeMod === 0 && (
                    <div
                      className={cn(
                        "w-3.5 h-3.5 md:w-4 md:h-4 rounded-full border border-black",
                        isOpen ? "bg-[#F0C020]" : "bg-[#D02020]"
                      )}
                    />
                  )}
                  {shapeMod === 1 && (
                    <div
                      className={cn(
                        "w-3.5 h-3.5 md:w-4 md:h-4 rounded-none border border-black",
                        isOpen ? "bg-white" : "bg-[#1040C0]"
                      )}
                    />
                  )}
                  {shapeMod === 2 && (
                    <div
                      className={cn(
                        "w-3.5 h-3.5 md:w-4 md:h-4 clip-triangle",
                        isOpen ? "bg-[#F0C020]" : "bg-[#121212]"
                      )}
                      style={{
                        backgroundColor: isOpen ? "#F0C020" : "#121212",
                      }}
                    />
                  )}
                </div>

                <span className="font-extrabold text-base md:text-xl uppercase tracking-tight leading-snug">
                  {item.question}
                </span>
              </div>

              <div
                className={cn(
                  "shrink-0 w-8 h-8 md:w-10 md:h-10 flex items-center justify-center border-2 border-black transition-transform duration-200 ease-out",
                  isOpen
                    ? "bg-[#F0C020] text-[#121212] rotate-180 shadow-[2px_2px_0px_0px_#121212]"
                    : "bg-white text-[#121212]"
                )}
              >
                <ChevronDown className="w-5 h-5 stroke-[2.5]" />
              </div>
            </button>

            {/* Accordion Expanded Content */}
            {isOpen && (
              <div className="bg-[#FFF9C4] text-[#121212] p-5 md:p-7 border-t-2 md:border-t-4 border-[#121212] transition-all animate-in fade-in duration-200">
                <p className="font-medium text-sm md:text-base leading-relaxed text-[#121212]">
                  {item.answer}
                </p>
                {item.tag && (
                  <div className="mt-4 pt-3 border-t border-black/20 flex items-center justify-between">
                    <span className="inline-block px-2.5 py-1 text-xs font-black uppercase tracking-widest bg-black text-white">
                      {item.tag}
                    </span>
                    <span className="text-xs font-bold uppercase tracking-wider text-black/70">
                      GitSentry Verification Matrix
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
