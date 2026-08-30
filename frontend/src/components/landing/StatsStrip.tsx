"use client";

import React from "react";
import { Zap, Database, BrainCircuit, ShieldBan } from "lucide-react";

export const StatsStrip: React.FC = () => {
  const stats = [
    {
      id: "stat-1",
      number: "0 SEC",
      label: "Webhook Ingestion Delay",
      detail: "Pub/Sub decoupled async queue",
      shape: "circle",
      icon: <Zap className="w-5 h-5 text-[#D02020]" />,
    },
    {
      id: "stat-2",
      number: "100%",
      label: "Architectural Memory Recall",
      detail: "Firestore stateful project history",
      shape: "square",
      icon: <Database className="w-5 h-5 text-[#1040C0]" />,
    },
    {
      id: "stat-3",
      number: "2-TIER",
      label: "Gemini 3.7 Flash Thinking",
      detail: "Low (Triage) & High (Deep Audit)",
      shape: "triangle",
      icon: <BrainCircuit className="w-5 h-5 text-black" />,
    },
    {
      id: "stat-4",
      number: "0",
      label: "Unblocked High-Risk PRs",
      detail: "Automated commit status gating",
      shape: "square",
      icon: <ShieldBan className="w-5 h-5 text-[#D02020]" />,
    },
  ];

  return (
    <section className="bg-[#F0C020] border-b-2 md:border-b-4 border-[#121212] overflow-hidden">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 divide-y-2 sm:divide-y-0 sm:divide-x-2 lg:divide-x-4 divide-[#121212]">
          {stats.map((stat, idx) => (
            <div
              key={stat.id}
              className="p-6 md:p-8 flex flex-col justify-between space-y-4 hover:bg-[#F0C020]/90 transition-colors relative group"
            >
              {/* Header with Geometric Shape and Icon */}
              <div className="flex items-center justify-between">
                <div className="p-2 bg-white border-2 border-black shadow-[2px_2px_0px_0px_#121212]">
                  {stat.icon}
                </div>

                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] font-black uppercase tracking-widest text-black/60">
                    METRIC // 0{idx + 1}
                  </span>
                  {stat.shape === "circle" && (
                    <div className="w-3.5 h-3.5 rounded-full bg-[#D02020] border border-black" />
                  )}
                  {stat.shape === "square" && (
                    <div className="w-3.5 h-3.5 rounded-none bg-[#1040C0] border border-black" />
                  )}
                  {stat.shape === "triangle" && (
                    <div className="w-3.5 h-3.5 clip-triangle bg-[#121212]" />
                  )}
                </div>
              </div>

              {/* Stat Value */}
              <div>
                <span className="block text-4xl sm:text-5xl lg:text-6xl font-black uppercase tracking-tighter text-[#121212] leading-none">
                  {stat.number}
                </span>
                <p className="mt-2 text-sm md:text-base font-extrabold uppercase tracking-tight text-[#121212]">
                  {stat.label}
                </p>
                <p className="mt-0.5 text-xs font-semibold text-[#121212]/80">
                  {stat.detail}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
