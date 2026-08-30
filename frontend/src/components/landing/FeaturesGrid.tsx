"use client";

import React from "react";
import { BauhausCard } from "@/components/ui/BauhausCard";
import {
  Brain,
  History,
  ShieldAlert,
  GitPullRequest,
  Lock,
  UserCheck,
} from "lucide-react";

export const FeaturesGrid: React.FC = () => {
  const capabilities = [
    {
      id: "cap-1",
      title: "Stateful Decision Memory Bank",
      shape: "circle" as const,
      badgeColor: "red" as const,
      icon: <History className="w-6 h-6 text-[#D02020]" />,
      summary:
        "Remembers past architectural approvals, security exemptions, and RFCs across repos in Firestore so developers never re-litigate approved designs.",
      meta: "Firestore Collection: /decisions",
    },
    {
      id: "cap-2",
      title: "Developer Habit Profiler",
      shape: "square" as const,
      badgeColor: "blue" as const,
      icon: <Brain className="w-6 h-6 text-[#1040C0]" />,
      summary:
        "Continuously detects recurring developer patterns (e.g. raw string SQL concatenation or wildcard CORS) and delivers targeted coaching in PR reviews.",
      meta: "Firestore Collection: /dev_habits",
    },
    {
      id: "cap-3",
      title: "OSV.dev CVE Automated Patching",
      shape: "triangle" as const,
      badgeColor: "yellow" as const,
      icon: <ShieldAlert className="w-6 h-6 text-black" />,
      summary:
        "Scans dependencies on every PR against Google's open-source OSV.dev vulnerability database and computes minimum safe version bumps.",
      meta: "OSV.dev REST API Integration",
    },
    {
      id: "cap-4",
      title: "Strict Commit Status Merge Gating",
      shape: "circle" as const,
      badgeColor: "red" as const,
      icon: <Lock className="w-6 h-6 text-[#D02020]" />,
      summary:
        "Sets 'gitsentry/security' GitHub commit status checks to failure on high risks, physically preventing merge until resolved or formally overridden.",
      meta: "GitHub Commit Status API",
    },
    {
      id: "cap-5",
      title: "Autonomous Remediation PRs",
      shape: "square" as const,
      badgeColor: "blue" as const,
      icon: <GitPullRequest className="w-6 h-6 text-[#1040C0]" />,
      summary:
        "Generates clean unified git diffs, creates a dedicated remediation branch, and opens a companion pull request ready for one-click merge.",
      meta: "GitHub App Octokit Engine",
    },
    {
      id: "cap-6",
      title: "Human-in-the-Loop Override Flow",
      shape: "triangle" as const,
      badgeColor: "yellow" as const,
      icon: <UserCheck className="w-6 h-6 text-black" />,
      summary:
        "Developers can tag @gitsentry with approved business justifications in PR comments; GitSentry evaluates validity before clearing commit status.",
      meta: "Two-Way Issue Comment Webhook",
    },
  ];

  return (
    <section
      id="features"
      className="bg-[#D02020] border-b-2 md:border-b-4 border-[#121212] py-16 md:py-24 relative overflow-hidden"
    >
      {/* Background Constructivist Patterns */}
      <div className="absolute inset-0 bg-dot-grid-white opacity-15 pointer-events-none" />
      <div className="absolute -bottom-20 -right-20 w-80 h-80 rounded-full border-8 border-black/20 pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section Header with Inverted Theme */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 md:mb-16 gap-6 pb-6 border-b-2 md:border-b-4 border-[#121212]">
          <div className="space-y-3 text-white">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-none bg-[#F0C020] border border-black" />
              <span className="text-xs font-black uppercase tracking-widest text-white">
                CORE CAPABILITIES
              </span>
            </div>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-black uppercase tracking-tighter text-white leading-[0.9]">
              AUTONOMOUS
              <br />
              SECURITY POWERS<span className="text-[#F0C020]">.</span>
            </h2>
          </div>

          <div className="bg-white p-4 border-2 md:border-4 border-black shadow-[4px_4px_0px_0px_#121212] max-w-md">
            <p className="text-xs md:text-sm font-extrabold uppercase tracking-tight text-[#121212]">
              FORM FOLLOWS FUNCTION: Every security check produces actionable,
              auditable, and enforceable code fixes.
            </p>
          </div>
        </div>

        {/* 6 Capabilities Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
          {capabilities.map((item) => (
            <BauhausCard
              key={item.id}
              shapeBadge={item.shape}
              badgeColor={item.badgeColor}
              borderWidth="4"
              className="p-6 md:p-8 bg-white flex flex-col justify-between"
            >
              <div>
                {/* Icon in white bordered container */}
                <div className="mb-5 inline-block p-3 bg-[#F0F0F0] border-2 border-black shadow-[3px_3px_0px_0px_#121212]">
                  {item.icon}
                </div>

                <h3 className="text-xl md:text-2xl font-black uppercase tracking-tight text-[#121212] mb-3">
                  {item.title}
                </h3>

                <p className="text-sm font-medium text-[#121212]/90 leading-relaxed mb-6">
                  {item.summary}
                </p>
              </div>

              <div className="pt-4 border-t-2 border-black flex items-center justify-between">
                <span className="text-[11px] font-black uppercase tracking-wider text-[#1040C0]">
                  {item.meta}
                </span>
                <span className="w-2 h-2 rounded-full bg-[#D02020]" />
              </div>
            </BauhausCard>
          ))}
        </div>
      </div>
    </section>
  );
};
