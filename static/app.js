let buildingSchemas = {};
let currentBuildingCode = "B_DONG";
let currentViewMode = "form"; // 'form' or 'dashboard'
let trendChartInstance = null;
let authToken = localStorage.getItem("ro_inspection_token") || "";

const COLOR_PALETTE = {
    "A": "#0284c7",
    "B": "#16a34a",
    "C": "#ea580c",
    "D": "#9333ea",
    "1": "#0284c7",
    "2": "#16a34a",
    "3": "#ea580c",
    "4": "#9333ea",
    "전단": "#0284c7",
    "후단": "#ea580c",
    "default": "#2563eb"
};

document.addEventListener("DOMContentLoaded", () => {
    checkAuthAndInit();
});

// Authentication Handlers (100% Guaranteed Instant Login)
function checkAuthAndInit() {
    if (!authToken) {
        showLoggedOutState();
        loadBuildingTabsOnly();
        return;
    }
    
    showLoggedInState();
    initApp();
}

function showLoggedOutState() {
    const loginArea = document.getElementById("header-login-area");
    const userArea = document.getElementById("header-user-area");
    const lockBanner = document.getElementById("auth-lock-banner");
    const contentArea = document.getElementById("auth-content-area");
    
    if (loginArea) loginArea.style.setProperty("display", "flex", "important");
    if (userArea) userArea.style.setProperty("display", "none", "important");
    if (lockBanner) lockBanner.style.setProperty("display", "block", "important");
    if (contentArea) contentArea.style.setProperty("display", "none", "important");
    
    // Clear input fields on logout
    const idInput = document.getElementById("inline-login-id");
    const pwInput = document.getElementById("inline-login-pw");
    if (idInput) idInput.value = "";
    if (pwInput) pwInput.value = "";
}

function showLoggedInState() {
    const loginArea = document.getElementById("header-login-area");
    const userArea = document.getElementById("header-user-area");
    const lockBanner = document.getElementById("auth-lock-banner");
    const contentArea = document.getElementById("auth-content-area");
    
    if (loginArea) loginArea.style.setProperty("display", "none", "important");
    if (userArea) userArea.style.setProperty("display", "flex", "important");
    if (lockBanner) lockBanner.style.setProperty("display", "none", "important");
    if (contentArea) contentArea.style.setProperty("display", "block", "important");
}

function handleInlineLoginSubmit(e) {
    if (e) e.preventDefault();
    const idInput = document.getElementById("inline-login-id").value.trim();
    const pwInput = document.getElementById("inline-login-pw").value.trim();
    const errDiv = document.getElementById("inline-login-error");
    if (errDiv) errDiv.textContent = "";

    if (idInput === "1234" && pwInput === "5678") {
        authToken = "auth-session-token-1234-5678";
        localStorage.setItem("ro_inspection_token", authToken);
        showLoggedInState();
        initApp();
        showToast("로그인 성공!");
        return false;
    } else {
        if (errDiv) errDiv.textContent = "아이디 또는 비밀번호가 올바르지 않습니다.";
        return false;
    }
}

function handleLogout() {
    localStorage.removeItem("ro_inspection_token");
    authToken = "";
    showLoggedOutState();
    showToast("로그아웃 되었습니다.");
}

async function loadBuildingTabsOnly() {
    try {
        const res = await fetch("/api/buildings");
        buildingSchemas = await res.json();
        renderBuildingTabs();
    } catch (e) {
        console.error("Failed to load building tabs", e);
    }
}

// Helper to auto-advance focus to the next input field
function advanceToNextInput(currentElement) {
    const inputs = Array.from(document.querySelectorAll("#form-fields-container input:not([disabled]), #form-fields-container select:not([disabled])"));
    const idx = inputs.indexOf(currentElement);
    if (idx !== -1 && idx < inputs.length - 1) {
        const nextInput = inputs[idx + 1];
        nextInput.focus();
        if (nextInput.select && typeof nextInput.select === "function") {
            nextInput.select();
        }
        nextInput.scrollIntoView({ behavior: "smooth", block: "center" });
    }
}

// App Initialization
async function initApp() {
    document.getElementById("input-date").value = new Date().toISOString().split("T")[0];
    
    // Global Enter / Mobile Check mark (✓) / Done key handler for fast navigation
    const container = document.getElementById("form-fields-container");
    if (container) {
        const handleKeyAdvance = function(e) {
            const isAdvanceKey = e.key === "Enter" || e.key === "Done" || e.key === "Next" || 
                                 e.keyCode === 13 || e.keyCode === 10 || 
                                 e.code === "Enter" || e.code === "NumpadEnter";
            if (isAdvanceKey) {
                e.preventDefault();
                advanceToNextInput(e.target);
            }
        };
        container.addEventListener("keydown", handleKeyAdvance);
    }
    
    // Offline & Network Event Listeners & Active Heartbeat Check
    window.addEventListener("online", async () => {
        await updateNetworkStatus();
        if (isRealOnline) syncOfflineQueue();
    });
    window.addEventListener("offline", () => {
        updateNetworkStatus();
    });
    
    // Check real network connectivity status every 3 seconds
    setInterval(updateNetworkStatus, 3000);
    updateNetworkStatus();
    
    try {
        const res = await fetch("/api/buildings");
        buildingSchemas = await res.json();
        renderBuildingTabs();
        loadBuildingForm(currentBuildingCode);
        
        // Auto-sync if real online and pending items exist
        if (isRealOnline && getOfflineQueue().length > 0) {
            syncOfflineQueue();
        }
    } catch (e) {
        console.error("Failed to load schemas", e);
    }
}

function renderBuildingTabs() {
    const tabsContainer = document.getElementById("building-tabs");
    tabsContainer.innerHTML = "";
    
    Object.keys(buildingSchemas).forEach(code => {
        const schema = buildingSchemas[code];
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = `tab-btn ${code === currentBuildingCode ? 'active' : ''}`;
        
        const hasDraft = !!localStorage.getItem(`RO_EDI_DRAFT_${code}`);
        btn.innerHTML = `${schema.name} ${hasDraft ? '<span class="draft-badge">작성중</span>' : ''}`;
        
        btn.onclick = () => switchBuildingTab(code);
        tabsContainer.appendChild(btn);
    });
}

function switchBuildingTab(code) {
    if (currentBuildingCode && currentViewMode === "form") {
        saveCurrentBuildingDraft();
    }
    currentBuildingCode = code;
    renderBuildingTabs();
    if (!authToken) {
        showToast("로그인 후 작성 및 조회가 가능합니다.");
        return;
    }
    if (currentViewMode === "form") {
        loadBuildingForm(code);
    } else {
        onGlobalFilterChange();
    }
}

function switchViewMode(mode) {
    if (!authToken) {
        showToast("로그인 후 이용 가능합니다.");
        return;
    }
    if (mode === "dashboard" && currentViewMode === "form") {
        saveCurrentBuildingDraft();
    }
    currentViewMode = mode;
    document.getElementById("btn-mode-form").classList.toggle("active", mode === "form");
    document.getElementById("btn-mode-dashboard").classList.toggle("active", mode === "dashboard");
    document.getElementById("view-form").classList.toggle("active", mode === "form");
    document.getElementById("view-dashboard").classList.toggle("active", mode === "dashboard");
    
    if (mode === "dashboard") {
        onGlobalFilterChange();
    }
}

// Render Form with Ultra-Clean Layout & Draft Restoration
function loadBuildingForm(buildingCode) {
    const schema = buildingSchemas[buildingCode];
    if (!schema) return;
    
    const container = document.getElementById("form-fields-container");
    container.innerHTML = "";
    
    schema.sections.forEach(sec => {
        const wrapper = document.createElement("div");
        wrapper.className = "excel-paper-wrapper";
        
        let secHTML = `
            <div class="excel-section-banner">
                <span>📌 ${sec.title}</span>
                <span class="range-badge">총 ${sec.fields.length}개 항목</span>
            </div>
            <div class="grid-card-body">
        `;
        
        const groupedFields = groupFieldsForMultiColumn(sec.fields);
        
        groupedFields.forEach(g => {
            if (g.fields.length === 1 && !g.fields[0].sub) {
                // Single Standalone Field (or Select dropdown)
                const f = g.fields[0];
                secHTML += `
                    <div class="grid-row-item grid-single-row" id="row-${f.key}">
                        <div class="grid-row-header">
                            <span>${f.label}</span>
                            <span class="range-badge">${f.range ? '범위: ' + f.range : ''}</span>
                        </div>
                        ${renderSingleFieldInput(f)}
                    </div>
                `;
            } else {
                // Grouped Multi-Line Field (A/B, A/B/C, A/B/C/D, 전단/후단)
                const colClass = `grid-${Math.min(g.fields.length, 4)}col`;
                secHTML += `
                    <div class="grid-row-item">
                        <div class="grid-row-header">
                            <span>${g.baseLabel}</span>
                            <span class="range-badge">기준: ${g.fields[0].range}</span>
                        </div>
                        <div class="grid-cols-container ${colClass}">
                            ${g.fields.map(f => renderFieldInputCell(f)).join('')}
                        </div>
                    </div>
                `;
            }
        });
        
        secHTML += `
            </div>
        `;
        
        wrapper.innerHTML = secHTML;
        container.appendChild(wrapper);
    });
    
    evaluateStandbyGroups();
}

function groupFieldsForMultiColumn(fields) {
    const groups = [];
    const map = new Map();
    
    fields.forEach(f => {
        if (f.group) {
            let baseLabel = f.label
                .replace(/\s+[A-D]$/, '')
                .replace(/\s+A\/B\/C\/D/, '')
                .replace(/\s+[A-D]-[1-4]/, '')
                .replace(/\s+\(전단\)/, '')
                .replace(/\s+\(후단\)/, '');
                
            if (!map.has(f.group)) {
                const groupObj = { groupKey: f.group, baseLabel: baseLabel, fields: [] };
                map.set(f.group, groupObj);
                groups.push(groupObj);
            }
            map.get(f.group).fields.push(f);
        } else {
            groups.push({ groupKey: f.key, baseLabel: f.label, fields: [f] });
        }
    });
    
    return groups;
}

function renderSingleFieldInput(f) {
    if (f.type === "select") {
        return `
            <select id="input-${f.key}" name="${f.key}" onchange="handleInputChange(this)">
                ${f.options.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
            </select>
        `;
    }
    
    return `
        <div class="cell-input-container">
            <input type="number" step="any" inputmode="decimal" enterkeyhint="next" id="input-${f.key}" name="${f.key}" 
                   placeholder="" oninput="handleInputChange(this)">
            ${f.unit ? `<span class="unit-suffix-inline">${f.unit}</span>` : ''}
        </div>
    `;
}

function renderFieldInputCell(f) {
    const groupAttr = f.group ? `data-group="${f.group}"` : '';
    const subAttr = f.sub ? `data-sub="${f.sub}"` : '';
    const subLabel = f.sub ? (isNaN(f.sub) && f.sub !== "전단" && f.sub !== "후단" && !f.sub.startsWith("EDI") && !f.sub.startsWith("PS") ? `라인 ${f.sub}` : `${f.sub}`) : f.label;
    
    if (f.type === "select") {
        return `
            <div class="grid-col-cell" id="cell-${f.key}" ${groupAttr} ${subAttr}>
                <div class="cell-header">
                    <span class="cell-title">${subLabel}</span>
                </div>
                <select id="input-${f.key}" name="${f.key}" onchange="handleInputChange(this)">
                    ${f.options.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
                </select>
            </div>
        `;
    }
    
    // Check if this is exempt from standby toggle (resin_trap & EDI modules are exempt, but EDI FEED PUMPS toggle standby!)
    const isExempt = f.group && (f.group.includes("resin_trap") || ((f.group.includes("edi") || f.group.includes("EDI")) && !f.group.includes("fpump")));
    
    return `
        <div class="grid-col-cell" id="cell-${f.key}" ${groupAttr} ${subAttr}>
            <div class="cell-header">
                <span class="cell-title">${subLabel}</span>
                ${!isExempt ? `<span id="badge-${f.key}" class="status-badge status-active" onclick="toggleBadgeStatus('${f.key}')" title="클릭하여 가동/비가동 수동 전환">가동</span>` : ''}
            </div>
            <div class="cell-input-container">
                <input type="number" step="any" inputmode="decimal" enterkeyhint="next" id="input-${f.key}" name="${f.key}" 
                       placeholder="" oninput="handleInputChange(this)">
                ${f.unit ? `<span class="unit-suffix-inline">${f.unit}</span>` : ''}
            </div>
        </div>
    `;
}

function handleInputChange(input) {
    if (!input.classList.contains('is-modified-value')) {
        input.classList.remove('is-previous-value');
        input.classList.add('is-modified-value');
    }
    evaluateStandbyGroups();
    saveCurrentBuildingDraft();
}

function toggleBadgeStatus(key) {
    const cell = document.getElementById(`cell-${key}`);
    const badge = document.getElementById(`badge-${key}`);
    const input = document.getElementById(`input-${key}`);
    if (!cell || !badge || !input) return;
    
    const isCurrentlyActive = badge.classList.contains("status-active");
    if (isCurrentlyActive) {
        badge.className = "status-badge status-locked";
        badge.textContent = "비가동";
        cell.classList.add("is-standby-locked");
        input.value = "";
        input.disabled = true;
        input.placeholder = "비가동";
        badge.setAttribute("data-manual-lock", "true");
    } else {
        badge.className = "status-badge status-active";
        badge.textContent = "가동";
        cell.classList.remove("is-standby-locked");
        input.disabled = false;
        input.placeholder = "";
        badge.removeAttribute("data-manual-lock");
    }
    evaluateStandbyGroups();
    saveCurrentBuildingDraft();
}

// ----------------------------------------------------
// Offline Draft & Sync Queue Helper Functions
// ----------------------------------------------------
function saveCurrentBuildingDraft() {
    if (!currentBuildingCode || !buildingSchemas[currentBuildingCode]) return;
    const schema = buildingSchemas[currentBuildingCode];
    
    const valuesDict = {};
    let hasAnyValue = false;
    
    schema.sections.forEach(sec => {
        sec.fields.forEach(f => {
            const input = document.getElementById(`input-${f.key}`);
            if (input) {
                const val = input.disabled ? "비가동" : input.value;
                valuesDict[f.key] = val;
                if (val !== "" && val !== "비가동") {
                    hasAnyValue = true;
                }
            }
        });
    });
    
    const dateVal = document.getElementById("input-date")?.value || "";
    const inspectorVal = document.getElementById("input-inspector")?.value || "";
    const notesVal = document.getElementById("input-notes")?.value || "";
    
    if (hasAnyValue || notesVal !== "") {
        const draftObj = {
            building_code: currentBuildingCode,
            inspection_date: dateVal,
            inspector: inspectorVal,
            notes: notesVal,
            values: valuesDict,
            updated_at: new Date().toISOString()
        };
        localStorage.setItem(`RO_EDI_DRAFT_${currentBuildingCode}`, JSON.stringify(draftObj));
    } else {
        localStorage.removeItem(`RO_EDI_DRAFT_${currentBuildingCode}`);
    }
    renderBuildingTabs();
}

function loadBuildingDraft(buildingCode) {
    const raw = localStorage.getItem(`RO_EDI_DRAFT_${buildingCode}`);
    if (!raw) return;
    try {
        const draft = JSON.parse(raw);
        if (draft.inspection_date && document.getElementById("input-date")) {
            document.getElementById("input-date").value = draft.inspection_date;
        }
        if (draft.inspector && document.getElementById("input-inspector")) {
            document.getElementById("input-inspector").value = draft.inspector;
        }
        if (draft.notes && document.getElementById("input-notes")) {
            document.getElementById("input-notes").value = draft.notes;
        }
        if (draft.values) {
            Object.keys(draft.values).forEach(k => {
                const input = document.getElementById(`input-${k}`);
                if (input) {
                    const val = draft.values[k];
                    if (val === "비가동") {
                        input.disabled = true;
                        input.placeholder = "비가동";
                        const key = k;
                        const badge = document.getElementById(`badge-${key}`);
                        if (badge) {
                            badge.className = "status-badge status-locked";
                            badge.textContent = "비가동";
                            badge.setAttribute("data-manual-lock", "true");
                        }
                    } else if (val !== "") {
                        input.value = val;
                        input.classList.add('is-modified-value');
                    }
                }
            });
            evaluateStandbyGroups();
        }
    } catch(e) {
        console.error("Failed to load draft", e);
    }
}

function clearBuildingDraft(buildingCode) {
    localStorage.removeItem(`RO_EDI_DRAFT_${buildingCode}`);
    renderBuildingTabs();
}

let isRealOnline = true;

async function checkRealOnlineStatus() {
    if (!navigator.onLine) return false;
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);
        
        const res = await fetch("/api/buildings", {
            method: "GET",
            cache: "no-store",
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        
        return res.ok || res.status === 200 || res.status === 304;
    } catch(e) {
        return false;
    }
}

function getOfflineQueue() {
    try {
        return JSON.parse(localStorage.getItem("RO_EDI_OFFLINE_QUEUE") || "[]");
    } catch(e) {
        return [];
    }
}

function saveOfflineQueue(queue) {
    localStorage.setItem("RO_EDI_OFFLINE_QUEUE", JSON.stringify(queue));
    updateNetworkStatus();
}

async function updateNetworkStatus() {
    isRealOnline = await checkRealOnlineStatus();
    const queue = getOfflineQueue();
    
    const statusBar = document.getElementById("network-status-bar");
    const iconSpan = document.getElementById("network-icon");
    const textSpan = document.getElementById("network-text");
    const syncBtn = document.getElementById("btn-sync-offline-queue");
    const countSpan = document.getElementById("offline-queue-count");
    
    if (countSpan) countSpan.textContent = queue.length;
    
    if (queue.length > 0) {
        if (syncBtn) syncBtn.style.display = "inline-flex";
    } else {
        if (syncBtn) syncBtn.style.display = "none";
    }
    
    if (!isRealOnline) {
        if (statusBar) statusBar.className = "network-status-bar offline";
        if (iconSpan) iconSpan.textContent = "📵";
        if (textSpan) textSpan.textContent = `음영지역 / 오프라인 상태 (작성 일지 대기 큐 ${queue.length}개 보관 중)`;
    } else {
        if (statusBar) statusBar.className = "network-status-bar online";
        if (iconSpan) iconSpan.textContent = "📶";
        if (queue.length > 0) {
            if (textSpan) textSpan.textContent = `인터넷 연결됨! (대기 중인 오프라인 일지 ${queue.length}개 발견)`;
        } else {
            if (textSpan) textSpan.textContent = "온라인 상태 (서버 실시간 저장 가능)";
        }
    }
}

function queueOfflineInspection(payload) {
    const queue = getOfflineQueue();
    queue.push({
        id: Date.now(),
        payload: payload,
        queued_at: new Date().toISOString()
    });
    saveOfflineQueue(queue);
    
    clearBuildingDraft(payload.building_code);
    
    const bName = buildingSchemas[payload.building_code] ? buildingSchemas[payload.building_code].name : payload.building_code;
    showToast(`📵 [${bName}] 오프라인 임시 저장 완료! (대기 큐: ${queue.length}개)\n데이터가 터지는 곳 이동 시 자동 동기화됩니다.`);
}

async function syncOfflineQueue() {
    const queue = getOfflineQueue();
    if (queue.length === 0) {
        showToast("대기 중인 오프라인 일지가 없습니다.");
        return;
    }
    
    const onlineNow = await checkRealOnlineStatus();
    if (!onlineNow) {
        showToast("📵 아직 인터넷 신호가 없습니다. 데이터가 터지는 곳으로 이동해 주세요.");
        return;
    }
    
    showToast(`🔄 대기 중인 점검일지 ${queue.length}개 서버 동기화 진행 중...`);
    
    let successCount = 0;
    const remainingQueue = [];
    
    for (const item of queue) {
        try {
            const res = await fetch("/api/inspections", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${authToken}`
                },
                body: JSON.stringify(item.payload)
            });
            
            if (res.ok) {
                successCount++;
            } else {
                remainingQueue.push(item);
            }
        } catch(e) {
            remainingQueue.push(item);
        }
    }
    
    saveOfflineQueue(remainingQueue);
    
    if (successCount > 0) {
        showToast(`🎉 오프라인에서 작성한 ${successCount}개 점검일지가 서버로 모두 전송되었습니다!`);
        if (currentViewMode === "dashboard") {
            onGlobalFilterChange();
        }
    } else {
        showToast("❌ 서버 통신 문제로 동기화에 실패했습니다. 다시 시도해 주세요.");
    }
}

// Active/Standby Auto-Locking Logic
function evaluateStandbyGroups() {
    const groups = {};
    const cells = document.querySelectorAll('.grid-col-cell[data-group]');
    
    cells.forEach(c => {
        const g = c.getAttribute('data-group');
        if (!g) return;
        // Skip resin_trap groups (both front and rear fillable without locking)
        if (g.includes("resin_trap")) return;
        // Skip EDI module groups (all EDI modules operate simultaneously, but FEED PUMP has standby!)
        if ((g.includes("edi") || g.includes("EDI")) && !g.includes("fpump")) return;
        if (!groups[g]) groups[g] = [];
        groups[g].push(c);
    });
    
    Object.keys(groups).forEach(g => {
        const groupCells = groups[g];
        const subMap = {};
        
        groupCells.forEach(c => {
            const sub = c.getAttribute('data-sub');
            const input = c.querySelector('input, select');
            
            let hasVal = false;
            if (input && input.value !== "" && input.value !== null) {
                const numVal = parseFloat(input.value);
                if (!isNaN(numVal) && numVal !== 0) {
                    hasVal = true;
                } else if (input.tagName === "SELECT" && input.value !== "전체정지") {
                    hasVal = true;
                }
            }
            
            if (!subMap[sub]) subMap[sub] = { cells: [], hasVal: false };
            subMap[sub].cells.push(c);
            if (hasVal) subMap[sub].hasVal = true;
        });
        
        const subs = Object.keys(subMap);
        const activeSubs = subs.filter(s => subMap[s].hasVal);
        const activeCount = activeSubs.length;
        const totalSubs = subs.length;
        const reqActive = totalSubs === 2 ? 1 : totalSubs - 1;
        
        if (activeCount >= reqActive && reqActive > 0) {
            subs.forEach(s => {
                const subObj = subMap[s];
                if (!subObj.hasVal) {
                    subObj.cells.forEach(c => {
                        const key = c.id.replace('cell-', '');
                        const badge = document.getElementById(`badge-${key}`);
                        const isManual = badge && badge.getAttribute("data-manual-lock") === "true";
                        
                        if (!isManual) {
                            c.classList.add('is-standby-locked');
                            const input = c.querySelector('input, select');
                            if (input) {
                                input.disabled = true;
                                input.placeholder = "비가동";
                            }
                            if (badge) {
                                badge.className = "status-badge status-locked";
                                badge.textContent = "비가동";
                            }
                        }
                    });
                } else {
                    subObj.cells.forEach(c => {
                        const key = c.id.replace('cell-', '');
                        const badge = document.getElementById(`badge-${key}`);
                        const isManual = badge && badge.getAttribute("data-manual-lock") === "true";
                        
                        if (!isManual) {
                            c.classList.remove('is-standby-locked');
                            const input = c.querySelector('input, select');
                            if (input) input.disabled = false;
                            if (badge) {
                                badge.className = "status-badge status-active";
                                badge.textContent = "가동";
                            }
                        }
                    });
                }
            });
        } else {
            subs.forEach(s => {
                subMap[s].cells.forEach(c => {
                    const key = c.id.replace('cell-', '');
                    const badge = document.getElementById(`badge-${key}`);
                    const isManual = badge && badge.getAttribute("data-manual-lock") === "true";
                    
                    if (!isManual) {
                        c.classList.remove('is-standby-locked');
                        const input = c.querySelector('input, select');
                        if (input) {
                            input.disabled = false;
                            input.placeholder = "";
                        }
                        if (badge) {
                            badge.className = "status-badge status-active";
                            badge.textContent = "가동";
                        }
                    }
                });
            });
        }
    });
}

// Copy Previous Log Values
async function copyPreviousLog() {
    try {
        const res = await fetch(`/api/inspections?building_code=${currentBuildingCode}`);
        const logs = await res.json();
        if (!logs || logs.length === 0) {
            showToast("이전 점검 기록이 없습니다.");
            return;
        }
        
        const prevLog = logs[0];
        const vals = prevLog.values;
        
        Object.keys(vals).forEach(k => {
            const input = document.getElementById(`input-${k}`);
            if (input && !input.disabled) {
                input.value = vals[k];
                input.classList.remove('is-modified-value');
                input.classList.add('is-previous-value');
            }
        });
        
        evaluateStandbyGroups();
        saveCurrentBuildingDraft();
        showToast(`이전 점검 값(${prevLog.inspection_date}) 불러오기 완료!`);
    } catch (e) {
        showToast("이전 기록을 가져오지 못했습니다.");
    }
}

// Form Submit Handler (Support Offline Queue)
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const dateVal = document.getElementById("input-date").value;
    const inspectorVal = document.getElementById("input-inspector").value.trim();
    const notesVal = document.getElementById("input-notes").value.trim();
    
    if (!dateVal || !inspectorVal) {
        alert("점검 일자와 점검자를 입력해 주세요.");
        return;
    }
    
    const schema = buildingSchemas[currentBuildingCode];
    const valuesDict = {};
    
    schema.sections.forEach(sec => {
        sec.fields.forEach(f => {
            const input = document.getElementById(`input-${f.key}`);
            if (input) {
                valuesDict[f.key] = input.disabled ? "비가동" : input.value;
            }
        });
    });
    
    const payload = {
        building_code: currentBuildingCode,
        line_code: "",
        inspection_date: dateVal,
        inspector: inspectorVal,
        values: valuesDict,
        notes: notesVal
    };
    
    // Check if offline
    if (!navigator.onLine) {
        queueOfflineInspection(payload);
        return;
    }
    
    try {
        const res = await fetch("/api/inspections", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            clearBuildingDraft(currentBuildingCode);
            showToast(`✅ [${schema.name}] 점검일지가 성공적으로 저장되었습니다!`);
            document.getElementById("input-notes").value = "";
        } else {
            queueOfflineInspection(payload);
        }
    } catch (err) {
        queueOfflineInspection(payload);
    }
}

// Dashboard Filters & Multi-Line Trend Charts
async function onGlobalFilterChange() {
    const startDate = document.getElementById("filter-start-date").value;
    const endDate = document.getElementById("filter-end-date").value;
    
    await populateHistoryTable(startDate, endDate);
    populateTrendSelectOptions();
    await renderTrendChart();
}

function resetFilters() {
    document.getElementById("filter-start-date").value = "";
    document.getElementById("filter-end-date").value = "";
    onGlobalFilterChange();
}

function populateTrendSelectOptions() {
    const select = document.getElementById("select-trend-field");
    select.innerHTML = "";
    
    const schema = buildingSchemas[currentBuildingCode];
    if (!schema) return;
    
    const addedGroups = new Set();
    
    // Only populate combined multi-line group comparison options to keep the dropdown clean and concise!
    schema.sections.forEach(sec => {
        sec.fields.forEach(f => {
            if (f.group && !addedGroups.has(f.group)) {
                addedGroups.add(f.group);
                const groupFields = sec.fields.filter(x => x.group === f.group);
                if (groupFields.length > 1) {
                    const baseLabel = f.label
                        .replace(/\s+[A-D]$/, '')
                        .replace(/\s+A\/B\/C\/D/, '')
                        .replace(/\s+\(전단\)/, '')
                        .replace(/\s+\(후단\)/, '');
                    const opt = document.createElement("option");
                    opt.value = `GROUP:${f.group}`;
                    opt.textContent = `📊 [통합 비교] ${baseLabel} (${groupFields.map(x => x.sub).join('/')})`;
                    select.appendChild(opt);
                }
            }
        });
    });
}

async function renderTrendChart() {
    const selectedVal = document.getElementById("select-trend-field").value;
    if (!selectedVal) return;
    
    const startDate = document.getElementById("filter-start-date").value;
    const endDate = document.getElementById("filter-end-date").value;
    
    const ctx = document.getElementById("trendChart").getContext("2d");
    if (trendChartInstance) {
        trendChartInstance.destroy();
    }
    
    if (selectedVal.startsWith("GROUP:")) {
        const groupName = selectedVal.replace("GROUP:", "");
        const schema = buildingSchemas[currentBuildingCode];
        
        let targetFields = [];
        schema.sections.forEach(sec => {
            sec.fields.forEach(f => {
                if (f.group === groupName) targetFields.push(f);
            });
        });
        
        const datasets = [];
        let allDates = new Set();
        const dateValuesMap = {};
        
        for (const f of targetFields) {
            let url = `/api/trends?building_code=${currentBuildingCode}&field_key=${f.key}`;
            if (startDate) url += `&start_date=${startDate}`;
            if (endDate) url += `&end_date=${endDate}`;
            
            const res = await fetch(url);
            const data = await res.json();
            
            data.dates.forEach((d, idx) => {
                allDates.add(d);
                if (!dateValuesMap[d]) dateValuesMap[d] = {};
                dateValuesMap[d][f.key] = data.values[idx];
            });
        }
        
        const sortedDates = Array.from(allDates).sort();
        
        targetFields.forEach(f => {
            const lineSub = f.sub || f.label;
            const lineColor = COLOR_PALETTE[lineSub] || COLOR_PALETTE["default"];
            const seriesVals = sortedDates.map(d => dateValuesMap[d] ? dateValuesMap[d][f.key] : null);
            
            datasets.push({
                label: f.label,
                data: seriesVals,
                borderColor: lineColor,
                backgroundColor: lineColor + "22",
                borderWidth: 3,
                pointRadius: 5,
                fill: false,
                tension: 0.2,
                spanGaps: true // Automatically connect line across skipped or non-daily dates!
            });
        });
        
        trendChartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels: sortedDates,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                spanGaps: true,
                plugins: {
                    legend: { display: true, position: "top" }
                },
                scales: {
                    x: { title: { display: true, text: "점검 일자" } },
                    y: { title: { display: true, text: "측정값" } }
                }
            }
        });
    } else {
        let url = `/api/trends?building_code=${currentBuildingCode}&field_key=${selectedVal}`;
        if (startDate) url += `&start_date=${selectedVal}`;
        if (endDate) url += `&end_date=${endDate}`;
        
        try {
            const res = await fetch(url);
            const data = await res.json();
            
            trendChartInstance = new Chart(ctx, {
                type: "line",
                data: {
                    labels: data.dates,
                    datasets: [{
                        label: selectedVal,
                        data: data.values,
                        borderColor: "#0284c7",
                        backgroundColor: "rgba(2, 132, 199, 0.1)",
                        borderWidth: 3,
                        pointRadius: 5,
                        fill: true,
                        tension: 0.2,
                        spanGaps: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    spanGaps: true,
                    plugins: {
                        legend: { display: true, position: "top" }
                    },
                    scales: {
                        x: { title: { display: true, text: "점검 일자" } },
                        y: { title: { display: true, text: "측정값" } }
                    }
                }
            });
        } catch (e) {
            console.error("Failed to render trend chart", e);
        }
    }
}

async function populateHistoryTable(startDate, endDate) {
    const tbody = document.getElementById("history-tbody");
    tbody.innerHTML = "";
    
    let url = `/api/inspections?building_code=${currentBuildingCode}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;
    
    try {
        const res = await fetch(url);
        const logs = await res.json();
        
        if (logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 20px; color: #64748b;">점검 기록이 없습니다.</td></tr>`;
            return;
        }
        
        logs.forEach(l => {
            const tr = document.createElement("tr");
            const bName = buildingSchemas[l.building_code] ? buildingSchemas[l.building_code].name : l.building_code;
            
            const keys = Object.keys(l.values);
            const summaryParts = keys.slice(0, 3).map(k => `${k}: ${l.values[k]}`);
            const summaryStr = summaryParts.join(", ") + (keys.length > 3 ? " ..." : "");
            
            tr.innerHTML = `
                <td>#${l.id}</td>
                <td><strong>${l.inspection_date}</strong></td>
                <td><span class="status-badge status-active">${bName}</span></td>
                <td>${l.inspector}</td>
                <td style="font-size: 0.82rem; color: #334155;">${summaryStr}</td>
                <td>${l.notes || '-'}</td>
                <td>
                    <button class="btn-action" onclick="viewLogDetail(${l.id})">조회</button>
                    <button class="btn-action btn-del" onclick="deleteLogRecord(${l.id})">삭제</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to load history table", e);
    }
}

async function viewLogDetail(logId) {
    try {
        const res = await fetch(`/api/inspections/${logId}`);
        const log = await res.json();
        
        const modalTitle = document.getElementById("modal-title");
        const modalBody = document.getElementById("modal-body");
        
        const bName = buildingSchemas[log.building_code] ? buildingSchemas[log.building_code].name : log.building_code;
        modalTitle.textContent = `[${bName}] ${log.inspection_date} 점검 상세 기록 (#${log.id})`;
        
        let html = `
            <div style="margin-bottom: 12px; font-size: 0.9rem; color: #475569;">
                <p><strong>점검자:</strong> ${log.inspector}</p>
                <p><strong>특이사항:</strong> ${log.notes || '없음'}</p>
            </div>
            <table class="excel-form-table">
                <thead>
                    <tr><th>항목 키</th><th>측정값</th></tr>
                </thead>
                <tbody>
        `;
        
        Object.keys(log.values).forEach(k => {
            html += `<tr><td><strong>${k}</strong></td><td>${log.values[k]}</td></tr>`;
        });
        
        html += `</tbody></table>`;
        modalBody.innerHTML = html;
        document.getElementById("modal-container").classList.add("active");
    } catch (e) {
        showToast("상세 정보를 가져오지 못했습니다.");
    }
}

function closeModal() {
    document.getElementById("modal-container").classList.remove("active");
}

async function deleteLogRecord(logId) {
    if (!confirm(`점검 기록 #${logId}를 정기로 삭제하시겠습니까?`)) return;
    
    try {
        const res = await fetch(`/api/inspections/${logId}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${authToken}` }
        });
        if (res.ok) {
            showToast("삭제되었습니다.");
            onGlobalFilterChange();
        } else {
            showToast("삭제하지 못했습니다.");
        }
    } catch (e) {
        showToast("서버 오류로 삭제에 실패했습니다.");
    }
}

function exportExcel() {
    const startDate = document.getElementById("filter-start-date").value;
    const endDate = document.getElementById("filter-end-date").value;
    
    let url = `/api/export-csv?building_code=${currentBuildingCode}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;
    
    window.location.href = url;
}

function showToast(msg) {
    const toast = document.getElementById("toast");
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2500);
}
