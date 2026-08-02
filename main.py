import os
import io
import csv
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database
import seed_sample_data

app = FastAPI(title="RO 순수 점검일지 시스템 API", version="1.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    database.init_db()
    seed_sample_data.seed()

BUILDING_SCHEMAS = {
    "2METAL": {
        "name": "2메탈동",
        "has_lines": False,
        "lines": [],
        "sections": [
            {
                "title": "용수 카본",
                "fields": [
                    {"key": "carbon_inlet_press", "label": "1. 용수 Carbon Filter Inlet Pressure", "unit": "kg/cm²", "range": "1.5 ~ 4.0", "min": 0, "max": 10},
                    {"key": "carbon_outlet_press", "label": "2. 용수 Carbon Filter Outlet Pressure", "unit": "kg/cm²", "range": "1.0 ~ 3.5", "min": 0, "max": 10}
                ]
            },
            {
                "title": "R/O 구분 및 제원",
                "fields": [
                    {"key": "ro_status", "label": "R/O 운전 상태", "type": "select", "options": ["A운전", "B운전", "A+B 동시운전", "전체정지"], "unit": "", "range": "-"},
                    {"key": "ro_feed_pump_press", "label": "1. R/O Feed Pump Pressure", "unit": "kg/cm²", "range": "2.0 ~ 3.5", "min": 0, "max": 10},
                    {"key": "safety_inlet_press", "label": "2. R/O Safety Filter Inlet Pressure", "unit": "kg/cm²", "range": "1.2 ~ 2.5", "min": 0, "max": 10},
                    {"key": "safety_outlet_press", "label": "3. R/O Safety Filter Outlet Pressure", "unit": "kg/cm²", "range": "0.7 ~ 1.8", "min": 0, "max": 10},
                    {"key": "inlet_cond", "label": "4. R/O Inlet Conductivity", "unit": "uS/cm", "range": "20.0 ~ 50.0", "min": 0, "max": 200},
                    {"key": "outlet_cond", "label": "5. R/O Outlet Conductivity", "unit": "uS/cm", "range": "0 ~ 10.0", "min": 0, "max": 50},
                    {"key": "feed_flow", "label": "6. R/O Feed 수량", "unit": "m³/hr", "range": "50.0 ~ 70.0", "min": 0, "max": 150},
                    {"key": "prod_flow", "label": "7. R/O 생산수량", "unit": "m³/hr", "range": "45.0 ~ 60.0", "min": 0, "max": 150},
                    {"key": "brine_flow", "label": "8. R/O 농축수량", "unit": "m³/hr", "range": "8.0 ~ 15.0", "min": 0, "max": 50},
                    {"key": "recovery_rate", "label": "9. 회수율", "unit": "%", "range": "75.0 ~ 85.0", "min": 0, "max": 100, "auto_calc": "prod_flow / feed_flow * 100"},
                    {"key": "hp_pump_press", "label": "10. R/O High Pressure Pump Pressure", "unit": "kg/cm²", "range": "8.5 ~ 12.0", "min": 0, "max": 25},
                    {"key": "ro_feed_press", "label": "11. R/O Feed Pressure", "unit": "kg/cm²", "range": "6.5 ~ 8.0", "min": 0, "max": 15},
                    {"key": "ro_prod_press", "label": "12. R/O Product Pressure", "unit": "kg/cm²", "range": "0.5 ~ 3.0", "min": 0, "max": 10},
                    {"key": "ro_brine_1st_press", "label": "13. R/O 1'st Brine Pressure", "unit": "kg/cm²", "range": "4.5 ~ 7.0", "min": 0, "max": 15},
                    {"key": "ro_brine_press", "label": "14. R/O Brine Pressure", "unit": "kg/cm²", "range": "2.0 ~ 6.5", "min": 0, "max": 15},
                    {"key": "diff_press", "label": "15. D/P 차압", "unit": "kg/cm²", "range": "1.0 ~ 3.5", "min": 0, "max": 10, "auto_calc": "ro_feed_press - ro_brine_press"},
                    {"key": "feed_temp", "label": "16. R/O Feed Water Temperature", "unit": "°C", "range": "20.0 ~ 32.0", "min": 0, "max": 50}
                ]
            },
            {
                "title": "1F, 2메탈, 3F 필터",
                "fields": [
                    {"key": "tw_1f_inlet_press", "label": "1. TW 1-F Filter Inlet Pressure", "unit": "kg/cm²", "range": "4.0 ~ 6.5", "min": 0, "max": 10},
                    {"key": "tw_1f_outlet_press", "label": "2. TW 1-F Filter Outlet Pressure", "unit": "kg/cm²", "range": "4.0 ~ 6.5", "min": 0, "max": 10},
                    {"key": "metal_2_inlet_press", "label": "3. 2-Metal Filter Inlet Pressure", "unit": "kg/cm²", "range": "2.5 ~ 6.0", "min": 0, "max": 10},
                    {"key": "metal_2_outlet_press", "label": "4. 2-Metal Filter Outlet Pressure", "unit": "kg/cm²", "range": "4.0 ~ 6.0", "min": 0, "max": 10},
                    {"key": "tw_3f_inlet_press", "label": "5. TW 3-F Filter Inlet Pressure", "unit": "kg/cm²", "range": "4.5 ~ 6.0", "min": 0, "max": 10},
                    {"key": "tw_3f_outlet_press", "label": "6. TW 3-F Filter Outlet Pressure", "unit": "kg/cm²", "range": "1.5 ~ 6.0", "min": 0, "max": 10}
                ]
            }
        ]
    },
    "B_DONG": {
        "name": "B동",
        "has_lines": False,
        "lines": [],
        "sections": [
            {
                "title": "B동 RO 점검 항목",
                "fields": [
                    {"key": "pre_feed_pump_press", "label": "전처리 FEED PUMP 압력", "unit": "Kg/Cm²", "range": "1.0 ~ 7.0", "min": 0, "max": 15},
                    {"key": "ro_feed_pump_press", "label": "1차 R/O FEED PUMP 압력", "unit": "Kg/Cm²", "range": "3.0 ~ 4.0", "min": 0, "max": 10},
                    {"key": "ro_hp_pump_press", "label": "1차 R/O 고압 펌프 압력", "unit": "Kg/Cm²", "range": "10.0 ~ 14.0", "min": 0, "max": 20},
                    {"key": "ro_feed_press", "label": "1차 RO FEED 압력", "unit": "Kg/Cm²", "range": "4.5 ~ 6.5", "min": 0, "max": 10},
                    {"key": "ro_1st_brine_press", "label": "1차 RO 1st 농축수 압력", "unit": "Kg/Cm²", "range": "3.5 ~ 5.0", "min": 0, "max": 10},
                    {"key": "ro_2nd_brine_press", "label": "1차 RO 2nd 농축수 압력", "unit": "Kg/Cm²", "range": "2.0 ~ 3.2", "min": 0, "max": 10},
                    {"key": "ro_diff_press", "label": "1차 RO UNIT 차압", "unit": "Kg/Cm²", "range": "0 ~ 5.0", "min": 0, "max": 10},
                    {"key": "ro_prod_press", "label": "1차 RO 생산수 압력", "unit": "Kg/Cm²", "range": "0 ~ 1.0", "min": 0, "max": 5},
                    {"key": "ro_prod_flow", "label": "1차 RO 생산수 유량", "unit": "m³/hr", "range": "30 ~ 60", "min": 0, "max": 100},
                    {"key": "ro_brine_flow", "label": "1차 RO 농축수 유량", "unit": "m³/hr", "range": "15 ~ 155", "min": 0, "max": 200},
                    {"key": "ro_prod_cond", "label": "1차 RO 생산수 전도도", "unit": "uS/cm", "range": "0 ~ 10.0", "min": 0, "max": 50},
                    {"key": "ro_feed_temp", "label": "1차 R/O Feed Temperature", "unit": "°C", "range": "23 ~ 25", "min": 0, "max": 50}
                ]
            }
        ]
    },
    "C_DONG_1": {
        "name": "C동 1차",
        "has_lines": False,
        "lines": [],
        "sections": [
            {
                "title": "C동 1차 RO 점검 항목",
                "fields": [
                    {"key": "ro_feed_pump_press", "label": "1. R/O Feed Pump Pressure", "unit": "kg/cm²", "range": "4.5 ~ 6.0", "min": 0, "max": 10},
                    {"key": "safety_inlet_press", "label": "2. Safety Filter Inlet Pressure", "unit": "kg/cm²", "range": "1.5 ~ 2.5", "min": 0, "max": 10},
                    {"key": "safety_outlet_press", "label": "3. Safety Filter Outlet Pressure", "unit": "kg/cm²", "range": "1.4 ~ 2.2", "min": 0, "max": 10},
                    {"key": "inlet_cond", "label": "4. R/O Inlet Conductivity", "unit": "uS/cm", "range": "45.0 ~ 70.0", "min": 0, "max": 200},
                    {"key": "outlet_cond", "label": "5. R/O Outlet Conductivity", "unit": "uS/cm", "range": "8.0 ~ 12.0", "min": 0, "max": 50},
                    {"key": "prod_flow", "label": "6. R/O 생산수량", "unit": "m³/hr", "range": "30.0 ~ 40.0", "min": 0, "max": 100}
                ]
            }
        ]
    },
    "C_DONG_2": {
        "name": "C동 2차",
        "has_lines": False,
        "lines": [],
        "sections": [
            {
                "title": "C동 2차 RO 점검 항목",
                "fields": [
                    {"key": "raw_feed_pump_press", "label": "1. Raw Water Feed Pump Pressure", "unit": "kg/cm²", "range": "2.0 ~ 3.5", "min": 0, "max": 10},
                    {"key": "mf_inlet_temp", "label": "2. M/F Inlet Temperature", "unit": "°C", "range": "20.0 ~ 30.0", "min": 0, "max": 50},
                    {"key": "mf_inlet_press", "label": "3. M/F Inlet Pressure", "unit": "kg/cm²", "range": "1.0 ~ 2.0", "min": 0, "max": 10},
                    {"key": "ro_feed_pump_press", "label": "4. R/O Feed Pump Pressure", "unit": "kg/cm²", "range": "2.0 ~ 3.0", "min": 0, "max": 10},
                    {"key": "safety_inlet_press", "label": "5. Safety Filter Inlet Pressure", "unit": "kg/cm²", "range": "1.5 ~ 2.2", "min": 0, "max": 10},
                    {"key": "safety_outlet_press", "label": "6. Safety Filter Outlet Pressure", "unit": "kg/cm²", "range": "1.0 ~ 2.2", "min": 0, "max": 10}
                ]
            }
        ]
    },
    "E_DONG": {
        "name": "E동",
        "has_lines": True,
        "lines": ["RO_A", "RO_B", "RO_C"],
        "sections": [
            {
                "title": "E동 RO 점검 항목",
                "fields": [
                    {"key": "feed_pump_press", "label": "R/O FEED PUMP 압력", "unit": "Kg/Cm²", "range": "3.0 ~ 6.0", "min": 0, "max": 10},
                    {"key": "hp_pump_press", "label": "1차 R/O 고압 펌프 압력", "unit": "Kg/Cm²", "range": "10.0 ~ 13.0", "min": 0, "max": 20},
                    {"key": "feed_press", "label": "1차 RO FEED 압력", "unit": "Kg/Cm²", "range": "7.0 ~ 9.5", "min": 0, "max": 15},
                    {"key": "brine_1st_press", "label": "1차 RO 1st 농축수 압력", "unit": "Kg/Cm²", "range": "5.0 ~ 10.0", "min": 0, "max": 15},
                    {"key": "brine_2nd_press", "label": "1차 RO 2nd 농축수 압력", "unit": "Kg/Cm²", "range": "4.5 ~ 6.5", "min": 0, "max": 15},
                    {"key": "unit_diff_press", "label": "1차 RO UNIT 차압", "unit": "Kg/Cm²", "range": "0 ~ 5.0", "min": 0, "max": 10},
                    {"key": "prod_press", "label": "1차 RO 생산수 압력", "unit": "Kg/Cm²", "range": "0 ~ 3.0", "min": 0, "max": 5},
                    {"key": "prod_flow", "label": "1차 RO 생산수 유량", "unit": "m³/hr", "range": "50 ~ 70", "min": 0, "max": 120}
                ]
            }
        ]
    },
    "PS_1_2F": {
        "name": "PS 1.2F",
        "has_lines": True,
        "lines": ["RO_A", "RO_B", "RO_C", "RO_D"],
        "sections": [
            {
                "title": "PS 1~2층 RO 점검 항목",
                "fields": [
                    {"key": "feed_pump_press", "label": "R/O FEED PUMP 압력", "unit": "Kg/Cm²", "range": "3.5 ~ 12.5", "min": 0, "max": 20},
                    {"key": "inlet_flow", "label": "1차 R/O 인입 유량", "unit": "m³/hr", "range": "30 ~ 65", "min": 0, "max": 120},
                    {"key": "hp_pump_press", "label": "1차 R/O 고압 펌프 압력", "unit": "Kg/Cm²", "range": "11.0 ~ 18.0", "min": 0, "max": 25},
                    {"key": "feed_press", "label": "1차 RO FEED 압력", "unit": "Kg/Cm²", "range": "6.5 ~ 8.5", "min": 0, "max": 15},
                    {"key": "brine_1st_press", "label": "1차 RO 1st 농축수 압력", "unit": "Kg/Cm²", "range": "5.0 ~ 6.5", "min": 0, "max": 15},
                    {"key": "brine_2nd_press", "label": "1차 RO 2nd 농축수 압력", "unit": "Kg/Cm²", "range": "4.0 ~ 6.0", "min": 0, "max": 15}
                ]
            }
        ]
    },
    "PS_3F": {
        "name": "PS 3F",
        "has_lines": False,
        "lines": [],
        "sections": [
            {
                "title": "PS 3층 RO 점검 항목",
                "fields": [
                    {"key": "supply_press", "label": "R/O 공급 압력", "unit": "Kg/Cm²", "range": "3.0 ~ 5.0", "min": 0, "max": 10},
                    {"key": "inlet_flow", "label": "1차 R/O 인입수 유량", "unit": "m³/hr", "range": "30 ~ 75", "min": 0, "max": 120},
                    {"key": "hp_pump_press", "label": "1차 R/O 고압 펌프 압력", "unit": "Kg/Cm²", "range": "13.0 ~ 18.0", "min": 0, "max": 25},
                    {"key": "feed_press", "label": "1차 RO FEED 압력", "unit": "Kg/Cm²", "range": "7.0 ~ 9.0", "min": 0, "max": 15},
                    {"key": "brine_1st_press", "label": "1차 RO 1st 농축수 압력", "unit": "Kg/Cm²", "range": "5.5 ~ 7.0", "min": 0, "max": 15},
                    {"key": "brine_2nd_press", "label": "1차 RO 2nd 농축수 압력", "unit": "Kg/Cm²", "range": "4.5 ~ 6.0", "min": 0, "max": 15}
                ]
            }
        ]
    }
}

class InspectionLogCreate(BaseModel):
    building_code: str
    line_code: Optional[str] = ""
    inspection_date: str
    inspector: str
    values: Dict[str, Any]
    notes: Optional[str] = ""

@app.get("/api/buildings")
def get_buildings():
    return BUILDING_SCHEMAS

@app.get("/api/inspections")
def list_inspections(
    building_code: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    return database.get_logs(building_code, start_date, end_date)

@app.get("/api/inspections/{log_id}")
def get_inspection(log_id: int):
    log = database.get_log_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Inspection log not found")
    return log

@app.post("/api/inspections", status_code=201)
def create_inspection(payload: InspectionLogCreate):
    if payload.building_code not in BUILDING_SCHEMAS:
        raise HTTPException(status_code=400, detail="Invalid building code")
    
    log_id = database.create_log(
        building_code=payload.building_code,
        line_code=payload.line_code or "",
        inspection_date=payload.inspection_date,
        inspector=payload.inspector,
        values=payload.values,
        notes=payload.notes or ""
    )
    return {"id": log_id, "message": "Log created successfully"}

@app.put("/api/inspections/{log_id}")
def update_inspection(log_id: int, payload: InspectionLogCreate):
    if payload.building_code not in BUILDING_SCHEMAS:
        raise HTTPException(status_code=400, detail="Invalid building code")
        
    updated = database.update_log(
        log_id=log_id,
        building_code=payload.building_code,
        line_code=payload.line_code or "",
        inspection_date=payload.inspection_date,
        inspector=payload.inspector,
        values=payload.values,
        notes=payload.notes or ""
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Inspection log not found")
    return {"message": "Log updated successfully"}

@app.delete("/api/inspections/{log_id}")
def delete_inspection(log_id: int):
    deleted = database.delete_log(log_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Inspection log not found")
    return {"message": "Log deleted successfully"}

# Trend API with Date Filter (start_date, end_date)
@app.get("/api/trends")
def get_trends(
    building_code: str,
    field_key: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    logs = database.get_logs(building_code=building_code, start_date=start_date, end_date=end_date)
    logs.sort(key=lambda x: x["inspection_date"])
    
    dates = []
    values = []
    
    for l in logs:
        d = l["inspection_date"]
        v = l["values"].get(field_key)
        if v is not None and v != "":
            try:
                num_v = float(v)
                dates.append(d)
                values.append(num_v)
            except (ValueError, TypeError):
                pass
                
    return {
        "building_code": building_code,
        "field_key": field_key,
        "dates": dates,
        "values": values
    }

# CSV Export API with Date Filter (start_date, end_date)
@app.get("/api/export-csv")
def export_csv(
    building_code: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    logs = database.get_logs(building_code=building_code, start_date=start_date, end_date=end_date)
    
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)
    
    headers = ["ID", "점검일자", "건물/구분", "라인", "점검자", "특이사항"]
    
    field_map = {}
    if building_code and building_code in BUILDING_SCHEMAS:
        bSchema = BUILDING_SCHEMAS[building_code]
        for sec in bSchema["sections"]:
            for f in sec["fields"]:
                field_map[f["key"]] = f"{f['label']} ({f['unit']})"
                headers.append(f"{f['label']} ({f['unit']})")
    else:
        all_keys = set()
        for l in logs:
            all_keys.update(l["values"].keys())
        for k in sorted(all_keys):
            field_map[k] = k
            headers.append(k)
            
    writer.writerow(headers)
    
    for l in logs:
        b_name = BUILDING_SCHEMAS.get(l["building_code"], {}).get("name", l["building_code"])
        row = [
            l["id"],
            l["inspection_date"],
            b_name,
            l["line_code"] or "-",
            l["inspector"],
            l["notes"] or "-"
        ]
        for k in field_map.keys():
            row.append(l["values"].get(k, ""))
        writer.writerow(row)
        
    output.seek(0)
    filename = f"RO_Inspection_Logs_{building_code or 'ALL'}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
