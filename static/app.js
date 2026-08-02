let buildingSchemas = {};
let currentBuildingCode = "2METAL";
let currentViewMode = "form";
let trendChartInstance = null;

document.addEventListener("DOMContentLoaded", async () => {
    document.getElementById("input-date").valueAsDate = new Date();
    await loadBuildingSchemas();
    renderBuildingTabs();
    selectBuilding(currentBuildingCode);
});

async function loadBuildingSchemas() {
    try {
        const res = await fetch("/api/buildings");
        buildingSchemas = await res.json();
    } catch (err) {
        console.error("Failed to load building schemas:", err);
        showToast("설비 데이터 로드 실패");
    }
}

function renderBuildingTabs() {
    const container = document.getElementById("building-tabs");
    container.innerHTML = "";
    
    for (const [code, bData] of Object.entries(buildingSchemas)) {
        const btn = document.createElement("button");
        btn.className = `tab-btn ${code === currentBuildingCode ? 'active' : ''}`;
        btn.textContent = bData.name;
        btn.onclick = () => selectBuilding(code);
        container.appendChild(btn);
    }
}

function selectBuilding(code) {
    currentBuildingCode = code;
    
    document.querySelectorAll(".tab-btn").forEach((btn, idx) => {
        const key = Object.keys(buildingSchemas)[idx];
        if (key === code) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    const bSchema = buildingSchemas[code];
    
    const lineGroup = document.getElementById("line-select-group");
    const lineSelect = document.getElementById("input-line");
    lineSelect.innerHTML = "";
    
    if (bSchema.has_lines && bSchema.lines.length > 0) {
        lineGroup.style.display = "flex";
        bSchema.lines.forEach(l => {
            const opt = document.createElement("option");
            opt.value = l;
            opt.textContent = l.replace("_", " ");
            lineSelect.appendChild(opt);
        });
    } else {
        lineGroup.style.display = "none";
    }

    renderFormFields(bSchema);
    
    if (currentViewMode === "dashboard") {
        populateTrendFieldSelector(bSchema);
        renderTrendChart();
        loadHistoryLogs();
    }
}

function switchViewMode(mode) {
    currentViewMode = mode;
    
    const formSec = document.getElementById("view-form");
    const dashSec = document.getElementById("view-dashboard");
    const formBtn = document.getElementById("btn-mode-form");
    const dashBtn = document.getElementById("btn-mode-dashboard");

    if (mode === "form") {
        formSec.classList.add("active");
        dashSec.classList.remove("active");
        formBtn.classList.add("active");
        dashBtn.classList.remove("active");
    } else {
        formSec.classList.remove("active");
        dashSec.classList.add("active");
        formBtn.classList.remove("active");
        dashBtn.classList.add("active");

        const bSchema = buildingSchemas[currentBuildingCode];
        populateTrendFieldSelector(bSchema);
        renderTrendChart();
        loadHistoryLogs();
    }
}

// Global Filter Handler: Syncs Trend Chart & History Log Table simultaneously
function onGlobalFilterChange() {
    renderTrendChart();
    loadHistoryLogs();
}

function resetFilters() {
    document.getElementById("filter-start-date").value = "";
    document.getElementById("filter-end-date").value = "";
    onGlobalFilterChange();
}

function renderFormFields(bSchema) {
    const container = document.getElementById("form-fields-container");
    container.innerHTML = "";

    bSchema.sections.forEach(sec => {
        const wrapper = document.createElement("div");
        wrapper.className = "excel-paper-wrapper";

        const banner = document.createElement("div");
        banner.className = "excel-section-banner";
        banner.innerHTML = `<span>📋</span> ${sec.title}`;
        wrapper.appendChild(banner);

        const table = document.createElement("table");
        table.className = "excel-form-table";

        table.innerHTML = `
            <thead>
                <tr>
                    <th style="width: 40%;">점검 항목</th>
                    <th style="width: 15%;">단위</th>
                    <th style="width: 20%;">기준 범위</th>
                    <th style="width: 25%;">측정 점검 수치 (입력)</th>
                </tr>
            </thead>
            <tbody>
            </tbody>
        `;

        const tbody = table.querySelector("tbody");

        sec.fields.forEach(field => {
            const tr = document.createElement("tr");
            tr.id = `row-${field.key}`;

            const tdLabel = document.createElement("td");
            tdLabel.className = "item-title";
            tdLabel.textContent = field.label;

            const tdUnit = document.createElement("td");
            tdUnit.className = "unit-badge";
            tdUnit.textContent = field.unit || "-";

            const tdRange = document.createElement("td");
            const rangeBadge = document.createElement("span");
            rangeBadge.className = "range-badge";
            rangeBadge.id = `badge-${field.key}`;
            rangeBadge.textContent = field.range || "-";
            tdRange.appendChild(rangeBadge);

            const tdInput = document.createElement("td");

            if (field.type === "select") {
                const selectEl = document.createElement("select");
                selectEl.id = `input-${field.key}`;
                selectEl.name = field.key;
                field.options.forEach(opt => {
                    const o = document.createElement("option");
                    o.value = opt;
                    o.textContent = opt;
                    selectEl.appendChild(o);
                });
                selectEl.onchange = () => markFieldAsModified(selectEl);
                tdInput.appendChild(selectEl);
            } else {
                const stepperWrapper = document.createElement("div");
                stepperWrapper.className = "input-stepper-wrapper";

                const btnMinus = document.createElement("button");
                btnMinus.type = "button";
                btnMinus.className = "stepper-btn";
                btnMinus.textContent = "-";
                btnMinus.onclick = () => stepInputValue(field.key, -0.1);

                const containerDiv = document.createElement("div");
                containerDiv.className = "stepper-input-container";

                const inp = document.createElement("input");
                inp.type = "number";
                inp.step = "any";
                inp.inputMode = "decimal";
                inp.id = `input-${field.key}`;
                inp.name = field.key;
                inp.placeholder = "0.00";
                if (field.auto_calc) {
                    inp.readOnly = true;
                    inp.style.background = "#f1f5f9";
                }

                inp.oninput = () => {
                    markFieldAsModified(inp);
                    validateFieldValue(field);
                    triggerAutoCalc();
                };

                const suffix = document.createElement("span");
                suffix.className = "unit-suffix";
                suffix.textContent = field.unit;

                containerDiv.appendChild(inp);
                if (field.unit) containerDiv.appendChild(suffix);

                const btnPlus = document.createElement("button");
                btnPlus.type = "button";
                btnPlus.className = "stepper-btn";
                btnPlus.textContent = "+";
                btnPlus.onclick = () => stepInputValue(field.key, 0.1);

                stepperWrapper.appendChild(btnMinus);
                stepperWrapper.appendChild(containerDiv);
                stepperWrapper.appendChild(btnPlus);

                tdInput.appendChild(stepperWrapper);
            }

            tr.appendChild(tdLabel);
            tr.appendChild(tdUnit);
            tr.appendChild(tdRange);
            tr.appendChild(tdInput);
            tbody.appendChild(tr);
        });

        wrapper.appendChild(table);
        container.appendChild(wrapper);
    });
}

function markFieldAsModified(el) {
    if (!el) return;
    el.classList.remove("is-previous-value");
    el.classList.add("is-modified-value");
}

async function copyPreviousLog() {
    try {
        const res = await fetch(`/api/inspections?building_code=${currentBuildingCode}`);
        const logs = await res.json();

        if (!logs || logs.length === 0) {
            showToast("이전 점검 기록이 없습니다.");
            return;
        }

        const latest = logs[0];
        const bSchema = buildingSchemas[currentBuildingCode];

        if (latest.inspector) {
            document.getElementById("input-inspector").value = latest.inspector;
        }
        if (latest.line_code && bSchema.has_lines) {
            document.getElementById("input-line").value = latest.line_code;
        }
        if (latest.notes) {
            document.getElementById("input-notes").value = latest.notes;
        }

        bSchema.sections.forEach(sec => {
            sec.fields.forEach(f => {
                const el = document.getElementById(`input-${f.key}`);
                if (el && latest.values[f.key] !== undefined) {
                    el.value = latest.values[f.key];
                    el.classList.remove("is-modified-value");
                    el.classList.add("is-previous-value");
                    validateFieldValue(f);
                }
            });
        });

        triggerAutoCalc();
        showToast(`📋 ${latest.inspection_date}의 이전 점검 값을 불러왔습니다 (수정 시 검정색 변경).`);
    } catch (err) {
        console.error("Copy previous log error:", err);
        showToast("이전 기록 불러오기 중 오류가 발생했습니다.");
    }
}

function stepInputValue(key, delta) {
    const input = document.getElementById(`input-${key}`);
    if (!input || input.readOnly) return;
    
    let currentVal = parseFloat(input.value) || 0;
    currentVal = Math.max(0, currentVal + delta);
    input.value = currentVal.toFixed(2);
    
    markFieldAsModified(input);

    const bSchema = buildingSchemas[currentBuildingCode];
    bSchema.sections.forEach(sec => {
        sec.fields.forEach(f => {
            if (f.key === key) validateFieldValue(f);
        });
    });
    triggerAutoCalc();
}

function validateFieldValue(field) {
    if (!field.range || field.range === "-") return;

    const input = document.getElementById(`input-${field.key}`);
    const tr = document.getElementById(`row-${field.key}`);
    const badge = document.getElementById(`badge-${field.key}`);

    if (!input || !tr || !badge) return;

    const rawVal = input.value.trim();
    if (rawVal === "") {
        tr.classList.remove("warning-out-range");
        badge.classList.remove("badge-out-range");
        badge.textContent = field.range;
        return;
    }

    const val = parseFloat(rawVal);
    let isNormal = true;
    
    if (field.range.includes("~")) {
        const parts = field.range.split("~").map(p => parseFloat(p.trim()));
        if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
            isNormal = (val >= parts[0] && val <= parts[1]);
        }
    } else if (field.range.includes("이하")) {
        const maxVal = parseFloat(field.range.replace("이하", "").trim());
        if (!isNaN(maxVal)) {
            isNormal = (val <= maxVal);
        }
    }

    if (!isNormal) {
        tr.classList.add("warning-out-range");
        badge.classList.add("badge-out-range");
        badge.textContent = `⚠️ 이탈 (${field.range})`;
    } else {
        tr.classList.remove("warning-out-range");
        badge.classList.remove("badge-out-range");
        badge.textContent = `✓ 정상 (${field.range})`;
    }
}

function triggerAutoCalc() {
    if (currentBuildingCode === "2METAL") {
        const feedFlowInp = document.getElementById("input-feed_flow");
        const prodFlowInp = document.getElementById("input-prod_flow");
        const recoveryInp = document.getElementById("input-recovery_rate");

        if (feedFlowInp && prodFlowInp && recoveryInp) {
            const feed = parseFloat(feedFlowInp.value);
            const prod = parseFloat(prodFlowInp.value);
            if (!isNaN(feed) && feed > 0 && !isNaN(prod)) {
                const rate = (prod / feed) * 100;
                recoveryInp.value = rate.toFixed(1);
            }
        }

        const roFeedPressInp = document.getElementById("input-ro_feed_press");
        const roBrinePressInp = document.getElementById("input-ro_brine_press");
        const diffPressInp = document.getElementById("input-diff_press");

        if (roFeedPressInp && roBrinePressInp && diffPressInp) {
            const fPress = parseFloat(roFeedPressInp.value);
            const bPress = parseFloat(roBrinePressInp.value);
            if (!isNaN(fPress) && !isNaN(bPress)) {
                const dp = Math.max(0, fPress - bPress);
                diffPressInp.value = dp.toFixed(2);
            }
        }
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();

    const bSchema = buildingSchemas[currentBuildingCode];
    const dateVal = document.getElementById("input-date").value;
    const inspectorVal = document.getElementById("input-inspector").value.trim();
    const lineVal = bSchema.has_lines ? document.getElementById("input-line").value : "";
    const notesVal = document.getElementById("input-notes").value.trim();

    if (!dateVal || !inspectorVal) {
        showToast("점검 일자와 점검자 성명을 입력해주세요.");
        return;
    }

    const values = {};
    bSchema.sections.forEach(sec => {
        sec.fields.forEach(field => {
            const el = document.getElementById(`input-${field.key}`);
            if (el) {
                values[field.key] = el.value.trim();
            }
        });
    });

    const payload = {
        building_code: currentBuildingCode,
        line_code: lineVal,
        inspection_date: dateVal,
        inspector: inspectorVal,
        values: values,
        notes: notesVal
    };

    try {
        const res = await fetch("/api/inspections", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            showToast("✅ 점검일지가 성공적으로 저장되었습니다.");
            bSchema.sections.forEach(sec => {
                sec.fields.forEach(field => {
                    const el = document.getElementById(`input-${field.key}`);
                    if (el && field.type !== "select") {
                        el.value = "";
                        el.classList.remove("is-previous-value", "is-modified-value");
                    }
                });
            });
            document.getElementById("input-notes").value = "";
        } else {
            showToast("❌ 저장 중 오류가 발생했습니다.");
        }
    } catch (err) {
        console.error("Submission error:", err);
        showToast("❌ 서버 통신 오류");
    }
}

function populateTrendFieldSelector(bSchema) {
    const sel = document.getElementById("select-trend-field");
    sel.innerHTML = "";

    bSchema.sections.forEach(sec => {
        sec.fields.forEach(f => {
            if (f.type !== "select") {
                const opt = document.createElement("option");
                opt.value = f.key;
                opt.textContent = `${f.label} (${f.unit || '-'})`;
                sel.appendChild(opt);
            }
        });
    });
}

// Render Trend Chart with Date Filters
async function renderTrendChart() {
    const sel = document.getElementById("select-trend-field");
    const fieldKey = sel.value;
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

        const bSchema = buildingSchemas[currentBuildingCode];
        let fieldLabel = fieldKey;
        bSchema.sections.forEach(sec => {
            sec.fields.forEach(f => {
                if (f.key === fieldKey) fieldLabel = f.label;
            });
        });

        trendChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: [{
                    label: fieldLabel,
                    data: data.values,
                    borderColor: '#1e40af',
                    backgroundColor: 'rgba(30, 64, 175, 0.1)',
                    borderWidth: 3,
                    pointBackgroundColor: '#0284c7',
                    pointRadius: 5,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#0f172a', font: { size: 14, weight: 'bold' } }
                    },
                    tooltip: {
                        backgroundColor: '#ffffff',
                        titleColor: '#1e40af',
                        bodyColor: '#0f172a',
                        borderColor: '#cbd5e1',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#475569' },
                        grid: { color: '#e2e8f0' }
                    },
                    y: {
                        ticks: { color: '#475569' },
                        grid: { color: '#e2e8f0' }
                    }
                }
            }
        });
    } catch (err) {
        console.error("Trend chart render error:", err);
    }
}

// Load History Logs Table with Date Filters
async function loadHistoryLogs() {
    const startDate = document.getElementById("filter-start-date").value;
    const endDate = document.getElementById("filter-end-date").value;

    let url = `/api/inspections?building_code=${currentBuildingCode}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;

    try {
        const res = await fetch(url);
        const logs = await res.json();

        const tbody = document.getElementById("history-tbody");
        tbody.innerHTML = "";

        if (logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-sub); padding: 24px;">선택한 기간에 조회된 점검 기록이 없습니다.</td></tr>`;
            return;
        }

        logs.forEach(l => {
            const tr = document.createElement("tr");

            const valEntries = Object.entries(l.values).slice(0, 3).map(([k, v]) => `${k}: ${v}`).join(", ");

            tr.innerHTML = `
                <td>#${l.id}</td>
                <td>${l.inspection_date}</td>
                <td><span class="range-badge">${buildingSchemas[l.building_code]?.name || l.building_code} ${l.line_code ? `(${l.line_code})` : ''}</span></td>
                <td>${l.inspector}</td>
                <td style="font-size:0.85rem; color: var(--text-sub);">${valEntries} ...</td>
                <td>${l.notes || '-'}</td>
                <td>
                    <button class="btn-action" onclick="viewLogDetail(${l.id})">상세보기</button>
                    <button class="btn-action btn-del" onclick="deleteLogRecord(${l.id})">삭제</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("History load error:", err);
    }
}

// Export Excel with Selected Date Filter Range
function exportExcel() {
    const startDate = document.getElementById("filter-start-date").value;
    const endDate = document.getElementById("filter-end-date").value;

    let url = `/api/export-csv?building_code=${currentBuildingCode}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;

    window.location.href = url;
}

async function viewLogDetail(logId) {
    try {
        const res = await fetch(`/api/inspections/${logId}`);
        const log = await res.json();

        const modalTitle = document.getElementById("modal-title");
        const modalBody = document.getElementById("modal-body");

        const bName = buildingSchemas[log.building_code]?.name || log.building_code;
        modalTitle.textContent = `${log.inspection_date} - ${bName} ${log.line_code ? `(${log.line_code})` : ''} 점검 상세`;

        let html = `
            <div style="margin-bottom: 16px; font-size: 0.95rem;">
                <p><strong>점검자:</strong> ${log.inspector}</p>
                <p><strong>특이사항:</strong> ${log.notes || '없음'}</p>
            </div>
            <table class="history-table" style="font-size:0.9rem;">
                <thead>
                    <tr><th>점검 항목</th><th>점검 수치</th></tr>
                </thead>
                <tbody>
        `;

        const bSchema = buildingSchemas[log.building_code];
        bSchema.sections.forEach(sec => {
            sec.fields.forEach(f => {
                const val = log.values[f.key] !== undefined ? log.values[f.key] : '-';
                html += `<tr><td>${f.label}</td><td><strong>${val} ${f.unit || ''}</strong></td></tr>`;
            });
        });

        html += `</tbody></table>`;
        modalBody.innerHTML = html;

        document.getElementById("modal-container").classList.add("active");
    } catch (err) {
        console.error("Detail load error:", err);
    }
}

async function deleteLogRecord(logId) {
    if (!confirm(`정말로 #${logId} 점검 기록을 삭제하시겠습니까?`)) return;

    try {
        const res = await fetch(`/api/inspections/${logId}`, { method: "DELETE" });
        if (res.ok) {
            showToast("삭제되었습니다.");
            loadHistoryLogs();
            renderTrendChart();
        } else {
            showToast("삭제 중 오류가 발생했습니다.");
        }
    } catch (err) {
        console.error("Delete error:", err);
    }
}

function closeModal() {
    document.getElementById("modal-container").classList.remove("active");
}

function showToast(msg) {
    const toast = document.getElementById("toast");
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => {
        toast.classList.remove("show");
    }, 2500);
}
