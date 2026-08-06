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
    "default": "#2563eb"
};

document.addEventListener("DOMContentLoaded", () => {
    checkAuthAndInit();
});

// Authentication Handlers
async function checkAuthAndInit() {
    if (!authToken) {
        showLoggedOutState();
        loadBuildingTabsOnly();
        return;
    }
    
    try {
        const res = await fetch("/api/verify", {
            headers: { "Authorization": `Bearer ${authToken}` }
        });
        if (!res.ok) {
            throw new Error("Invalid session");
        }
        showLoggedInState();
        initApp();
    } catch (e) {
        localStorage.removeItem("ro_inspection_token");
        authToken = "";
        showLoggedOutState();
        loadBuildingTabsOnly();
    }
}

function showLoggedOutState() {
    document.getElementById("header-login-area").style.display = "flex";
    document.getElementById("header-user-area").style.display = "none";
    document.getElementById("auth-lock-banner").style.display = "block";
    document.getElementById("auth-content-area").style.display = "none";
}

function showLoggedInState() {
    document.getElementById("header-login-area").style.display = "none";
    document.getElementById("header-user-area").style.display = "flex";
    document.getElementById("auth-lock-banner").style.display = "none";
    document.getElementById("auth-content-area").style.display = "block";
}

async function handleInlineLoginSubmit(e) {
    e.preventDefault();
    const idInput = document.getElementById("inline-login-id").value.trim();
    const pwInput = document.getElementById("inline-login-pw").value.trim();
    const errDiv = document.getElementById("inline-login-error");
    errDiv.textContent = "";

    try {
        const res = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: idInput, password: pwInput })
        });
        const data = await res.json();
        if (!res.ok) {
            errDiv.textContent = data.detail || "오류";
            return;
        }
        
        authToken = data.token;
        localStorage.setItem("ro_inspection_token", authToken);
        showLoggedInState();
        initApp();
        showToast("로그인 성공!");
    } catch (err) {
        errDiv.textContent = "연결 오류";
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

// App Initialization
async function initApp() {
    document.getElementById("input-date").value = new Date().toISOString().split("T")[0];
    
    try {
        const res = await fetch("/api/buildings");
        buildingSchemas = await res.json();
        renderBuildingTabs();
        loadBuildingForm(currentBuildingCode);
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
        btn.textContent = schema.name;
        btn.onclick = () => switchBuildingTab(code);
        tabsContainer.appendChild(btn);
    });
}

function switchBuildingTab(code) {
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
    currentViewMode = mode;
    document.getElementById("btn-mode-form").classList.toggle("active", mode === "form");
    document.getElementById("btn-mode-dashboard").classList.toggle("active", mode === "dashboard");
    document.getElementById("view-form").classList.toggle("active", mode === "form");
    document.getElementById("view-dashboard").classList.toggle("active", mode === "dashboard");
    
    if (mode === "dashboard") {
        onGlobalFilterChange();
    }
}

// Render Form with 2-col (A/B), 3-col (A/B/C), 4-col (EDI A/B/C/D) Multi-Column Grid
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
                const f = g.fields[0];
                secHTML += `
                    <div class="grid-row-item" id="row-${f.key}">
                        <div class="grid-row-header">
                            <span>${f.label}</span>
                            <span class="range-badge">범위: ${f.range}</span>
                        </div>
                        <div class="grid-cols-container grid-1col">
                            ${renderFieldInputCell(f)}
                        </div>
                    </div>
                `;
            } else {
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
            const baseLabel = f.label.replace(/\s+[A-D]$/, '').replace(/\s+A\/B\/C\/D/, '').replace(/\s+[A-D]-[1-4]/, '');
            if (!map.has(f.group)) {
                const groupObj = { baseLabel: baseLabel, fields: [] };
                map.set(f.group, groupObj);
                groups.push(groupObj);
            }
            map.get(f.group).fields.push(f);
        } else {
            groups.push({ baseLabel: f.label, fields: [f] });
        }
    });
    
    return groups;
}

function renderFieldInputCell(f) {
    const groupAttr = f.group ? `data-group="${f.group}"` : '';
    const subAttr = f.sub ? `data-sub="${f.sub}"` : '';
    const subLabel = f.sub ? `라인 ${f.sub}` : f.label;
    
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
    
    return `
        <div class="grid-col-cell" id="cell-${f.key}" ${groupAttr} ${subAttr}>
            <div class="cell-header">
                <span class="cell-title">${subLabel}</span>
                <span id="badge-${f.key}" class="status-badge status-active">가동</span>
            </div>
            <div class="cell-input-container">
                <input type="number" step="any" inputmode="decimal" id="input-${f.key}" name="${f.key}" 
                       placeholder="수치" oninput="handleInputChange(this)">
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
}

// Active/Standby Auto-Locking Logic (0 treated as empty/unentered)
function evaluateStandbyGroups() {
    const groups = {};
    const cells = document.querySelectorAll('.grid-col-cell[data-group]');
    
    cells.forEach(c => {
        const g = c.getAttribute('data-group');
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
        const activeCount = subs.filter(s => subMap[s].hasVal).length;
        const totalSubs = subs.length;
        const reqActive = totalSubs - 1;
        
        if (activeCount >= reqActive && reqActive > 0) {
            subs.forEach(s => {
                const subObj = subMap[s];
                if (!subObj.hasVal) {
                    subObj.cells.forEach(c => {
                        c.classList.add('is-standby-locked');
                        const input = c.querySelector('input, select');
                        if (input) {
                            input.disabled = true;
                            input.placeholder = "비가동";
                        }
                        const key = c.id.replace('cell-', '');
                        const badge = document.getElementById(`badge-${key}`);
                        if (badge) {
                            badge.className = "status-badge status-locked";
                            badge.textContent = "비가동";
                        }
                    });
                } else {
                    subObj.cells.forEach(c => {
                        c.classList.remove('is-standby-locked');
                        const input = c.querySelector('input, select');
                        if (input) input.disabled = false;
                        const key = c.id.replace('cell-', '');
                        const badge = document.getElementById(`badge-${key}`);
                        if (badge) {
                            badge.className = "status-badge status-active";
                            badge.textContent = "가동";
                        }
                    });
                }
            });
        } else {
            subs.forEach(s => {
                subMap[s].cells.forEach(c => {
                    c.classList.remove('is-standby-locked');
                    const input = c.querySelector('input, select');
                    if (input) {
                        input.disabled = false;
                        input.placeholder = "수치";
                    }
                    const key = c.id.replace('cell-', '');
                    const badge = document.getElementById(`badge-${key}`);
                    if (badge) {
                        badge.className = "status-badge status-active";
                        badge.textContent = "가동";
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
        showToast(`이전 점검 값(${prevLog.inspection_date}) 불러오기 완료!`);
    } catch (e) {
        showToast("이전 기록을 가져오지 못했습니다.");
    }
}

// Form Submit Handler
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
            showToast("✅ 점검일지가 성공적으로 저장되었습니다!");
            document.getElementById("input-notes").value = "";
        } else {
            showToast("❌ 저장 중 오류가 발생했습니다.");
        }
    } catch (err) {
        showToast("❌ 서버와의 통신에 실패했습니다.");
    }
}

// Dashboard Filters & Multi-Line Trend Charts (Pumps A/B/C/D, EDI 4-modules together!)
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
    
    schema.sections.forEach(sec => {
        // First add grouped multi-line comparison options
        sec.fields.forEach(f => {
            if (f.group && !addedGroups.has(f.group)) {
                addedGroups.add(f.group);
                const groupFields = sec.fields.filter(x => x.group === f.group);
                if (groupFields.length > 1) {
                    const baseLabel = f.label.replace(/\s+[A-D]$/, '').replace(/\s+A\/B\/C\/D/, '');
                    const opt = document.createElement("option");
                    opt.value = `GROUP:${f.group}`;
                    opt.textContent = `📊 [통합 비교] ${baseLabel} (${groupFields.map(x => x.sub).join('/')})`;
                    select.appendChild(opt);
                }
            }
        });
        
        // Next add individual single field options
        sec.fields.forEach(f => {
            if (f.type !== "select") {
                const opt = document.createElement("option");
                opt.value = f.key;
                opt.textContent = `[${sec.title}] ${f.label}`;
                select.appendChild(opt);
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
        // Multi-line comparison chart (e.g. Pump A/B/C, EDI A/B/C/D together!)
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
        const dateValuesMap = {}; // { date: { fieldKey: value } }
        
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
                tension: 0.2
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
        // Single field trend chart
        let url = `/api/trends?building_code=${currentBuildingCode}&field_key=${selectedVal}`;
        if (startDate) url += `&start_date=${startDate}`;
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
                        tension: 0.2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
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
