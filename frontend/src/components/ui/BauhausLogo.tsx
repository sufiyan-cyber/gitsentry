"use client";

import React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export interface BauhausLogoProps {
  size?: "sm" | "md" | "lg" | "xl";
  showText?: boolean;
  className?: string;
  href?: string;
}

export const BauhausLogo: React.FC<BauhausLogoProps> = ({
  size = "md",
  showText = true,
  className,
  href = "/",
}) => {
  const sizeMap = {
    sm: {
      shape: "w-3.5 h-3.5",
      gap: "gap-1",
      text: "text-lg",
      badgeText: "text-[9px]",
    },
    md: {
      shape: "w-4.5 h-4.5 md:w-5 md:h-5",
      gap: "gap-1.5",
      text: "text-xl md:text-2xl",
      badgeText: "text-[10px]",
    },
    lg: {
      shape: "w-6 h-6 md:w-7 md:h-7",
      gap: "gap-2",
      text: "text-2xl md:text-3xl",
      badgeText: "text-xs",
    },
    xl: {
      shape: "w-8 h-8 md:w-10 md:h-10",
      gap: "gap-2.5",
      text: "text-3xl md:text-5xl",
      badgeText: "text-sm",
    },
  };

  const currentSize = sizeMap[size];

  const content = (
    <div
      className={cn(
        "group inline-flex items-center gap-3 select-none cursor-pointer transition-transform duration-150 active:scale-95",
        className
      )}
    >
      {/* The Iconic Bauhaus Geometric Trinity: Circle (Red), Square (Blue), Triangle (Yellow) */}
      <div className={cn("inline-flex items-center", currentSize.gap)}>
        {/* Red Circle */}
        <div
          className={cn(
            "rounded-full bg-[#D02020] border-2 border-[#121212] shadow-[2px_2px_0px_0px_#121212] transition-transform duration-200 group-hover:-translate-y-0.5",
            currentSize.shape
          )}
        />
        {/* Blue Square */}
        <div
          className={cn(
            "rounded-none bg-[#1040C0] border-2 border-[#121212] shadow-[2px_2px_0px_0px_#121212] transition-transform duration-200 group-hover:rotate-12",
            currentSize.shape
          )}
        />
        {/* Yellow Triangle */}
        <div
          className={cn(
            "clip-triangle bg-[#F0C020] transition-transform duration-200 group-hover:translate-y-0.5",
            currentSize.shape
          )}
          style={{
            filter: "drop-shadow(2px 2px 0px #121212)",
          }}
        />
      </div>

      {/* Brand Title */}
      {showText && (
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span
              className={cn(
                "font-black uppercase tracking-tighter text-[#121212] leading-none",
                currentSize.text
              )}
            >
              GIT<span className="text-[#D02020]">.</span>SENTRY
            </span>
            <span
              className={cn(
                "hidden sm:inline-block px-1.5 py-0.5 font-black uppercase tracking-widest bg-[#121212] text-[#F0C020] border border-black",
                currentSize.badgeText
              )}
            >
              SEC-OPS
            </span>
          </div>
        </div>
      )}
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="inline-block focus:outline-none">
        {content}
      </Link>
    );
  }

  return content;
};
