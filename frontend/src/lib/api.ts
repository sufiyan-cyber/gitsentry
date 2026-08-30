export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8080";

export interface BackendMemoryResponse {
  repo_id: string;
  decisions: Array<{
    id: string;
    description: string;
    approved_by: string;
    pr_reference: string;
    created_at: string;
    status: "active" | "superseded";
  }>;
  habits: Array<{
    author_id: string;
    pattern: string;
    occurrences: string[];
    first_seen: string;
    last_seen: string;
  }>;
  audit_logs: Array<{
    id?: string;
    pr_reference: string;
    action_taken: string;
    reasoning_summary: string;
    timestamp: string;
  }>;
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/healthz`, {
      method: "GET",
      cache: "no-store",
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function fetchLiveMemory(): Promise<BackendMemoryResponse | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/dashboard/memory`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function runLiveBeat(beat: number): Promise<{ status: string; log: string } | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/dashboard/run-beat?beat=${beat}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function resetBackendState(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/dashboard/reset`, {
      method: "POST",
    });
    return res.ok;
  } catch {
    return false;
  }
}
