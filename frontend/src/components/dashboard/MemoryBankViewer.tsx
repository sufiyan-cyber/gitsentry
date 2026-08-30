"use client";

import React, { useState, useEffect } from "react";
import {
  FIRESTORE_DECISIONS,
  FIRESTORE_HABITS,
  FirestoreDecision,
  FirestoreHabit,
} from "@/lib/mockData";
import { fetchLiveMemory, checkBackendHealth, resetBackendState } from "@/lib/api";
import { BauhausCard } from "@/components/ui/BauhausCard";
import { BauhausBadge } from "@/components/ui/BauhausBadge";
import { BauhausButton } from "@/components/ui/BauhausButton";
import {
  Database,
  History,
  Brain,
  ShieldCheck,
  Search,
  Plus,
  RotateCcw,
  Server,
} from "lucide-react";

export const MemoryBankViewer: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"decisions" | "habits">("decisions");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [decisions, setDecisions] = useState<FirestoreDecision[]>(FIRESTORE_DECISIONS);
  const [habits, setHabits] = useState<FirestoreHabit[]>(FIRESTORE_HABITS);
  const [backendConnected, setBackendConnected] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newDesc, setNewDesc] = useState("");
  const [newApprover, setNewApprover] = useState("");
  const [newPrRef, setNewPrRef] = useState("");

  const refreshFromBackend = async () => {
    try {
      const isHealthy = await checkBackendHealth();
      setBackendConnected(isHealthy);
      if (isHealthy) {
        const data = await fetchLiveMemory();
        if (data && data.decisions && data.decisions.length > 0) {
          setDecisions(
            data.decisions.map((d: any, idx: number) => ({
              id: d.id || `DEC-${100 + idx + 1}`,
              repo: data.repo_id || "gitsentry-core/production-service",
              description: d.description || "",
              approvedBy: d.approved_by || d.approvedBy || "SecOps Team",
              prReference: d.pr_reference || d.prReference || `PR #${idx + 1}`,
              createdAt: typeof d.created_at === "string" ? d.created_at.split("T")[0] : "2026-08-20",
              status: (d.status === "superseded" ? "superseded" : "active") as "active" | "superseded",
            }))
          );
        }
        if (data && data.habits && data.habits.length > 0) {
          setHabits(
            data.habits.map((h: any, idx: number) => ({
              authorId: h.author_id || h.authorId || (idx === 0 ? "dev-alice" : `developer_${idx + 1}`),
              pattern: h.pattern || "",
              occurrences: Array.isArray(h.occurrences) ? h.occurrences : ["PR #1"],
              firstSeen: typeof h.first_seen === "string" ? h.first_seen.split("T")[0] : "2026-01-10",
              lastSeen: typeof h.last_seen === "string" ? h.last_seen.split("T")[0] : "2026-08-28",
              riskLevel: "HIGH" as const,
            }))
          );
        }
      }
    } catch (e) {
      console.warn("Could not sync with live backend:", e);
    }
  };

  useEffect(() => {
    refreshFromBackend();
  }, []);

  const safeQuery = (searchQuery || "").toLowerCase();

  const filteredDecisions = (decisions || []).filter(
    (d) =>
      (d?.description || "").toLowerCase().includes(safeQuery) ||
      (d?.id || "").toLowerCase().includes(safeQuery) ||
      (d?.approvedBy || "").toLowerCase().includes(safeQuery)
  );

  const filteredHabits = (habits || []).filter(
    (h) =>
      (h?.authorId || "").toLowerCase().includes(safeQuery) ||
      (h?.pattern || "").toLowerCase().includes(safeQuery)
  );

  const handleReset = async () => {
    if (backendConnected) {
      await resetBackendState();
      await refreshFromBackend();
    } else {
      setDecisions(FIRESTORE_DECISIONS);
      setHabits(FIRESTORE_HABITS);
    }
  };

  const handleAddDecision = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDesc || !newApprover) return;

    const newDec: FirestoreDecision = {
      id: `DEC-${100 + decisions.length + 1}`,
      repo: "gitsentry-core/identity-service",
      description: newDesc,
      approvedBy: newApprover,
      prReference: newPrRef || "PR #50",
      createdAt: new Date().toISOString().split("T")[0],
      status: "active",
    };

    setDecisions([newDec, ...decisions]);
    setNewDesc("");
    setNewApprover("");
    setNewPrRef("");
    setShowAddModal(false);
  };

  return (
    <div className="space-y-6">
      {/* Header & Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b-2 md:border-b-4 border-black">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-[#1040C0] text-white border-2 border-black shadow-[3px_3px_0px_0px_#121212]">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl md:text-3xl font-black uppercase tracking-tight text-[#121212]">
                Firestore Memory Bank Explorer
              </h2>
              <span className="hidden md:inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-black uppercase border border-black bg-white">
                <Server className="w-3 h-3 text-[#1040C0]" />
                {backendConnected ? "LIVE FASTAPI SYNC" : "STANDALONE MEMORY"}
              </span>
            </div>
            <p className="text-xs md:text-sm font-semibold text-neutral-600">
              Collection path: <code className="font-mono text-black font-bold">projects/&#123;repo_id&#125;/...</code>
            </p>
          </div>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab("decisions")}
            className={`px-4 py-2 text-xs md:text-sm font-black uppercase tracking-wider border-2 border-black transition-all cursor-pointer ${
              activeTab === "decisions"
                ? "bg-[#D02020] text-white shadow-[3px_3px_0px_0px_#121212]"
                : "bg-white text-[#121212] hover:bg-neutral-100"
            }`}
          >
            Decisions ({decisions.length})
          </button>
          <button
            onClick={() => setActiveTab("habits")}
            className={`px-4 py-2 text-xs md:text-sm font-black uppercase tracking-wider border-2 border-black transition-all cursor-pointer ${
              activeTab === "habits"
                ? "bg-[#1040C0] text-white shadow-[3px_3px_0px_0px_#121212]"
                : "bg-white text-[#121212] hover:bg-neutral-100"
            }`}
          >
            Dev Habits ({habits.length})
          </button>
        </div>
      </div>

      {/* Search & Actions Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search architectural policies, authors, or CVE patterns..."
            className="w-full pl-10 pr-4 py-2.5 bg-white border-2 border-black shadow-[3px_3px_0px_0px_#121212] text-sm font-medium focus:outline-none focus:ring-2 focus:ring-black"
          />
        </div>

        <div className="flex items-center gap-2">
          <BauhausButton
            variant="outline"
            shape="square"
            size="md"
            icon={<RotateCcw className="w-3.5 h-3.5" />}
            onClick={handleReset}
          >
            Reset
          </BauhausButton>

          {activeTab === "decisions" && (
            <BauhausButton
              variant="yellow"
              shape="square"
              size="md"
              icon={<Plus className="w-4 h-4 stroke-[3]" />}
              onClick={() => setShowAddModal(true)}
            >
              Add Exemption
            </BauhausButton>
          )}
        </div>
      </div>

      {/* Decisions View */}
      {activeTab === "decisions" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDecisions.length === 0 ? (
            <div className="col-span-full p-8 text-center bg-white border-2 border-black">
              <p className="text-sm font-bold uppercase text-neutral-500">
                No architectural decisions matched your search.
              </p>
            </div>
          ) : (
            filteredDecisions.map((item) => (
              <BauhausCard
                key={item.id}
                shapeBadge="circle"
                badgeColor="red"
                borderWidth="4"
                className="p-6 bg-white flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="px-2.5 py-1 text-xs font-black uppercase bg-[#121212] text-[#F0C020] border border-black">
                      {item.id}
                    </span>
                    <span className="text-[10px] font-black uppercase px-2 py-0.5 bg-green-100 text-green-800 border border-green-800">
                      {item.status}
                    </span>
                  </div>

                  <p className="font-extrabold text-sm md:text-base leading-snug uppercase tracking-tight text-[#121212] mb-4">
                    {item.description}
                  </p>
                </div>

                <div className="pt-4 border-t-2 border-black space-y-1 text-xs">
                  <div className="flex items-center justify-between text-neutral-600 font-semibold">
                    <span>Approved By:</span>
                    <span className="font-bold text-black">{item.approvedBy}</span>
                  </div>
                  <div className="flex items-center justify-between text-neutral-600 font-semibold">
                    <span>Origin PR:</span>
                    <span className="font-mono font-bold text-[#1040C0]">
                      {item.prReference}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-neutral-600 font-semibold">
                    <span>Recorded Date:</span>
                    <span className="font-mono">{item.createdAt}</span>
                  </div>
                </div>
              </BauhausCard>
            ))
          )}
        </div>
      )}

      {/* Habits View */}
      {activeTab === "habits" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {filteredHabits.length === 0 ? (
            <div className="col-span-full p-8 text-center bg-white border-2 border-black">
              <p className="text-sm font-bold uppercase text-neutral-500">
                No developer habit records matched your search.
              </p>
            </div>
          ) : (
            filteredHabits.map((habit, idx) => (
              <BauhausCard
                key={`${habit.authorId}-${idx}`}
                shapeBadge="square"
                badgeColor="blue"
                borderWidth="4"
                className="p-6 bg-white flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-sm font-black font-mono bg-[#1040C0] text-white px-2.5 py-1">
                      @{habit.authorId}
                    </span>
                    <span className="text-[10px] font-black uppercase px-2 py-0.5 bg-[#D02020] text-white border border-black">
                      {habit.riskLevel || "HIGH"} HABIT
                    </span>
                  </div>

                  <p className="text-xs font-bold uppercase tracking-wide text-neutral-500 mb-1">
                    Detected Code Pattern:
                  </p>
                  <p className="font-mono text-xs bg-neutral-100 p-2.5 border border-black text-[#121212] mb-4">
                    &quot;{habit.pattern}&quot;
                  </p>
                </div>

                <div className="pt-4 border-t-2 border-black space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-neutral-600">Past PR Instances:</span>
                    <div className="flex gap-1">
                      {(habit.occurrences || []).map((pr) => (
                        <span
                          key={pr}
                          className="px-1.5 py-0.5 bg-[#121212] text-white font-mono text-[10px] font-bold"
                        >
                          {pr}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-neutral-600">
                    <span>Last Seen:</span>
                    <span className="font-mono font-bold">{habit.lastSeen}</span>
                  </div>
                </div>
              </BauhausCard>
            ))
          )}
        </div>
      )}

      {/* Add Decision Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border-4 border-black shadow-[10px_10px_0px_0px_#121212] max-w-lg w-full p-6 md:p-8 space-y-5 animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b-2 border-black">
              <h3 className="font-black text-xl uppercase tracking-tight">
                Record Architectural Exemption
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="w-8 h-8 font-black border-2 border-black bg-[#D02020] text-white hover:bg-black"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddDecision} className="space-y-4">
              <div>
                <label className="block text-xs font-black uppercase tracking-wider mb-1">
                  Policy Description / Exemption Rule
                </label>
                <textarea
                  required
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="e.g. Staging cluster allows unauthenticated /metrics endpoint"
                  className="w-full p-2.5 border-2 border-black text-sm font-medium focus:outline-none"
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-black uppercase tracking-wider mb-1">
                    Approver (SecOps / Lead)
                  </label>
                  <input
                    required
                    type="text"
                    value={newApprover}
                    onChange={(e) => setNewApprover(e.target.value)}
                    placeholder="e.g. marcus (SecOps Lead)"
                    className="w-full p-2 border-2 border-black text-sm font-medium focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-black uppercase tracking-wider mb-1">
                    PR Reference
                  </label>
                  <input
                    type="text"
                    value={newPrRef}
                    onChange={(e) => setNewPrRef(e.target.value)}
                    placeholder="e.g. PR #48"
                    className="w-full p-2 border-2 border-black text-sm font-medium focus:outline-none"
                  />
                </div>
              </div>

              <div className="pt-3 border-t-2 border-black flex justify-end gap-3">
                <BauhausButton
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAddModal(false)}
                >
                  Cancel
                </BauhausButton>
                <BauhausButton type="submit" variant="primary" size="sm">
                  Save to Firestore
                </BauhausButton>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
