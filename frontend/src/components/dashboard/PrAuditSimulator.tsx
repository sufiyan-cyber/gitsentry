"use client";

import React, { useState, useEffect } from "react";
import { SAMPLE_PRS, PullRequestScenario } from "@/lib/mockData";
import { checkBackendHealth, runLiveBeat, fetchLiveEvents, fetchLivePRs } from "@/lib/api";
import { BauhausCard } from "@/components/ui/BauhausCard";
import { BauhausButton } from "@/components/ui/BauhausButton";
import { BauhausBadge } from "@/components/ui/BauhausBadge";
import {
  CheckCircle2,
  ShieldAlert,
  Terminal,
  Cpu,
  Database,
  GitPullRequest,
  RefreshCw,
  Sparkles,
  Lock,
  Unlock,
  Radio,
  Server,
  Zap,
} from "lucide-react";

export const PrAuditSimulator: React.FC = () => {
  const [livePrList, setLivePrList] = useState<any[]>([]);
  const [selectedPr, setSelectedPr] = useState<PullRequestScenario>(
    SAMPLE_PRS[0]
  );
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(4);
  const [backendConnected, setBackendConnected] = useState<boolean>(false);
  const [liveBackendLogs, setLiveBackendLogs] = useState<string>("");
  const [liveEvents, setLiveEvents] = useState<any[]>([]);
  const [commitStatus, setCommitStatus] = useState<"failure" | "success">(
    SAMPLE_PRS[0].commitGateStatus as "failure" | "success"
  );
  const [remediationApplied, setRemediationApplied] = useState<boolean>(false);

  useEffect(() => {
    checkBackendHealth().then((isHealthy) => setBackendConnected(isHealthy));
    fetchLiveEvents().then((events) => setLiveEvents(events));
    fetchLivePRs().then((prs) => {
      if (prs && prs.length > 0) {
        setLivePrList(prs);
        setSelectedPr(prs[0]);
      }
    });

    const pollInterval = setInterval(() => {
      fetchLiveEvents().then((events) => {
        if (events && events.length > 0) setLiveEvents(events);
      });
      fetchLivePRs().then((prs) => {
        if (prs && prs.length > 0) {
          setLivePrList(prs);
        }
      });
      checkBackendHealth().then((isHealthy) => setBackendConnected(isHealthy));
    }, 2500);

    return () => clearInterval(pollInterval);
  }, []);

  const displayedPrs = livePrList.length > 0 ? livePrList : SAMPLE_PRS;

  const simulationSteps = [
    {
      title: "Webhook Ingestion & HMAC Verification",
      icon: <CheckCircle2 className="w-4 h-4 text-green-500" />,
      detail: "Cloud Run Receiver verified X-Hub-Signature-256 in 4ms -> Pub/Sub published.",
    },
    {
      title: "Gemini 3.7 Flash Low-Tier Triage (<200ms)",
      icon: <Cpu className="w-4 h-4 text-[#F0C020]" />,
      detail: selectedPr.geminiTriage.lowThinkingSummary,
    },
    {
      title: "Firestore Memory Bank & OSV.dev Lookup",
      icon: <Database className="w-4 h-4 text-[#1040C0]" />,
      detail: selectedPr.memoryMatch.decisionHit
        ? `Recalled Decision ${selectedPr.memoryMatch.decisionHit.id}: "${selectedPr.memoryMatch.decisionHit.description}"`
        : selectedPr.memoryMatch.habitHit
        ? `Detected Dev Habit for @${selectedPr.memoryMatch.habitHit.author} (${selectedPr.memoryMatch.habitHit.occurrencesCount} past occurrences)`
        : "Scanned OSV.dev vulnerability index; matched GHSA-w787-c79q-63p3 (CVE-2023-45803).",
    },
    {
      title: "Gemini 3.7 Flash Deep Audit (thinking_level=HIGH)",
      icon: <Sparkles className="w-4 h-4 text-[#D02020]" />,
      detail: "Full AST flow reasoning, severity evaluation, and auto-patch synthesis complete.",
    },
    {
      title: "Enforcement: Commit Gate & Remediation PR",
      icon: <GitPullRequest className="w-4 h-4 text-white" />,
      detail:
        commitStatus === "failure"
          ? `Gated merge: gitsentry/security = FAILED. Remediation branch '${selectedPr.remediationPR.branch}' opened.`
          : `Gated merge: gitsentry/security = SUCCESS. All compliance gates cleared.`,
    },
  ];

  const runSimulation = async (prToRun = selectedPr) => {
    setIsRunning(true);
    setCurrentStepIndex(0);
    setRemediationApplied(false);
    setCommitStatus(prToRun.commitGateStatus as "failure" | "success");
    setLiveBackendLogs("");

    // If live FastAPI backend is connected, execute beat
    if (backendConnected) {
      const beatNum = prToRun.id === "pr-42" ? 1 : prToRun.id === "pr-43" ? 2 : 3;
      runLiveBeat(beatNum).then((res) => {
        if (res && res.log) setLiveBackendLogs(res.log);
      });
    }

    let step = 0;
    const interval = setInterval(() => {
      step += 1;
      setCurrentStepIndex(step);
      if (step >= simulationSteps.length - 1) {
        clearInterval(interval);
        setIsRunning(false);
      }
    }, 550);
  };

  const handleSelectScenario = (pr: PullRequestScenario) => {
    setSelectedPr(pr);
    setRemediationApplied(false);
    setCommitStatus(pr.commitGateStatus as "failure" | "success");
    runSimulation(pr);
  };

  const handleApplyRemediation = () => {
    setRemediationApplied(true);
    setCommitStatus("success");
  };

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="bg-[#121212] text-white p-6 md:p-8 border-2 md:border-4 border-black shadow-[6px_6px_0px_0px_#D02020] flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-[#D02020]" />
            <span className="text-xs font-black uppercase tracking-widest text-[#F0C020]">
              INTERACTIVE CO-PILOT SIMULATOR
            </span>
            <div className="ml-2 inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-black uppercase border border-neutral-700 bg-neutral-900">
              <Server className="w-3 h-3 text-[#F0C020]" />
              <span>
                BACKEND:{" "}
                {backendConnected ? (
                  <span className="text-green-400">FASTAPI LIVE (:8080)</span>
                ) : (
                  <span className="text-neutral-400">STANDALONE / MOCK</span>
                )}
              </span>
            </div>
          </div>
          <h2 className="text-2xl md:text-3xl font-black uppercase tracking-tight">
            PR Security Triage & Audit Workbench
          </h2>
          <p className="text-xs md:text-sm text-neutral-300">
            Select a live scenario to witness two-tier Gemini reasoning and stateful memory in action.
          </p>
        </div>

        <BauhausButton
          variant="yellow"
          shape="square"
          size="md"
          onClick={() => runSimulation()}
          disabled={isRunning}
          icon={
            <RefreshCw
              className={`w-4 h-4 stroke-[2.5] ${isRunning ? "animate-spin" : ""}`}
            />
          }
        >
          {isRunning ? "Auditing PR..." : "Re-Run Audit"}
        </BauhausButton>
      </div>

      {/* Live GitHub Webhook Event Ticker */}
      {liveEvents.length > 0 ? (
        <div className="bg-[#FFF9C4] border-2 md:border-4 border-black p-4 shadow-[4px_4px_0px_0px_#121212] flex items-center justify-between gap-4 animate-pulse">
          <div className="flex items-center gap-3">
            <span className="w-3 h-3 rounded-full bg-green-500 animate-ping" />
            <div className="text-xs font-mono">
              <span className="font-black uppercase bg-black text-white px-2 py-0.5 mr-2">
                ⚡ LIVE GITHUB WEBHOOK
              </span>
              <span className="font-bold text-black">
                {liveEvents[0].repo} — PR #{liveEvents[0].pr_number} ({liveEvents[0].action}) by @{liveEvents[0].author}
              </span>
              <span className="text-neutral-600 ml-2 font-normal">
                [{liveEvents[0].timestamp}]
              </span>
            </div>
          </div>
          <span className="text-[10px] font-black uppercase px-2 py-0.5 bg-green-600 text-white">
            RECEIVED VIA CLOUD RUN
          </span>
        </div>
      ) : (
        <div className="bg-white border-2 border-black p-3 text-xs font-mono text-neutral-600 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-green-500" />
            <span>Webhook Receiver Active: Listening for live PRs on <strong>sufiyantesting789/production-web</strong></span>
          </div>
          <span className="text-[10px] font-black uppercase bg-neutral-200 px-2 py-0.5">POLLING EVERY 2.5S</span>
        </div>
      )}

      {/* PR Scenario Selector Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {displayedPrs.map((pr) => {
          const isSelected = selectedPr.id === pr.id;
          return (
            <button
              key={pr.id}
              onClick={() => handleSelectScenario(pr)}
              className={`p-4 text-left border-2 md:border-4 border-black transition-all cursor-pointer select-none ${
                isSelected
                  ? "bg-[#D02020] text-white shadow-[6px_6px_0px_0px_#121212] -translate-y-1"
                  : "bg-white text-[#121212] shadow-[3px_3px_0px_0px_#121212] hover:-translate-y-0.5"
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-2">
                <span
                  className={`text-xs font-black px-2 py-0.5 uppercase ${
                    isSelected ? "bg-black text-white" : "bg-[#F0F0F0] text-black"
                  }`}
                >
                  PR #{pr.prNumber}
                </span>
                <span
                  className={`text-[10px] font-black uppercase px-2 py-0.5 ${
                    pr.riskTier === "HIGH"
                      ? isSelected
                        ? "bg-[#F0C020] text-black"
                        : "bg-[#D02020] text-white"
                      : "bg-[#1040C0] text-white"
                  }`}
                >
                  {pr.riskTier} RISK
                </span>
              </div>
              <p className="font-extrabold text-sm uppercase leading-tight line-clamp-2">
                {pr.title}
              </p>
              <p className="mt-2 text-xs font-mono opacity-80 truncate">
                {pr.repo}
              </p>
            </button>
          );
        })}
      </div>

      {/* Main Audit Console Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Live Execution Pipeline Timeline */}
        <div className="lg:col-span-6 space-y-6">
          <BauhausCard
            shapeBadge="circle"
            badgeColor="red"
            borderWidth="4"
            className="p-6 md:p-8 bg-white"
          >
            <div className="flex items-center justify-between pb-4 mb-6 border-b-2 border-black">
              <div className="flex items-center gap-2">
                <Terminal className="w-5 h-5 text-[#D02020]" />
                <h3 className="font-black text-lg md:text-xl uppercase tracking-tight">
                  Stateful Execution Pipeline
                </h3>
              </div>
              <span className="text-xs font-black uppercase px-2 py-0.5 bg-black text-[#F0C020]">
                {isRunning ? "PROCESSING" : "COMPLETED"}
              </span>
            </div>

            {/* Pipeline Step Indicators */}
            <div className="space-y-4">
              {simulationSteps.map((step, idx) => {
                const isActive = currentStepIndex === idx;
                const isPassed = currentStepIndex >= idx;

                return (
                  <div
                    key={step.title}
                    className={`p-3.5 border-2 border-black transition-all ${
                      isActive
                        ? "bg-[#FFF9C4] shadow-[4px_4px_0px_0px_#121212] -translate-x-1"
                        : isPassed
                        ? "bg-[#F0F0F0] opacity-100"
                        : "bg-white opacity-40"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="font-black text-xs">0{idx + 1}.</span>
                        <span className="font-extrabold text-xs md:text-sm uppercase tracking-tight">
                          {step.title}
                        </span>
                      </div>
                      {isPassed && step.icon}
                    </div>
                    <p className="text-xs font-mono text-neutral-700 pl-6 leading-relaxed">
                      {step.detail}
                    </p>
                  </div>
                );
              })}
            </div>

            {/* Live Backend Output if available */}
            {liveBackendLogs && (
              <div className="mt-6 pt-4 border-t-2 border-black">
                <div className="flex items-center gap-2 mb-2">
                  <Radio className="w-3.5 h-3.5 text-[#D02020] animate-pulse" />
                  <span className="text-[11px] font-black uppercase tracking-wider text-black">
                    Live FastAPI Worker Stream:
                  </span>
                </div>
                <div className="bg-black text-green-400 p-3 font-mono text-xs overflow-x-auto whitespace-pre-wrap leading-tight border border-black">
                  {liveBackendLogs}
                </div>
              </div>
            )}
          </BauhausCard>
        </div>

        {/* Right Column: Deep Security Audit & Commit Gate */}
        <div className="lg:col-span-6 space-y-6">
          {/* Commit Status Gate Badge */}
          <div
            className={`p-6 border-2 md:border-4 border-black shadow-[6px_6px_0px_0px_#121212] text-white flex items-center justify-between transition-colors ${
              commitStatus === "failure" ? "bg-[#D02020]" : "bg-[#1040C0]"
            }`}
          >
            <div className="flex items-center gap-3">
              {commitStatus === "failure" ? (
                <div className="p-2 bg-black text-white border-2 border-white">
                  <Lock className="w-6 h-6 stroke-[2.5]" />
                </div>
              ) : (
                <div className="p-2 bg-[#F0C020] text-black border-2 border-black">
                  <Unlock className="w-6 h-6 stroke-[2.5]" />
                </div>
              )}
              <div>
                <span className="text-[11px] font-black uppercase tracking-widest text-[#F0C020]">
                  GITHUB COMMIT STATUS: gitsentry/security
                </span>
                <h4 className="text-xl md:text-2xl font-black uppercase tracking-tight">
                  {commitStatus === "failure"
                    ? "MERGE BLOCKED (HIGH RISK)"
                    : "MERGE CLEARED (PASSED AUDIT)"}
                </h4>
              </div>
            </div>

            <div className="text-right hidden sm:block">
              <span className="text-xs font-mono font-bold block">
                PR #{selectedPr.prNumber}
              </span>
              <span className="text-[10px] uppercase font-black">
                {selectedPr.branch}
              </span>
            </div>
          </div>

          {/* Autonomous Remediation Action Card */}
          <BauhausCard
            shapeBadge="square"
            badgeColor="blue"
            borderWidth="4"
            className="p-6 md:p-8 bg-white space-y-4"
          >
            <div className="flex items-center justify-between pb-3 border-b-2 border-black">
              <div className="flex items-center gap-2">
                <GitPullRequest className="w-5 h-5 text-[#1040C0]" />
                <h3 className="font-black text-lg uppercase tracking-tight">
                  Autonomous Remediation
                </h3>
              </div>
              <span
                className={`text-[10px] font-black uppercase px-2 py-0.5 border border-black ${
                  remediationApplied
                    ? "bg-[#1040C0] text-white"
                    : "bg-[#F0C020] text-black"
                }`}
              >
                {remediationApplied ? "APPLIED & VERIFIED" : "READY TO MERGE"}
              </span>
            </div>

            <div>
              <p className="text-xs font-bold uppercase text-[#121212] mb-1">
                Target: {selectedPr.remediationPR.title}
              </p>
              <p className="text-xs font-mono text-neutral-600 mb-3">
                Branch: {selectedPr.remediationPR.branch}
              </p>

              {/* Unified Diff View */}
              <div className="bg-black text-[#F0F0F0] p-4 border-2 border-black font-mono text-xs overflow-x-auto">
                <pre className="text-neutral-300">
                  {selectedPr.remediationPR.diffSnippet}
                </pre>
              </div>
            </div>

            {/* Action Bar */}
            <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3">
              {commitStatus === "failure" && !remediationApplied ? (
                <BauhausButton
                  variant="primary"
                  shape="square"
                  size="md"
                  onClick={handleApplyRemediation}
                  className="w-full sm:w-auto"
                  icon={<CheckCircle2 className="w-4 h-4 stroke-[3]" />}
                >
                  Merge Remediation PR & Clear Gate
                </BauhausButton>
              ) : (
                <div className="flex items-center gap-2 text-xs font-black uppercase text-green-700 bg-green-100 p-2.5 border-2 border-green-700 w-full">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>
                    Remediation PR applied. Commit status &apos;gitsentry/security&apos; is SUCCESS.
                  </span>
                </div>
              )}
            </div>
          </BauhausCard>
        </div>
      </div>
    </div>
  );
};
