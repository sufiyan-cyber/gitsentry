export const BAUHAUS_COLORS = {
  canvas: "#F0F0F0",
  foreground: "#121212",
  primaryRed: "#D02020",
  primaryBlue: "#1040C0",
  primaryYellow: "#F0C020",
  border: "#121212",
  muted: "#E0E0E0",
  lightYellow: "#FFF9C4",
} as const;

export const SHAPES = ["circle", "square", "triangle"] as const;
export type ShapeType = (typeof SHAPES)[number];

export const BUTTON_VARIANTS = {
  primary: "bg-[#D02020] text-white border-2 lg:border-4 border-black shadow-[4px_4px_0px_0px_black] lg:shadow-[6px_6px_0px_0px_black] hover:bg-[#D02020]/90",
  secondary: "bg-[#1040C0] text-white border-2 lg:border-4 border-black shadow-[4px_4px_0px_0px_black] lg:shadow-[6px_6px_0px_0px_black] hover:bg-[#1040C0]/90",
  yellow: "bg-[#F0C020] text-black border-2 lg:border-4 border-black shadow-[4px_4px_0px_0px_black] lg:shadow-[6px_6px_0px_0px_black] hover:bg-[#F0C020]/90",
  outline: "bg-white text-black border-2 lg:border-4 border-black shadow-[4px_4px_0px_0px_black] lg:shadow-[6px_6px_0px_0px_black] hover:bg-gray-100",
  ghost: "border-none text-black hover:bg-black/10 shadow-none",
  dark: "bg-[#121212] text-white border-2 lg:border-4 border-black shadow-[4px_4px_0px_0px_black] lg:shadow-[6px_6px_0px_0px_black] hover:bg-neutral-800",
} as const;

export const SHAPE_VARIANTS = {
  square: "rounded-none",
  pill: "rounded-full",
} as const;
