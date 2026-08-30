import React from "react";
import { Navbar } from "@/components/landing/Navbar";
import { HeroSection } from "@/components/landing/HeroSection";
import { StatsStrip } from "@/components/landing/StatsStrip";
import { ArchitectureFlow } from "@/components/landing/ArchitectureFlow";
import { FeaturesGrid } from "@/components/landing/FeaturesGrid";
import { ThreatStream } from "@/components/landing/ThreatStream";
import { FaqSection } from "@/components/landing/FaqSection";
import { CtaSection } from "@/components/landing/CtaSection";
import { Footer } from "@/components/landing/Footer";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#F0F0F0] text-[#121212] flex flex-col font-sans">
      <Navbar />
      <HeroSection />
      <StatsStrip />
      <ArchitectureFlow />
      <FeaturesGrid />
      <ThreatStream />
      <FaqSection />
      <CtaSection />
      <Footer />
    </main>
  );
}
