"""Interactive Web Dashboard for GitSentry.

Provides a rich visual UI for judges, developers, and operators to:
  - Visually inspect the Firestore Memory Bank (Decisions, Dev Habits, Audit Logs, Briefs).
  - Run the 3-beat demo simulation interactively with live animations and visual status badges.
  - Test synthetic webhook events and view real-time HMAC verification.
  - Monitor commit status checks and autonomous remediation PRs.
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitSentry — Stateful Security Co-Pilot Dashboard</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        brand: {
                            50: '#eef2ff',
                            500: '#6366f1',
                            600: '#4f46e5',
                            700: '#4338ca',
                        },
                        dark: {
                            900: '#0f172a',
                            800: '#1e293b',
                            700: '#334155',
                        }
                    }
                }
            }
        }
    </script>
    <style>
        .glow { box-shadow: 0 0 25px rgba(99, 102, 241, 0.25); }
        .code-font { font-family: 'JetBrains Mono', 'Fira Code', monospace; }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col font-sans">

    <!-- Top Navigation -->
    <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-emerald-500 flex items-center justify-center shadow-lg shadow-indigo-500/30">
                    <i data-lucide="shield-alert" class="w-6 h-6 text-white"></i>
                </div>
                <div>
                    <div class="flex items-center space-x-2">
                        <h1 class="text-xl font-bold tracking-tight text-white">GitSentry</h1>
                        <span class="px-2 py-0.5 text-xs font-semibold rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">Gemini 3.7 Flash</span>
                    </div>
                    <p class="text-xs text-slate-400">Stateful AI Security Co-Pilot for GitHub</p>
                </div>
            </div>
            <div class="flex items-center space-x-3 text-sm">
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 mr-2 animate-pulse"></span>
                    System Ready
                </span>
                <a href="/docs" target="_blank" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition flex items-center space-x-1.5 border border-slate-700">
                    <i data-lucide="file-code" class="w-4 h-4"></i>
                    <span>Swagger API Docs</span>
                </a>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

        <!-- Top Metrics & Architecture Banner -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div class="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
                    <span>MODEL ENGINE</span>
                    <i data-lucide="cpu" class="w-4 h-4 text-indigo-400"></i>
                </div>
                <div class="text-xl font-bold text-white">Gemini 3.7 Flash</div>
                <div class="text-xs text-slate-400 mt-1">Dual-tier thinking (LOW/HIGH)</div>
            </div>

            <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div class="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
                    <span>MEMORY BANK</span>
                    <i data-lucide="database" class="w-4 h-4 text-emerald-400"></i>
                </div>
                <div class="text-xl font-bold text-emerald-400" id="stat-decisions">0 Active Decisions</div>
                <div class="text-xs text-slate-400 mt-1" id="stat-habits">0 Tracked Habits</div>
            </div>

            <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div class="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
                    <span>STATUS GATE</span>
                    <i data-lucide="git-pull-request" class="w-4 h-4 text-amber-400"></i>
                </div>
                <div class="text-xl font-bold text-amber-400" id="stat-status">gitsentry/security</div>
                <div class="text-xs text-slate-400 mt-1">Merge blocking enabled</div>
            </div>

            <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div class="flex items-center justify-between text-slate-400 text-xs font-medium mb-2">
                    <span>GCP DEPLOYMENT</span>
                    <i data-lucide="cloud" class="w-4 h-4 text-sky-400"></i>
                </div>
                <div class="text-xl font-bold text-sky-400">Cloud Run + Pub/Sub</div>
                <div class="text-xs text-slate-400 mt-1">Secret Manager & Firestore</div>
            </div>
        </div>

        <!-- 3-Beat Demo Simulation Interactive Controller -->
        <div class="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-900/50 rounded-2xl p-6 glow">
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center space-x-3">
                    <div class="p-2 rounded-lg bg-indigo-500/20 text-indigo-400">
                        <i data-lucide="play-circle" class="w-6 h-6"></i>
                    </div>
                    <div>
                        <h2 class="text-lg font-bold text-white">Live 3-Beat Demo Scenario Simulator</h2>
                        <p class="text-xs text-slate-400">Execute the 3 proof points from PRD Section 5 with 1-click simulations</p>
                    </div>
                </div>
                <button onclick="resetMemory()" class="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition flex items-center space-x-1">
                    <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i>
                    <span>Reset Memory</span>
                </button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <!-- Beat 1 Button -->
                <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-4 hover:border-indigo-500/50 transition flex flex-col justify-between">
                    <div>
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-xs font-bold text-indigo-400 uppercase tracking-wider">Beat 1</span>
                            <span class="px-2 py-0.5 text-[10px] bg-slate-800 rounded text-slate-400 font-mono">PR #1</span>
                        </div>
                        <h3 class="text-sm font-semibold text-white mb-1">Socratic Dialogue & Exemption</h3>
                        <p class="text-xs text-slate-400">Staging unauth /health -> Socratic pushback -> Accepted exemption stored in Firestore.</p>
                    </div>
                    <button onclick="runDemoBeat(1)" id="btn-beat-1" class="mt-4 w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition flex items-center justify-center space-x-2">
                        <i data-lucide="play" class="w-3.5 h-3.5"></i>
                        <span>Run PR #1 Scenario</span>
                    </button>
                </div>

                <!-- Beat 2 Button -->
                <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-4 hover:border-emerald-500/50 transition flex flex-col justify-between">
                    <div>
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-xs font-bold text-emerald-400 uppercase tracking-wider">Beat 2</span>
                            <span class="px-2 py-0.5 text-[10px] bg-slate-800 rounded text-slate-400 font-mono">PR #2</span>
                        </div>
                        <h3 class="text-sm font-semibold text-white mb-1">Cross-PR Memory & Auto-Fix</h3>
                        <p class="text-xs text-slate-400">Production exposure -> Cites PR #1 exemption -> Autonomously opens fix PR adding JWT auth.</p>
                    </div>
                    <button onclick="runDemoBeat(2)" id="btn-beat-2" class="mt-4 w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition flex items-center justify-center space-x-2">
                        <i data-lucide="play" class="w-3.5 h-3.5"></i>
                        <span>Run PR #2 Scenario</span>
                    </button>
                </div>

                <!-- Beat 3 Button -->
                <div class="bg-slate-900/90 border border-slate-800 rounded-xl p-4 hover:border-amber-500/50 transition flex flex-col justify-between">
                    <div>
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-xs font-bold text-amber-400 uppercase tracking-wider">Beat 3</span>
                            <span class="px-2 py-0.5 text-[10px] bg-slate-800 rounded text-slate-400 font-mono">PR #3</span>
                        </div>
                        <h3 class="text-sm font-semibold text-white mb-1">Developer Habit Adaptation</h3>
                        <p class="text-xs text-slate-400">Raw SQL concatenation -> Inspects dev_habits -> Cites 2nd recurrence and offers patch.</p>
                    </div>
                    <button onclick="runDemoBeat(3)" id="btn-beat-3" class="mt-4 w-full py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold transition flex items-center justify-center space-x-2">
                        <i data-lucide="play" class="w-3.5 h-3.5"></i>
                        <span>Run PR #3 Scenario</span>
                    </button>
                </div>
            </div>

            <!-- Live Output Terminal in Dashboard -->
            <div class="bg-black/90 rounded-xl border border-slate-800 p-4 code-font text-xs">
                <div class="flex items-center justify-between border-b border-slate-800 pb-2 mb-3 text-slate-400">
                    <div class="flex items-center space-x-2">
                        <span class="w-3 h-3 rounded-full bg-red-500 inline-block"></span>
                        <span class="w-3 h-3 rounded-full bg-yellow-500 inline-block"></span>
                        <span class="w-3 h-3 rounded-full bg-green-500 inline-block"></span>
                        <span class="ml-2 font-mono text-[11px]">gitsentry-live-execution-log</span>
                    </div>
                    <span id="log-status" class="text-[11px] text-indigo-400">Idle - Click any scenario above</span>
                </div>
                <pre id="terminal-output" class="text-slate-300 max-h-56 overflow-y-auto whitespace-pre-wrap leading-relaxed">Ready. Select a PR beat above to watch GitSentry execute live.</pre>
            </div>
        </div>

        <!-- Firestore Memory Bank Explorer -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div class="flex items-center justify-between mb-6">
                <div class="flex items-center space-x-3">
                    <div class="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
                        <i data-lucide="database" class="w-6 h-6"></i>
                    </div>
                    <div>
                        <h2 class="text-lg font-bold text-white">Firestore Memory Bank Inspector</h2>
                        <p class="text-xs text-slate-400">Live inspection of institutional memory across pull requests</p>
                    </div>
                </div>
                <!-- Tabs -->
                <div class="flex space-x-2 border border-slate-800 bg-slate-950 p-1 rounded-xl text-xs font-medium">
                    <button onclick="switchTab('decisions')" id="tab-decisions" class="px-3 py-1.5 rounded-lg bg-indigo-600 text-white">Decisions & Exemptions</button>
                    <button onclick="switchTab('habits')" id="tab-habits" class="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white">Developer Habits</button>
                    <button onclick="switchTab('audit')" id="tab-audit" class="px-3 py-1.5 rounded-lg text-slate-400 hover:text-white">Audit Log</button>
                </div>
            </div>

            <!-- Decisions List -->
            <div id="content-decisions" class="space-y-3">
                <div id="decisions-empty" class="text-center py-8 text-slate-500 text-sm">
                    No active decisions recorded yet. Run Beat 1 to record an exemption!
                </div>
                <div id="decisions-list" class="space-y-2"></div>
            </div>

            <!-- Habits List -->
            <div id="content-habits" class="space-y-3 hidden">
                <div id="habits-empty" class="text-center py-8 text-slate-500 text-sm">
                    No developer habits tracked yet. Run Beat 3 to simulate habit learning!
                </div>
                <div id="habits-list" class="space-y-2"></div>
            </div>

            <!-- Audit Log List -->
            <div id="content-audit" class="space-y-3 hidden">
                <div id="audit-empty" class="text-center py-8 text-slate-500 text-sm">
                    No audit actions recorded yet.
                </div>
                <div id="audit-list" class="space-y-2"></div>
            </div>
        </div>

    </main>

    <!-- Footer -->
    <footer class="border-t border-slate-800 bg-slate-900/50 py-6 text-center text-xs text-slate-500">
        <div class="max-w-7xl mx-auto px-4">
            GitSentry • Built with Gemini 3.7 Flash, Google GenAI SDK, Google Cloud Run, Firestore, Pub/Sub & Secret Manager
        </div>
    </footer>

    <script>
        lucide.createIcons();

        let currentTab = 'decisions';

        function switchTab(tab) {
            currentTab = tab;
            ['decisions', 'habits', 'audit'].forEach(t => {
                const el = document.getElementById('content-' + t);
                const tabBtn = document.getElementById('tab-' + t);
                if (t === tab) {
                    el.classList.remove('hidden');
                    tabBtn.className = 'px-3 py-1.5 rounded-lg bg-indigo-600 text-white';
                } else {
                    el.classList.add('hidden');
                    tabBtn.className = 'px-3 py-1.5 rounded-lg text-slate-400 hover:text-white';
                }
            });
        }

        async function fetchMemoryStatus() {
            try {
                const res = await fetch('/api/dashboard/memory');
                if (res.ok) {
                    const data = await res.json();
                    renderMemory(data);
                }
            } catch (err) {
                console.error("Failed to fetch memory:", err);
            }
        }

        function renderMemory(data) {
            // Stats
            document.getElementById('stat-decisions').innerText = `${data.decisions.length} Active Decisions`;
            document.getElementById('stat-habits').innerText = `${data.habits.length} Tracked Habits`;

            // Decisions
            const decList = document.getElementById('decisions-list');
            const decEmpty = document.getElementById('decisions-empty');
            if (data.decisions.length === 0) {
                decEmpty.classList.remove('hidden');
                decList.innerHTML = '';
            } else {
                decEmpty.classList.add('hidden');
                decList.innerHTML = data.decisions.map(d => `
                    <div class="bg-slate-950 border border-slate-800 p-3.5 rounded-xl flex items-start justify-between">
                        <div>
                            <div class="flex items-center space-x-2">
                                <span class="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-500/20 text-emerald-300 uppercase">${d.status}</span>
                                <span class="text-xs font-mono text-indigo-400">${d.pr_reference}</span>
                                <span class="text-xs text-slate-400">by @${d.approved_by}</span>
                            </div>
                            <p class="text-xs text-slate-200 mt-1.5">${d.description}</p>
                        </div>
                        <span class="text-[10px] text-slate-500">${new Date(d.created_at).toLocaleTimeString()}</span>
                    </div>
                `).join('');
            }

            // Habits
            const habList = document.getElementById('habits-list');
            const habEmpty = document.getElementById('habits-empty');
            if (data.habits.length === 0) {
                habEmpty.classList.remove('hidden');
                habList.innerHTML = '';
            } else {
                habEmpty.classList.add('hidden');
                habList.innerHTML = data.habits.map(h => `
                    <div class="bg-slate-950 border border-slate-800 p-3.5 rounded-xl flex items-start justify-between">
                        <div>
                            <div class="flex items-center space-x-2">
                                <span class="px-2 py-0.5 text-[10px] font-bold rounded bg-amber-500/20 text-amber-300">Seen ${h.occurrences.length}x</span>
                                <span class="text-xs text-slate-400">PRs: ${h.occurrences.join(', ')}</span>
                            </div>
                            <p class="text-xs text-slate-200 mt-1.5">${h.pattern}</p>
                        </div>
                    </div>
                `).join('');
            }

            // Audit Log
            const audList = document.getElementById('audit-list');
            const audEmpty = document.getElementById('audit-empty');
            if (data.audit_logs.length === 0) {
                audEmpty.classList.remove('hidden');
                audList.innerHTML = '';
            } else {
                audEmpty.classList.add('hidden');
                audList.innerHTML = data.audit_logs.map(a => `
                    <div class="bg-slate-950 border border-slate-800 p-3.5 rounded-xl flex items-start justify-between text-xs">
                        <div>
                            <div class="flex items-center space-x-2">
                                <span class="font-mono text-indigo-400 font-semibold">${a.pr_reference}</span>
                                <span class="text-slate-200">${a.action_taken}</span>
                            </div>
                            <p class="text-slate-400 text-[11px] mt-1">${a.reasoning_summary}</p>
                        </div>
                        <span class="text-[10px] text-slate-500">${new Date(a.timestamp).toLocaleTimeString()}</span>
                    </div>
                `).join('');
            }
        }

        async function runDemoBeat(beatNumber) {
            const statusEl = document.getElementById('log-status');
            const term = document.getElementById('terminal-output');
            statusEl.innerText = `Executing Beat ${beatNumber}...`;

            try {
                const res = await fetch(`/api/dashboard/run-beat?beat=${beatNumber}`, { method: 'POST' });
                const result = await res.json();
                if (result && result.log) {
                    term.innerText = result.log;
                    statusEl.innerText = `Beat ${beatNumber} completed successfully!`;
                } else if (result && result.detail) {
                    term.innerText = 'API Error: ' + JSON.stringify(result.detail, null, 2);
                    statusEl.innerText = 'Execution error';
                } else {
                    term.innerText = JSON.stringify(result, null, 2);
                    statusEl.innerText = `Beat ${beatNumber} finished`;
                }
                await fetchMemoryStatus();
            } catch (err) {
                term.innerText = `Error executing Beat ${beatNumber}: ` + err;
                statusEl.innerText = 'Execution error';
            }
        }

        async function resetMemory() {
            await fetch('/api/dashboard/reset', { method: 'POST' });
            document.getElementById('terminal-output').innerText = 'Memory reset. Ready for clean simulation run.';
            document.getElementById('log-status').innerText = 'Memory cleared';
            await fetchMemoryStatus();
        }

        // Initialize on load
        fetchMemoryStatus();
        setInterval(fetchMemoryStatus, 5000);
    </script>
</body>
</html>
"""
