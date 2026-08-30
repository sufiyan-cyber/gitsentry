"use client";

import React, { useState } from "react";
import Link from "next/link";
import { SAMPLE_PRS, PullRequestScenario } from "@/lib/mockData";
import { BauhausCard } from "@/components/ui/BauhausCard";
import { BauhausBadge } from "@/components/ui/BauhausBadge";
import { BauhausButton } from "@/components/ui/BauhausButton";
import {
  ShieldAlert,
  CheckCircle2,
  GitBranch,
  Terminal,
  ArrowRight,
  ExternalLink,
} from "lucide-react";

export const ThreatStream: React.FC = () => {
  const [selectedPr, setSelectedPr] = useState<PullRequestScenario>(
    SAMPLE_PRS[0]
  );

  return (
    <section
      id="threat-stream"
      className="bg-[#1040C0] border-b-2 md:border-b-4 border-[#121212] py-16 md:py-24 text-white relative overflow-hidden"
    >
      {/* Background Constructivist Elements */}
      <div className="absolute inset-0 bg-dot-grid-white opacity-20 pointer-events-none" />
      <div className="absolute top-10 -right-20 w-72 h-72 rotate-45 border-8 border-white/15 pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 md:mb-16 gap-6 pb-6 border-b-2 md:border-b-4 border-white">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-[#F0C020] border border-black" />
              <span className="text-xs font-black uppercase tracking-widest text-[#F0C020]">
                REAL-TIME TELEMETRY
              </span>
            </div>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-black uppercase tracking-tighter text-white leading-[0.9]">
              LIVE AUDIT
              <br />
              THREAT STREAM<span className="text-[#F0C020]">.</span>
            </h2>
          </div>

          <p className="max-w-md text-sm md:text-base font-semibold text-white/90">
            Real PR security events processed live through Gemini 3.7 Flash
            two-tier reasoning, stateful memory recall, and OSV.dev lookup.
          </p>
        </div>

        {/* PR Selection Strip & Live Inspector */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left: PR List Selector */}
          <div className="lg:col-span-5 space-y-4">
            <div className="text-xs font-black uppercase tracking-widest text-[#F0C020] flex items-center justify-between pb-2 border-b-2 border-white/40">
              <span>SELECT PULL REQUEST EVENT</span>
              <span>3 DEMO SCENARIOS</span>
            </div>

            {SAMPLE_PRS.map((pr, idx) => {
              const isSelected = selectedPr.id === pr.id;
              return (
                <div
                  key={pr.id}
                  onClick={() => setSelectedPr(pr)}
                  className={`cursor-pointer transition-all duration-200 border-2 md:border-4 border-black p-5 text-left select-none ${
                    isSelected
                      ? "bg-[#F0C020] text-[#121212] shadow-[6px_6px_0px_0px_#FFFFFF] translate-x-2"
                      : "bg-white text-[#121212] shadow-[4px_4px_0px_0px_#121212] hover:-translate-y-1"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 text-xs font-black bg-black text-white uppercase tracking-wider">
                        PR #{pr.prNumber}
                      </span>
                      <span className="text-xs font-mono font-bold text-black/70">
                        @{pr.author}
                      </span>
                    </div>

                    <span
                      className={`text-[10px] font-black uppercase px-2 py-0.5 border border-black ${
                        pr.riskTier === "HIGH"
                          ? "bg-[#D02020] text-white"
                          : "bg-[#1040C0] text-white"
                      }`}
                    >
                      {pr.riskTier} RISK
                    </span>
                  </div>

                  <p className="font-extrabold text-sm md:text-base leading-snug uppercase tracking-tight line-clamp-2">
                    {pr.title}
                  </p>

                  <div className="mt-3 pt-2 border-t border-black/20 flex items-center justify-between text-xs font-semibold">
                    <span className="text-black/80 font-mono truncate max-w-[200px]">
                      {pr.repo}
                    </span>
                    <span className="font-black uppercase tracking-wider text-[11px] text-black">
                      {pr.geminiTriage.thinkingLevelUsed} THINKING
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right: Live Audit Terminal & Memory Match Details */}
          <div className="lg:col-span-7">
            <BauhausCard
              shapeBadge="triangle"
              badgeColor="yellow"
              borderWidth="4"
              colorScheme="dark"
              className="p-6 md:p-8 space-y-6"
            >
              {/* Header Bar */}
              <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b-2 border-neutral-700">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-[#D02020] text-white border-2 border-white">
                    <Terminal className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-black text-lg md:text-xl uppercase tracking-tight text-white">
                      Gemini 3.7 Flash Security Audit
                    </h3>
                    <p className="text-xs font-mono text-[#F0C020]">
                      Execution Latency: {selectedPr.geminiTriage.latencyMs}ms |
                      Tier: {selectedPr.geminiTriage.thinkingLevelUsed}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`px-3 py-1 text-xs font-black uppercase tracking-widest border-2 ${
                      selectedPr.commitGateStatus === "failure"
                        ? "bg-[#D02020] text-white border-white"
                        : "bg-[#F0C020] text-black border-black"
                    }`}
                  >
                    GATE:{" "}
                    {selectedPr.commitGateStatus === "failure"
                      ? "BLOCKED"
                      : "CLEARED"}
                  </span>
                </div>
              </div>

              {/* Triage & Audit Reasoning Output */}
              <div className="space-y-3">
                <div className="bg-neutral-900 border-2 border-neutral-700 p-4 font-mono text-xs text-neutral-200 whitespace-pre-wrap leading-relaxed">
                  {selectedPr.geminiTriage.highThinkingAnalysis}
                </div>
              </div>

              {/* Memory Bank Hit Indicator */}
              {selectedPr.memoryMatch.decisionHit && (
                <div className="bg-[#1040C0] text-white p-4 border-2 border-white space-y-1">
                  <span className="text-[10px] font-black uppercase tracking-widest text-[#F0C020]">
                    FIRESTORE DECISION RECALLED
                  </span>
                  <p className="text-sm font-bold">
                    {selectedPr.memoryMatch.decisionHit.id}:{" "}
                    {selectedPr.memoryMatch.decisionHit.description}
                  </p>
                  <p className="text-xs text-white/80">
                    Approved by:{" "}
                    {selectedPr.memoryMatch.decisionHit.approvedBy} in{" "}
                    {selectedPr.memoryMatch.decisionHit.prReference}
                  </p>
                </div>
              )}

              {selectedPr.memoryMatch.habitHit && (
                <div className="bg-[#D02020] text-white p-4 border-2 border-white space-y-1">
                  <span className="text-[10px] font-black uppercase tracking-widest text-[#F0C020]">
                    DEVELOPER HABIT PATTERN DETECTED
                  </span>
                  <p className="text-sm font-bold">
                    Author &apos;{selectedPr.memoryMatch.habitHit.author}&apos; has{" "}
                    {selectedPr.memoryMatch.habitHit.occurrencesCount} past
                    occurrences of:
                  </p>
                  <p className="text-xs font-mono text-white/90">
                    &quot;{selectedPr.memoryMatch.habitHit.pattern}&quot;
                  </p>
                </div>
              )}

              {/* Remediation Diff Snippet */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-black uppercase tracking-wider text-[#F0C020]">
                  <span>Autonomous Remediation PR Patch:</span>
                  <span className="font-mono text-white">
                    {selectedPr.remediationPR.branch}
                  </span>
                </div>
                <div className="bg-black border-2 border-neutral-600 p-3 font-mono text-[11px] text-green-400 overflow-x-auto leading-tight">
                  <pre>{selectedPr.remediationPR.diffSnippet}</pre>
                </div>
              </div>

              {/* Action Bar */}
              <div className="pt-4 border-t-2 border-neutral-700 flex flex-col sm:flex-row items-center justify-between gap-4">
                <span className="text-xs font-bold text-neutral-300">
                  Ready to test with your custom diffs?
                </span>
                <Link href="/dashboard" className="w-full sm:w-auto">
                  <BauhausButton
                    variant="yellow"
                    shape="square"
                    size="sm"
                    icon={<ExternalLink className="w-4 h-4 stroke-[3]" />}
                    className="w-full sm:w-auto"
                  >
                    Open Live Simulator
                  </BauhausButton>
                </Link>
              </div>
            </BauhausCard>
          </div>
        </div>
      </div>
    </section>
  );
};
