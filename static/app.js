let buildingSchemas = {};
let currentBuildingCode = "B_DONG";
let currentViewMode = "form"; // 'form' or 'dashboard'
let trendChartInstance = null;
let authToken = localStorage.getItem("ro_inspection_token") || "";

document.addEventListener("DOMContentLoaded", () => {
    checkAuthAndInit();
});

// Authentication Handlers
async function checkAuthAndInit() {
    if (!authToken) {
        showLoginModal();
        return;
    }
    
    try {
        const res = await fetch("/api/verify", {
            headers: { "Authorization": `Bearer ${authToken}` }
        });
        if (!res.ok) {
            throw new Error("Invalid session");
        }
        hideLoginModal();
        initApp();
    } catch (e) {
        localStorage.removeItem("ro_inspection_token");
        authToken = "";
        showLoginModal();
    }
}

function showLoginModal() {
    document.getElementById("login-modal").classList.add("active");
}

function hideLoginModal() {
    document.getElementById("login-modal").classList.remove("active");
}

async function handleLoginSubmit(e) {
    e.preventDefault();
    const idInput = document.getElementById("login-id").value.trim();
    const pwInput = document.getElementById("login-pw").value.trim();
    const errDiv = document.getElementById("login-error");
    errDiv.textContent = "";

    try {
        const res = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: idInput, password: pwInput })
        });
        const data = await res.json();
        if (!res.ok) {
            errDiv.textContent = data.detail || "로그인 실패";
            return;
        }
        
        authToken = data.token;
        localStorage.setItem("ro_inspection_token", authToken);
        hideLoginModal();
        initApp();
        showToast("로그인 성공!");
    } catch (err) {
        errDiv.textContent = "서버 연결 오류가 발생했습니다.";
    }
}

function handleLogout() {
    localStorage.removeItem("ro_inspection_token");
    authToken = "";
    showLoginModal();
    showToast("로그아웃 되었습니다.");
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
    if (currentViewMode === "form") {
        loadBuildingForm(code);
    } else {
        onGlobalFilterChange();
    }
}

function switchViewMode(mode) {
    currentViewMode = mode;
    document.getElementById("btn-mode-form").classList.toggle("active", mode === "form");
    document.getElementById("btn-mode-dashboard").classList.toggle("active", mode === "dashboard");
    document.getElementById("view-form").classList.toggle("active", mode === "form");
    document.getElementById("view-dashboard").classList.toggle("active", mode === "dashboard");
    
    if (mode === "dashboard") {
        onGlobalFilterChange();
    }
}

// Render Mobile High-Density Form
function loadBuildingForm(buildingCode) {
    const schema = buildingSchemas[buildingCode];
    if (!schema) return;
    
    const container = document.getElementById("form-fields-container");
    container.innerHTML = "";
    
    schema.sections.forEach(sec => {
        const card = document.createElement("div");
        card.className = "excel-paper-wrapper";
        
        let secHTML = `
            <div class="excel-section-banner">
                <span>📌 ${sec.title}</span>
                <span class="range-badge">항목 수: ${sec.fields.length}개</span>
            </div>
            <table class="excel-form-table">
                <thead>
                    <tr>
                        <th style="width: 32%;">항목명</th>
                        <th style="width: 15%;">단위</th>
                        <th style="width: 18%;">기준 범위</th>
                        <th style="width: 35%;">점검 수치 입력</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        sec.fields.forEach(f => {
            const groupAttr = f.group ? `data-group="${f.group}"` : '';
            const subAttr = f.sub ? `data-sub="${f.sub}"` : '';
            
            secHTML += `
                <tr id="row-${f.key}" ${groupAttr} ${subAttr}>
                    <td>
                        <span class="item-title">${f.label}</span>
                        <span id="badge-${f.key}" class="status-badge status-active">가동</span>
                    </td>
                    <td><span class="unit-badge">${f.unit || '-'}</span></td>
                    <td><span class="range-badge">${f.range}</span></td>
                    <td>
            `;
            
            if (f.type === "select") {
                secHTML += `
                    <select id="input-${f.key}" name="${f.key}" onchange="handleInputChange(this)">
                        ${f.options.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
                    </select>
                `;
            } else {
                secHTML += `
                    <div class="input-stepper-wrapper">
                        <button type="button" class="stepper-btn" onclick="stepValue('${f.key}', -0.1)">-</button>
                        <div class="stepper-input-container">
                            <input type="number" step="any" inputmode="decimal" id="input-${f.key}" name="${f.key}" 
                                   placeholder="값 입력" oninput="handleInputChange(this)">
                            ${f.unit ? `<span class="unit-suffix">${f.unit}</span>` : ''}
                        </div>
                        <button type="button" class="stepper-btn" onclick="stepValue('${f.key}', 0.1)">+</button>
                    </div>
                `;
            }
            
            secHTML += `
                    </td>
                </tr>
            `;
        });
        
        secHTML += `
                </tbody>
            </table>
        `;
        
        card.innerHTML = secHTML;
        container.appendChild(card);
    });
    
    // Initial evaluation of active/standby groups
    evaluateStandbyGroups();
}

function handleInputChange(input) {
    if (!input.classList.contains('is-modified-value')) {
        input.classList.remove('is-previous-value');
        input.classList.add('is-modified-value');
    }
    evaluateStandbyGroups();
}

// Active/Standby Auto-Locking Logic
function evaluateStandbyGroups() {
    const groups = {};
    const rows = document.querySelectorAll('tr[data-group]');
    
    rows.forEach(r => {
        const g = r.getAttribute('data-group');
        if (!groups[g]) groups[g] = [];
        groups[g].push(r);
    });
    
    Object.keys(groups).forEach(g => {
        const groupRows = groups[g];
        const subMap = {};
        
        groupRows.forEach(r => {
            const sub = r.getAttribute('data-sub');
            const input = r.querySelector('input, select');
            const hasVal = input && input.value !== "" && input.value !== null;
            if (!subMap[sub]) subMap[sub] = { rows: [], hasVal: false };
            subMap[sub].rows.push(r);
            if (hasVal) subMap[sub].hasVal = true;
        });
        
        const subs = Object.keys(subMap);
        const activeCount = subs.filter(s => subMap[s].hasVal).length;
        const totalSubs = subs.length;
        const reqActive = totalSubs - 1; // 1 standby unit logic
        
        if (activeCount >= reqActive && reqActive > 0) {
            subs.forEach(s => {
                const subObj = subMap[s];
                if (!subObj.hasVal) {
                    // Auto-lock remaining standby unit
                    subObj.rows.forEach(r => {
                        r.classList.add('is-standby-locked');
                        const input = r.querySelector('input, select');
                        if (input) {
                            input.disabled = true;
                            input.placeholder = "비가동";
                        }
                        const badge = r.querySelector('.status-badge');
                        if (badge) {
                            badge.className = "status-badge status-locked";
                            badge.textContent = "비가동";
                        }
                    });
                } else {
                    subObj.rows.forEach(r => {
                        r.classList.remove('is-standby-locked');
                        const input = r.querySelector('input, select');
                        if (input) input.disabled = false;
                        const badge = r.querySelector('.status-badge');
                        if (badge) {
                            badge.className = "status-badge status-active";
                            badge.textContent = "가동";
                        }
                    });
                }
            });
        } else {
            // Unlock all in group
            subs.forEach(s => {
                subMap[s].rows.forEach(r => {
                    r.classList.remove('is-standby-locked');
                    const input = r.querySelector('input, select');
                    if (input) {
                        input.disabled = false;
                        input.placeholder = "값 입력";
                    }
                    const badge = r.querySelector('.status-badge');
                    if (badge) {
                        badge.className = "status-badge status-active";
                        badge.textContent = "가동";
                    }
                });
            });
        }
    });
}

function stepValue(key, delta) {
    const input = document.getElementById(`input-${key}`);
    if (!input || input.disabled) return;
    
    let val = parseFloat(input.value) || 0;
    val = Math.round((val + delta) * 100) / 100;
    input.value = val;
    handleInputChange(input);
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
    const lineVal = document.getElementById("input-line").value || "";
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
        line_code: lineVal,
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

// Dashboard Filters & Trend Charts
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
    
    schema.sections.forEach(sec => {
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
    const fieldKey = document.getElementById("select-trend-field").value;
    if (!fieldKey) return;
    
    const startDate = document.getElementById("filter-start-date").value;
    const endDate = document.getElementById("filter-end-date").value;
    
    let url = `/api/trends?building_code=${currentBuildingCode}&field_key=${fieldKey}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;
    
    try {
        const res = await fetch(url);
        const data = await res.json();
        
        const ctx = document.getElementById("trendChart").getContext("2d");
        if (trendChartInstance) {
            trendChartInstance.destroy();
        }
        
        trendChartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels: data.dates,
                datasets: [{
                    label: fieldKey,
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
