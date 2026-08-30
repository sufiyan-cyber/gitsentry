"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface BauhausButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "yellow" | "outline" | "ghost" | "dark";
  shape?: "square" | "pill";
  size?: "sm" | "md" | "lg" | "xl";
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  children: React.ReactNode;
}

export const BauhausButton = React.forwardRef<
  HTMLButtonElement,
  BauhausButtonProps
>(
  (
    {
      variant = "primary",
      shape = "square",
      size = "md",
      icon,
      iconPosition = "right",
      className,
      children,
      ...props
    },
    ref
  ) => {
    const variantStyles = {
      primary:
        "bg-[#D02020] text-white border-2 md:border-4 border-[#121212] shadow-[4px_4px_0px_0px_#121212] md:shadow-[6px_6px_0px_0px_#121212] hover:bg-[#D02020]/90",
      secondary:
        "bg-[#1040C0] text-white border-2 md:border-4 border-[#121212] shadow-[4px_4px_0px_0px_#121212] md:shadow-[6px_6px_0px_0px_#121212] hover:bg-[#1040C0]/90",
      yellow:
        "bg-[#F0C020] text-[#121212] border-2 md:border-4 border-[#121212] shadow-[4px_4px_0px_0px_#121212] md:shadow-[6px_6px_0px_0px_#121212] hover:bg-[#F0C020]/90",
      outline:
        "bg-white text-[#121212] border-2 md:border-4 border-[#121212] shadow-[4px_4px_0px_0px_#121212] md:shadow-[6px_6px_0px_0px_#121212] hover:bg-neutral-100",
      ghost:
        "bg-transparent text-[#121212] border-2 border-transparent shadow-none hover:bg-black/10",
      dark:
        "bg-[#121212] text-white border-2 md:border-4 border-[#121212] shadow-[4px_4px_0px_0px_#D02020] md:shadow-[6px_6px_0px_0px_#D02020] hover:bg-neutral-800",
    };

    const shapeStyles = {
      square: "rounded-none",
      pill: "rounded-full",
    };

    const sizeStyles = {
      sm: "px-3 py-1.5 text-xs font-bold tracking-wider",
      md: "px-5 py-2.5 text-sm font-bold tracking-wider",
      lg: "px-7 py-3.5 text-base font-extrabold tracking-widest",
      xl: "px-9 py-4.5 text-lg font-black tracking-widest",
    };

    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-2.5 uppercase font-bold select-none cursor-pointer transition-all duration-150 ease-out",
          "active:translate-x-[2px] active:translate-y-[2px] active:shadow-none focus:outline-none focus-visible:ring-2 focus-visible:ring-[#121212] focus-visible:ring-offset-2",
          "disabled:opacity-50 disabled:pointer-events-none disabled:active:translate-x-0 disabled:active:translate-y-0",
          variantStyles[variant],
          shapeStyles[shape],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {icon && iconPosition === "left" && (
          <span className="inline-flex shrink-0">{icon}</span>
        )}
        <span>{children}</span>
        {icon && iconPosition === "right" && (
          <span className="inline-flex shrink-0">{icon}</span>
        )}
      </button>
    );
  }
);

BauhausButton.displayName = "BauhausButton";
