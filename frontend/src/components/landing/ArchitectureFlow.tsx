"use client";

import React from "react";
import { BauhausBadge } from "@/components/ui/BauhausBadge";
import { BauhausCard } from "@/components/ui/BauhausCard";
import {
  Webhook,
  Cpu,
  GitPullRequest,
  ArrowRight,
  ShieldCheck,
  Flame,
  Radio,
} from "lucide-react";

export const ArchitectureFlow: React.FC = () => {
  const steps = [
    {
      stepNumber: "01",
      title: "Decoupled Webhook Ingestion",
      subtitle: "Cloud Run Receiver + HMAC-SHA256 + Pub/Sub",
      badge: "SUB-10MS LATENCY",
      badgeVariant: "red" as const,
      shape: "circle" as const,
      colorScheme: "white" as const,
      description:
        "GitHub PR events arrive at the Webhook Receiver. Signatures are verified with constant-time HMAC comparison before instant publishing to the 'pr-events' Pub/Sub queue, eliminating webhook timeouts.",
      tags: ["HMAC Verification", "Pub/Sub Decoupled", "Secret Manager"],
      icon: <Webhook className="w-6 h-6 text-[#D02020]" />,
    },
    {
      stepNumber: "02",
      title: "Two-Tier Gemini Reasoning",
      subtitle: "Gemini 3.7 Flash (Low & High Thinking) + ADK",
      badge: "STATEFUL INTELLIGENCE",
      badgeVariant: "yellow" as const,
      shape: "square" as const,
      colorScheme: "white" as const,
      description:
        "Worker executes rapid triage (<200ms) with thinking_level=LOW. High-risk signals trigger deep threat audits with thinking_level=HIGH, cross-referencing Firestore Memory Bank and OSV.dev databases.",
      tags: ["thinking_level: HIGH", "Firestore Bank", "OSV.dev API"],
      icon: <Cpu className="w-6 h-6 text-[#1040C0]" />,
    },
    {
      stepNumber: "03",
      title: "Autonomous Action Engine",
      subtitle: "Remediation PR & Commit Gating",
      badge: "ACTIVE ENFORCEMENT",
      badgeVariant: "black" as const,
      shape: "triangle" as const,
      colorScheme: "white" as const,
      description:
        "Sets commit status 'gitsentry/security' to block unsafe merges. Generates precision patch diffs, creates a dedicated branch, and autonomously opens a ready-to-merge remediation PR.",
      tags: ["Commit Status Gating", "Auto-Remediation PR", "Audit Log"],
      icon: <GitPullRequest className="w-6 h-6 text-[#F0C020]" />,
    },
  ];

  return (
    <section
      id="architecture"
      className="relative bg-[#F0F0F0] border-b-2 md:border-b-4 border-[#121212] py-16 md:py-24"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 md:mb-16 gap-6 pb-6 border-b-2 md:border-b-4 border-[#121212]">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-[#D02020] border border-black" />
              <span className="text-xs font-black uppercase tracking-widest text-[#121212]">
                SYSTEM PIPELINE
              </span>
            </div>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-black uppercase tracking-tighter text-[#121212] leading-[0.9]">
              CONSTRUCTIVIST
              <br />
              ARCHITECTURE<span className="text-[#D02020]">.</span>
            </h2>
          </div>

          <p className="max-w-md text-sm md:text-base font-semibold text-[#121212]/80">
            A battle-tested serverless architecture on Google Cloud Platform
            engineered for resilience, strict zero-leak secret handling, and
            real-time GitHub integration.
          </p>
        </div>

        {/* 3-Step Pipeline Grid */}
        <div className="relative grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((step, idx) => (
            <BauhausCard
              key={step.stepNumber}
              shapeBadge={step.shape}
              badgeColor={idx === 0 ? "red" : idx === 1 ? "blue" : "yellow"}
              borderWidth="4"
              className="p-6 md:p-8 flex flex-col justify-between"
            >
              <div>
                {/* Step Number with 45° Rotated Box & Counter-Rotated Text */}
                <div className="flex items-center justify-between mb-6">
                  <div className="w-12 h-12 bg-[#121212] border-2 border-black rotate-45 flex items-center justify-center shadow-[3px_3px_0px_0px_#D02020] group-hover:rotate-90 transition-transform duration-300">
                    <span className="-rotate-45 group-hover:-rotate-90 transition-transform duration-300 text-white font-black text-sm tracking-widest">
                      {step.stepNumber}
                    </span>
                  </div>

                  <BauhausBadge variant={step.badgeVariant} size="sm">
                    {step.badge}
                  </BauhausBadge>
                </div>

                {/* Icon & Title */}
                <div className="space-y-2 mb-4">
                  <div className="p-2.5 inline-block bg-[#F0F0F0] border-2 border-black shadow-[2px_2px_0px_0px_#121212]">
                    {step.icon}
                  </div>
                  <h3 className="text-xl md:text-2xl font-black uppercase tracking-tight text-[#121212]">
                    {step.title}
                  </h3>
                  <p className="text-xs font-bold uppercase tracking-wider text-[#1040C0]">
                    {step.subtitle}
                  </p>
                </div>

                {/* Description */}
                <p className="text-sm font-medium text-[#121212]/90 leading-relaxed mb-6">
                  {step.description}
                </p>
              </div>

              {/* Tags */}
              <div className="pt-4 border-t-2 border-black flex flex-wrap gap-1.5">
                {step.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wider bg-neutral-100 border border-black"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </BauhausCard>
          ))}
        </div>
      </div>
    </section>
  );
};
