"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface BauhausBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "red" | "blue" | "yellow" | "black" | "white" | "outline";
  shape?: "square" | "pill";
  size?: "sm" | "md" | "lg";
  icon?: React.ReactNode;
  children: React.ReactNode;
}

export const BauhausBadge: React.FC<BauhausBadgeProps> = ({
  variant = "yellow",
  shape = "square",
  size = "md",
  icon,
  className,
  children,
  ...props
}) => {
  const variantClasses = {
    red: "bg-[#D02020] text-white border-2 border-[#121212] shadow-[2px_2px_0px_0px_#121212]",
    blue: "bg-[#1040C0] text-white border-2 border-[#121212] shadow-[2px_2px_0px_0px_#121212]",
    yellow: "bg-[#F0C020] text-[#121212] border-2 border-[#121212] shadow-[2px_2px_0px_0px_#121212]",
    black: "bg-[#121212] text-white border-2 border-[#121212] shadow-[2px_2px_0px_0px_#D02020]",
    white: "bg-white text-[#121212] border-2 border-[#121212] shadow-[2px_2px_0px_0px_#121212]",
    outline: "bg-transparent text-[#121212] border-2 border-[#121212]",
  };

  const shapeClasses = {
    square: "rounded-none",
    pill: "rounded-full px-3.5",
  };

  const sizeClasses = {
    sm: "px-2 py-0.5 text-[10px] font-black tracking-wider uppercase",
    md: "px-2.5 py-1 text-xs font-black tracking-widest uppercase",
    lg: "px-3.5 py-1.5 text-sm font-black tracking-widest uppercase",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 select-none font-sans leading-none",
        variantClasses[variant],
        shapeClasses[shape],
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{children}</span>
    </span>
  );
};
