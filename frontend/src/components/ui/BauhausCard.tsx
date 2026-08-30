"use client";

import React from "react";
import { cn } from "@/lib/utils";

export type GeometricBadgeShape = "circle" | "square" | "triangle" | "none";
export type GeometricBadgeColor = "red" | "blue" | "yellow" | "black" | "white";

export interface BauhausCardProps extends React.HTMLAttributes<HTMLDivElement> {
  shapeBadge?: GeometricBadgeShape;
  badgeColor?: GeometricBadgeColor;
  badgePosition?: "top-right" | "top-left";
  hoverLift?: boolean;
  colorScheme?: "white" | "yellow" | "blue" | "red" | "dark" | "canvas";
  borderWidth?: "2" | "4";
}

export const BauhausCard = React.forwardRef<HTMLDivElement, BauhausCardProps>(
  (
    {
      children,
      className,
      shapeBadge = "circle",
      badgeColor = "red",
      badgePosition = "top-right",
      hoverLift = true,
      colorScheme = "white",
      borderWidth = "4",
      ...props
    },
    ref
  ) => {
    const colorStyles = {
      white: "bg-white text-[#121212]",
      yellow: "bg-[#F0C020] text-[#121212]",
      blue: "bg-[#1040C0] text-white",
      red: "bg-[#D02020] text-white",
      dark: "bg-[#121212] text-white",
      canvas: "bg-[#F0F0F0] text-[#121212]",
    };

    const badgeColorClasses = {
      red: "bg-[#D02020]",
      blue: "bg-[#1040C0]",
      yellow: "bg-[#F0C020]",
      black: "bg-[#121212]",
      white: "bg-white",
    };

    const renderBadge = () => {
      if (shapeBadge === "none") return null;

      const baseClasses = cn(
        "w-4 h-4 md:w-5 md:h-5 transition-transform duration-200 group-hover:scale-125 border border-black",
        badgeColorClasses[badgeColor]
      );

      if (shapeBadge === "circle") {
        return <div className={cn(baseClasses, "rounded-full")} />;
      }
      if (shapeBadge === "square") {
        return <div className={cn(baseClasses, "rounded-none")} />;
      }
      if (shapeBadge === "triangle") {
        return (
          <div
            className={cn(baseClasses, "clip-triangle border-none")}
            style={{
              backgroundColor:
                badgeColor === "red"
                  ? "#D02020"
                  : badgeColor === "blue"
                  ? "#1040C0"
                  : badgeColor === "yellow"
                  ? "#F0C020"
                  : badgeColor === "white"
                  ? "#FFFFFF"
                  : "#121212",
            }}
          />
        );
      }
      return null;
    };

    return (
      <div
        ref={ref}
        className={cn(
          "group relative rounded-none transition-all duration-200 ease-out",
          borderWidth === "4" ? "border-2 md:border-4 border-[#121212]" : "border-2 border-[#121212]",
          "shadow-[4px_4px_0px_0px_#121212] md:shadow-[8px_8px_0px_0px_#121212]",
          hoverLift && "hover:-translate-y-1.5 md:hover:-translate-y-2 hover:shadow-[6px_6px_0px_0px_#121212] md:hover:shadow-[12px_12px_0px_0px_#121212]",
          colorStyles[colorScheme],
          className
        )}
        {...props}
      >
        {shapeBadge !== "none" && (
          <div
            className={cn(
              "absolute top-3.5 z-10",
              badgePosition === "top-right" ? "right-3.5" : "left-3.5"
            )}
          >
            {renderBadge()}
          </div>
        )}
        {children}
      </div>
    );
  }
);

BauhausCard.displayName = "BauhausCard";
