import os
import io
import csv
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.responses import StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database
import seed_sample_data

app = FastAPI(title="RO/EDI 순수 운영점검일지 통합 관리 API", version="4.2.0")

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

@app.get("/api/ping")
def ping():
    return Response(
        content='{"status":"ok"}',
        media_type="application/json",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache"
        }
    )

class LoginRequest(BaseModel):
    user_id: str
    password: str

class InspectionLogCreate(BaseModel):
    building_code: str
    line_code: Optional[str] = ""
    inspection_date: str
    inspector: str
    values: Dict[str, Any]
    notes: Optional[str] = ""

# Comprehensive Building Schemas (Matching 100% of Excel & PDF Checklists)
BUILDING_SCHEMAS = {
    "B_DONG": {
        "name": "B동",
        "sections": [
            {
                "title": "전처리 FEED PUMP",
                "fields": [
                    {"key": "pre_feed_pump_press", "label": "전처리 FEED PUMP 압력", "unit": "Kg/Cm²", "range": "3~6"},
                    {"key": "pre_feed_pump_flow_a", "label": "전처리 FEED PUMP 유량 A", "unit": "m³/hr", "range": "30~80", "group": "b_pre_pump_flow", "sub": "A"},
                    {"key": "pre_feed_pump_flow_b", "label": "전처리 FEED PUMP 유량 B", "unit": "m³/hr", "range": "30~80", "group": "b_pre_pump_flow", "sub": "B"}
                ]
            },
            {
                "title": "1차 R/O",
                "fields": [
                    {"key": "ro_1st_feed_pump_press_a", "label": "R/O FEED PUMP 압력 A", "unit": "Kg/Cm²", "range": "3~5", "group": "b_ro1_fpump", "sub": "A"},
                    {"key": "ro_1st_feed_pump_press_b", "label": "R/O FEED PUMP 압력 B", "unit": "Kg/Cm²", "range": "3~5", "group": "b_ro1_fpump", "sub": "B"},
                    {"key": "ro_1st_feed_pump_press_c", "label": "R/O FEED PUMP 압력 C", "unit": "Kg/Cm²", "range": "3~5", "group": "b_ro1_fpump", "sub": "C"},
                    
                    {"key": "ro_1st_hp_pump_press_a", "label": "1차 R/O 고압 펌프 압력 A", "unit": "Kg/Cm²", "range": "7~15", "group": "b_ro1_hppump", "sub": "A"},
                    {"key": "ro_1st_hp_pump_press_b", "label": "1차 R/O 고압 펌프 압력 B", "unit": "Kg/Cm²", "range": "7~15", "group": "b_ro1_hppump", "sub": "B"},
                    {"key": "ro_1st_hp_pump_press_c", "label": "1차 R/O 고압 펌프 압력 C", "unit": "Kg/Cm²", "range": "7~15", "group": "b_ro1_hppump", "sub": "C"},
                    
                    {"key": "ro_1st_feed_press_a", "label": "1차 RO FEED 압력 A", "unit": "Kg/Cm²", "range": "7~15", "group": "b_ro1_fpress", "sub": "A"},
                    {"key": "ro_1st_feed_press_b", "label": "1차 RO FEED 압력 B", "unit": "Kg/Cm²", "range": "7~15", "group": "b_ro1_fpress", "sub": "B"},
                    
                    {"key": "ro_1st_brine_1st_press_a", "label": "1차 RO 1st 농축수 압력 A", "unit": "Kg/Cm²", "range": "7~15", "group": "b_ro1_b1press", "sub": "A"},
                    {"key": "ro_1st_brine_1st_press_b", "label": "1차 RO 1st 농축수 압력 B", "unit": "Kg/Cm²", "range": "7~15", "group": "b_ro1_b1press", "sub": "B"},
                    
                    {"key": "ro_1st_brine_2nd_press_a", "label": "1차 RO 2nd 농축수 압력 A", "unit": "Kg/Cm²", "range": "7~15", "group": "b_ro1_b2press", "sub": "A"},
                    {"key": "ro_1st_brine_2nd_press_b", "label": "1차 RO 2nd 농축수 압력 B", "unit": "Kg/Cm²", "range": "7~15", "group": "b_ro1_b2press", "sub": "B"},
                    
                    {"key": "ro_1st_unit_diff_press_a", "label": "1차 RO UNIT 차압 A", "unit": "Kg/Cm²", "range": "0~5", "group": "b_ro1_udiff", "sub": "A"},
                    {"key": "ro_1st_unit_diff_press_b", "label": "1차 RO UNIT 차압 B", "unit": "Kg/Cm²", "range": "0~5", "group": "b_ro1_udiff", "sub": "B"},
                    
                    {"key": "ro_1st_prod_press_a", "label": "1차 RO 생산수 압력 A", "unit": "Kg/Cm²", "range": "0~1", "group": "b_ro1_ppress", "sub": "A"},
                    {"key": "ro_1st_prod_press_b", "label": "1차 RO 생산수 압력 B", "unit": "Kg/Cm²", "range": "0~1", "group": "b_ro1_ppress", "sub": "B"},
                    
                    {"key": "ro_1st_prod_flow_a", "label": "1차 RO 생산수 유량 A", "unit": "m³/hr", "range": "30~60", "group": "b_ro1_pflow", "sub": "A"},
                    {"key": "ro_1st_prod_flow_b", "label": "1차 RO 생산수 유량 B", "unit": "m³/hr", "range": "30~60", "group": "b_ro1_pflow", "sub": "B"},
                    
                    {"key": "ro_1st_brine_flow_a", "label": "1차 RO 농축수 유량 A", "unit": "m³/hr", "range": "15~155", "group": "b_ro1_bflow", "sub": "A"},
                    {"key": "ro_1st_brine_flow_b", "label": "1차 RO 농축수 유량 B", "unit": "m³/hr", "range": "15~155", "group": "b_ro1_bflow", "sub": "B"},
                    
                    {"key": "ro_1st_prod_cond_a", "label": "1차 RO 생산수 전도도 A", "unit": "uS/cm", "range": "10이하", "group": "b_ro1_pcond", "sub": "A"},
                    {"key": "ro_1st_prod_cond_b", "label": "1차 RO 생산수 전도도 B", "unit": "uS/cm", "range": "10이하", "group": "b_ro1_pcond", "sub": "B"},
                    
                    {"key": "ro_1st_feed_temp_a", "label": "R/O Feed Temperature A", "unit": "°C", "range": "23~25", "group": "b_ro1_ftemp", "sub": "A"},
                    {"key": "ro_1st_feed_temp_b", "label": "R/O Feed Temperature B", "unit": "°C", "range": "23~25", "group": "b_ro1_ftemp", "sub": "B"}
                ]
            },
            {
                "title": "2차 R/O",
                "fields": [
                    {"key": "ro_2nd_hp_pump_press_a", "label": "2차 R/O 고압 펌프 압력 A", "unit": "Kg/Cm²", "range": "7~12", "group": "b_ro2_hppump", "sub": "A"},
                    {"key": "ro_2nd_hp_pump_press_b", "label": "2차 R/O 고압 펌프 압력 B", "unit": "Kg/Cm²", "range": "7~12", "group": "b_ro2_hppump", "sub": "B"},
                    {"key": "ro_2nd_feed_press", "label": "2차 R/O FEED 압력", "unit": "Kg/Cm²", "range": "7~12"},
                    {"key": "ro_2nd_brine_1st_press", "label": "2차 R/O 1st 농축수 압력", "unit": "Kg/Cm²", "range": "7~12"},
                    {"key": "ro_2nd_brine_2nd_press", "label": "2차 R/O 2nd 농축수 압력", "unit": "Kg/Cm²", "range": "7~12"},
                    {"key": "ro_2nd_unit_diff_press", "label": "2차 R/O UNIT 차압", "unit": "Kg/Cm²", "range": "0~5"},
                    {"key": "ro_2nd_prod_press", "label": "2차 R/O 생산수 압력", "unit": "Kg/Cm²", "range": "0~2"},
                    {"key": "ro_2nd_prod_flow", "label": "2차 R/O 생산수 유량", "unit": "m³/hr", "range": "38~50"},
                    {"key": "ro_2nd_brine_flow", "label": "2차 R/O 농축수 유량", "unit": "m³/hr", "range": "3.5~5"},
                    {"key": "ro_2nd_prod_cond", "label": "2차 R/O 생산수 전도도", "unit": "uS/cm", "range": "0.3~1"}
                ]
            },
            {
                "title": "EDI",
                "fields": [
                    {"key": "edi_feed_pump_press_a", "label": "EDI FEED PUMP 압력 A", "unit": "Kg/Cm²", "range": "3~6", "group": "b_edi_fpump", "sub": "A"},
                    {"key": "edi_feed_pump_press_b", "label": "EDI FEED PUMP 압력 B", "unit": "Kg/Cm²", "range": "3~6", "group": "b_edi_fpump", "sub": "B"},
                    
                    {"key": "edi_feed_flow_a", "label": "EDI FEED 유량 A", "unit": "m³/hr", "range": "10~13", "group": "b_edi_fflow", "sub": "A"},
                    {"key": "edi_feed_flow_b", "label": "EDI FEED 유량 B", "unit": "m³/hr", "range": "10~13", "group": "b_edi_fflow", "sub": "B"},
                    {"key": "edi_feed_flow_c", "label": "EDI FEED 유량 C", "unit": "m³/hr", "range": "10~13", "group": "b_edi_fflow", "sub": "C"},
                    {"key": "edi_feed_flow_d", "label": "EDI FEED 유량 D", "unit": "m³/hr", "range": "10~13", "group": "b_edi_fflow", "sub": "D"},
                    
                    {"key": "edi_brine_flow_a", "label": "EDI 농축수 유량 A", "unit": "m³/hr", "range": "0.5~1.5", "group": "b_edi_bflow", "sub": "A"},
                    {"key": "edi_brine_flow_b", "label": "EDI 농축수 유량 B", "unit": "m³/hr", "range": "0.5~1.5", "group": "b_edi_bflow", "sub": "B"},
                    {"key": "edi_brine_flow_c", "label": "EDI 농축수 유량 C", "unit": "m³/hr", "range": "0.5~1.5", "group": "b_edi_bflow", "sub": "C"},
                    {"key": "edi_brine_flow_d", "label": "EDI 농축수 유량 D", "unit": "m³/hr", "range": "0.5~1.5", "group": "b_edi_bflow", "sub": "D"},
                    
                    {"key": "edi_inlet_press_a", "label": "EDI 인입수 압력 A", "unit": "Kg/Cm²", "range": "1~4", "group": "b_edi_inpress", "sub": "A"},
                    {"key": "edi_inlet_press_b", "label": "EDI 인입수 압력 B", "unit": "Kg/Cm²", "range": "1~4", "group": "b_edi_inpress", "sub": "B"},
                    {"key": "edi_inlet_press_c", "label": "EDI 인입수 압력 C", "unit": "Kg/Cm²", "range": "1~4", "group": "b_edi_inpress", "sub": "C"},
                    {"key": "edi_inlet_press_d", "label": "EDI 인입수 압력 D", "unit": "Kg/Cm²", "range": "1~4", "group": "b_edi_inpress", "sub": "D"},

                    {"key": "edi_in_brine_press_a", "label": "EDI 인입 농축수 압력 A", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "b_edi_inbpress", "sub": "A"},
                    {"key": "edi_in_brine_press_b", "label": "EDI 인입 농축수 압력 B", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "b_edi_inbpress", "sub": "B"},
                    {"key": "edi_in_brine_press_c", "label": "EDI 인입 농축수 압력 C", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "b_edi_inbpress", "sub": "C"},
                    {"key": "edi_in_brine_press_d", "label": "EDI 인입 농축수 압력 D", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "b_edi_inbpress", "sub": "D"},

                    {"key": "edi_prod_press_a", "label": "EDI 생산수 압력 A", "unit": "Kg/Cm²", "range": "0~2", "group": "b_edi_ppress", "sub": "A"},
                    {"key": "edi_prod_press_b", "label": "EDI 생산수 압력 B", "unit": "Kg/Cm²", "range": "0~2", "group": "b_edi_ppress", "sub": "B"},
                    {"key": "edi_prod_press_c", "label": "EDI 생산수 압력 C", "unit": "Kg/Cm²", "range": "0~2", "group": "b_edi_ppress", "sub": "C"},
                    {"key": "edi_prod_press_d", "label": "EDI 생산수 압력 D", "unit": "Kg/Cm²", "range": "0~2", "group": "b_edi_ppress", "sub": "D"},

                    {"key": "edi_prod_brine_press_a", "label": "EDI 생산 농축수 압력 A", "unit": "Kg/Cm²", "range": "0~2", "group": "b_edi_pbpress", "sub": "A"},
                    {"key": "edi_prod_brine_press_b", "label": "EDI 생산 농축수 압력 B", "unit": "Kg/Cm²", "range": "0~2", "group": "b_edi_pbpress", "sub": "B"},
                    {"key": "edi_prod_brine_press_c", "label": "EDI 생산 농축수 압력 C", "unit": "Kg/Cm²", "range": "0~2", "group": "b_edi_pbpress", "sub": "C"},
                    {"key": "edi_prod_brine_press_d", "label": "EDI 생산 농축수 압력 D", "unit": "Kg/Cm²", "range": "0~2", "group": "b_edi_pbpress", "sub": "D"},
                    
                    {"key": "edi_amp_a", "label": "EDI MODULE AMP A", "unit": "AMP", "range": "2~6", "group": "b_edi_amp", "sub": "A"},
                    {"key": "edi_amp_b", "label": "EDI MODULE AMP B", "unit": "AMP", "range": "2~6", "group": "b_edi_amp", "sub": "B"},
                    {"key": "edi_amp_c", "label": "EDI MODULE AMP C", "unit": "AMP", "range": "2~6", "group": "b_edi_amp", "sub": "C"},
                    {"key": "edi_amp_d", "label": "EDI MODULE AMP D", "unit": "AMP", "range": "2~6", "group": "b_edi_amp", "sub": "D"},
                    
                    {"key": "edi_volt_a", "label": "EDI MODULE VOLT A", "unit": "VOLT", "range": "20~250", "group": "b_edi_volt", "sub": "A"},
                    {"key": "edi_volt_b", "label": "EDI MODULE VOLT B", "unit": "VOLT", "range": "20~250", "group": "b_edi_volt", "sub": "B"},
                    {"key": "edi_volt_c", "label": "EDI MODULE VOLT C", "unit": "VOLT", "range": "20~250", "group": "b_edi_volt", "sub": "C"},
                    {"key": "edi_volt_d", "label": "EDI MODULE VOLT D", "unit": "VOLT", "range": "20~250", "group": "b_edi_volt", "sub": "D"},
                    
                    {"key": "edi_total_prod_flow", "label": "EDI 생산수 유량", "unit": "m³/hr", "range": "30~35"},
                    {"key": "edi_total_prod_cond", "label": "EDI 생산수 전도도", "unit": "MΩ·cm", "range": "15~18"}
                ]
            },
            {
                "title": "DI / M/B POLISHER",
                "fields": [
                    {"key": "di_feed_pump_press_a", "label": "DI FEED PUMP 압력 A", "unit": "Kg/Cm²", "range": "3~6", "group": "b_di_fpump", "sub": "A"},
                    {"key": "di_feed_pump_press_b", "label": "DI FEED PUMP 압력 B", "unit": "Kg/Cm²", "range": "3~6", "group": "b_di_fpump", "sub": "B"},
                    {"key": "di_supply_temp", "label": "DI 공급수 온도", "unit": "°C", "range": "24~26"},
                    {"key": "di_polisher_purity", "label": "DI M/B POLISHER 후단 순도", "unit": "MΩ·cm", "range": "15~18"},
                    
                    {"key": "di_resin_trap_press_front", "label": "DI RESIN TRAP 압력 (전단)", "unit": "Kg/Cm²", "range": "0.5~1.5", "group": "b_resin_trap", "sub": "전단"},
                    {"key": "di_resin_trap_press_rear", "label": "DI RESIN TRAP 압력 (후단)", "unit": "Kg/Cm²", "range": "0.5~1.5", "group": "b_resin_trap", "sub": "후단"},
                    
                    {"key": "uf_brine_flow", "label": "ULTRA FILTER 농축수 유량", "unit": "m³/hr", "range": "1.0~3.0"},
                    {"key": "di_supply_press", "label": "DI 공급 압력", "unit": "Kg/Cm²", "range": "2~4"},
                    {"key": "di_supply_flow", "label": "DI 공급 유량", "unit": "m³/hr", "range": "30~40"},
                    {"key": "di_supply_purity", "label": "DI 공급 순도", "unit": "MΩ·cm", "range": "18.0"}
                ]
            }
        ]
    },
    "C_DONG_1": {
        "name": "C동 1차",
        "sections": [
            {
                "title": "C동 1차 R/O 점검 항목",
                "fields": [
                    {"key": "ro_feed_pump_press", "label": "1. R/O Feed Pump Pressure", "unit": "kg/cm²", "range": "4.5~6.0"},
                    {"key": "mf_inlet_press", "label": "2. MICRO FILTER 인입수 압력", "unit": "kg/cm²", "range": "1.5~2.5"},
                    {"key": "mf_prod_press", "label": "3. MICRO FILTER 생산수 압력", "unit": "kg/cm²", "range": "1.4~2.2"},
                    {"key": "inlet_cond", "label": "4. R/O 인입수 전도도", "unit": "uS/cm", "range": "45.0~70.0"},
                    {"key": "prod_cond", "label": "5. R/O 생산수 전도도", "unit": "uS/cm", "range": "8.0~12.0"},
                    {"key": "prod_flow", "label": "6. R/O 생산수 유량", "unit": "m³/hr", "range": "30.0~40.0"},
                    {"key": "brine_flow", "label": "7. R/O 농축수 유량", "unit": "m³/hr", "range": "10.0~20.0"},
                    {"key": "hp_pump_press", "label": "8. R/O 고압 P/P 압력", "unit": "kg/cm²", "range": "10.0~15.0"},
                    {"key": "ro_feed_press", "label": "9. R/O Feed Pressure", "unit": "kg/cm²", "range": "5.0~12.0"},
                    {"key": "brine_1st_press", "label": "10. R/O 1차 농축수 압력", "unit": "kg/cm²", "range": "5.0~10.0"},
                    {"key": "brine_2nd_press", "label": "11. R/O 2차 농축수 압력", "unit": "kg/cm²", "range": "5.0~10.0"},
                    {"key": "unit_diff_press", "label": "12. R/O UNIT 차압", "unit": "kg/cm²", "range": "0~5.0"},
                    {"key": "prod_press", "label": "13. R/O Product Pressure", "unit": "kg/cm²", "range": "0~3.0"},
                    {"key": "prod_temp", "label": "14. R/O 생산수 온도", "unit": "°C", "range": "20.0~30.0"}
                ]
            }
        ]
    },
    "D_DONG_2METAL": {
        "name": "D동 2메탈",
        "sections": [
            {
                "title": "R/O 구분 (A/B운전 - 선택)",
                "fields": [
                    {"key": "ro_status", "label": "R/O 운전 구분 (선택)", "type": "select", "options": ["A운전", "B운전", "전체정지"], "unit": "", "range": "-"},
                    {"key": "ro_feed_pump_press", "label": "1. R/O Feed Pump Pressure", "unit": "kg/cm²", "range": "2.0~3.5"},
                    {"key": "mf_inlet_press", "label": "2. R/O MICRO FILTER 인입수 압력", "unit": "kg/cm²", "range": "1.2~2.5"},
                    {"key": "mf_prod_press", "label": "3. R/O MICRO FILTER 생산수 압력", "unit": "kg/cm²", "range": "0.7~1.8"},
                    {"key": "inlet_cond", "label": "4. R/O 인입수 전도도", "unit": "uS/cm", "range": "20.0~50.0"},
                    {"key": "prod_cond", "label": "5. R/O 생산수 전도도", "unit": "uS/cm", "range": "0~10.0"},
                    {"key": "inlet_flow", "label": "6. R/O 인입수 유량", "unit": "m³/hr", "range": "50.0~70.0"},
                    {"key": "prod_flow", "label": "7. R/O 생산수 유량", "unit": "m³/hr", "range": "45.0~60.0"},
                    {"key": "brine_flow", "label": "8. R/O 농축수 유량", "unit": "m³/hr", "range": "8.0~15.0"},
                    {"key": "hp_pump_press", "label": "9. R/O High Pressure Pump Pressure", "unit": "kg/cm²", "range": "8.5~12.0"},
                    {"key": "ro_feed_press", "label": "10. R/O Feed Pressure", "unit": "kg/cm²", "range": "6.5~8.0"},
                    {"key": "brine_1st_press", "label": "11. R/O 1차 농축수 압력", "unit": "kg/cm²", "range": "4.5~7.0"},
                    {"key": "brine_2nd_press", "label": "12. R/O 2차 농축수 압력", "unit": "kg/cm²", "range": "2.0~6.5"},
                    {"key": "unit_diff_press", "label": "13. R/O UNIT 차압", "unit": "kg/cm²", "range": "1.0~3.5"},
                    {"key": "prod_press", "label": "14. R/O Product Pressure", "unit": "kg/cm²", "range": "0.5~3.0"},
                    {"key": "prod_temp", "label": "15. R/O 생산수 온도", "unit": "°C", "range": "20.0~32.0"}
                ]
            },
            {
                "title": "2메탈, 3F 필터",
                "fields": [
                    {"key": "metal_inlet_press", "label": "1. 2-Metal Filter Inlet Pressure", "unit": "kg/cm²", "range": "2.5~6.0"},
                    {"key": "metal_outlet_press", "label": "2. 2-Metal Filter Outlet Pressure", "unit": "kg/cm²", "range": "4.0~6.0"},
                    {"key": "tw_3f_inlet_press", "label": "3. TW 3-F Filter Inlet Pressure", "unit": "kg/cm²", "range": "4.5~6.0"},
                    {"key": "tw_3f_outlet_press", "label": "4. TW 3-F Filter Outlet Pressure", "unit": "kg/cm²", "range": "1.5~6.0"}
                ]
            }
        ]
    },
    "D_DONG_PS_1_2F": {
        "name": "D동 1.2F PS",
        "sections": [
            {
                "title": "1차 R/O (RO A, B, C, D 4개 라인)",
                "fields": [
                    {"key": "ro_fpump_press_a", "label": "1차 R/O FEED PUMP 압력 A", "unit": "Kg/Cm²", "range": "4~7", "group": "d_ro1_fpump", "sub": "A"},
                    {"key": "ro_fpump_press_b", "label": "1차 R/O FEED PUMP 압력 B", "unit": "Kg/Cm²", "range": "4~7", "group": "d_ro1_fpump", "sub": "B"},
                    {"key": "ro_fpump_press_c", "label": "1차 R/O FEED PUMP 압력 C", "unit": "Kg/Cm²", "range": "4~7", "group": "d_ro1_fpump", "sub": "C"},
                    {"key": "ro_fpump_press_d", "label": "1차 R/O FEED PUMP 압력 D", "unit": "Kg/Cm²", "range": "4~7", "group": "d_ro1_fpump", "sub": "D"},

                    {"key": "ro_inlet_flow_a", "label": "1차 R/O 인입 유량 A", "unit": "m³/hr", "range": "30~60", "group": "d_ro1_inflow", "sub": "A"},
                    {"key": "ro_inlet_flow_b", "label": "1차 R/O 인입 유량 B", "unit": "m³/hr", "range": "30~60", "group": "d_ro1_inflow", "sub": "B"},
                    {"key": "ro_inlet_flow_c", "label": "1차 R/O 인입 유량 C", "unit": "m³/hr", "range": "30~60", "group": "d_ro1_inflow", "sub": "C"},
                    {"key": "ro_inlet_flow_d", "label": "1차 R/O 인입 유량 D", "unit": "m³/hr", "range": "30~60", "group": "d_ro1_inflow", "sub": "D"},

                    {"key": "ro_hppump_press_a", "label": "1차 R/O 고압 펌프 압력 A", "unit": "Kg/Cm²", "range": "13~18", "group": "d_ro1_hppump", "sub": "A"},
                    {"key": "ro_hppump_press_b", "label": "1차 R/O 고압 펌프 압력 B", "unit": "Kg/Cm²", "range": "13~18", "group": "d_ro1_hppump", "sub": "B"},
                    {"key": "ro_hppump_press_c", "label": "1차 R/O 고압 펌프 압력 C", "unit": "Kg/Cm²", "range": "13~18", "group": "d_ro1_hppump", "sub": "C"},
                    {"key": "ro_hppump_press_d", "label": "1차 R/O 고압 펌프 압력 D", "unit": "Kg/Cm²", "range": "13~18", "group": "d_ro1_hppump", "sub": "D"},

                    {"key": "ro_fpress_a", "label": "1차 RO FEED 압력 A", "unit": "Kg/Cm²", "range": "7~15", "group": "d_ro1_fpress", "sub": "A"},
                    {"key": "ro_fpress_b", "label": "1차 RO FEED 압력 B", "unit": "Kg/Cm²", "range": "7~15", "group": "d_ro1_fpress", "sub": "B"},
                    {"key": "ro_fpress_c", "label": "1차 RO FEED 압력 C", "unit": "Kg/Cm²", "range": "7~15", "group": "d_ro1_fpress", "sub": "C"},
                    {"key": "ro_fpress_d", "label": "1차 RO FEED 압력 D", "unit": "Kg/Cm²", "range": "7~15", "group": "d_ro1_fpress", "sub": "D"},

                    {"key": "ro_b1press_a", "label": "1차 RO 1st 농축수 압력 A", "unit": "Kg/Cm²", "range": "5~10", "group": "d_ro1_b1press", "sub": "A"},
                    {"key": "ro_b1press_b", "label": "1차 RO 1st 농축수 압력 B", "unit": "Kg/Cm²", "range": "5~10", "group": "d_ro1_b1press", "sub": "B"},
                    {"key": "ro_b1press_c", "label": "1차 RO 1st 농축수 압력 C", "unit": "Kg/Cm²", "range": "5~10", "group": "d_ro1_b1press", "sub": "C"},
                    {"key": "ro_b1press_d", "label": "1차 RO 1st 농축수 압력 D", "unit": "Kg/Cm²", "range": "5~10", "group": "d_ro1_b1press", "sub": "D"},

                    {"key": "ro_b2press_a", "label": "1차 RO 2nd 농축수 압력 A", "unit": "Kg/Cm²", "range": "5~10", "group": "d_ro1_b2press", "sub": "A"},
                    {"key": "ro_b2press_b", "label": "1차 RO 2nd 농축수 압력 B", "unit": "Kg/Cm²", "range": "5~10", "group": "d_ro1_b2press", "sub": "B"},
                    {"key": "ro_b2press_c", "label": "1차 RO 2nd 농축수 압력 C", "unit": "Kg/Cm²", "range": "5~10", "group": "d_ro1_b2press", "sub": "C"},
                    {"key": "ro_b2press_d", "label": "1차 RO 2nd 농축수 압력 D", "unit": "Kg/Cm²", "range": "5~10", "group": "d_ro1_b2press", "sub": "D"},

                    {"key": "ro_udiff_a", "label": "1차 RO UNIT 차압 A", "unit": "Kg/Cm²", "range": "0~5", "group": "d_ro1_udiff", "sub": "A"},
                    {"key": "ro_udiff_b", "label": "1차 RO UNIT 차압 B", "unit": "Kg/Cm²", "range": "0~5", "group": "d_ro1_udiff", "sub": "B"},
                    {"key": "ro_udiff_c", "label": "1차 RO UNIT 차압 C", "unit": "Kg/Cm²", "range": "0~5", "group": "d_ro1_udiff", "sub": "C"},
                    {"key": "ro_udiff_d", "label": "1차 RO UNIT 차압 D", "unit": "Kg/Cm²", "range": "0~5", "group": "d_ro1_udiff", "sub": "D"},

                    {"key": "ro_ppress_a", "label": "1차 RO 생산수 압력 A", "unit": "Kg/Cm²", "range": "0~2", "group": "d_ro1_ppress", "sub": "A"},
                    {"key": "ro_ppress_b", "label": "1차 RO 생산수 압력 B", "unit": "Kg/Cm²", "range": "0~2", "group": "d_ro1_ppress", "sub": "B"},
                    {"key": "ro_ppress_c", "label": "1차 RO 생산수 압력 C", "unit": "Kg/Cm²", "range": "0~2", "group": "d_ro1_ppress", "sub": "C"},
                    {"key": "ro_ppress_d", "label": "1차 RO 생산수 압력 D", "unit": "Kg/Cm²", "range": "0~2", "group": "d_ro1_ppress", "sub": "D"},

                    {"key": "ro_pflow_a", "label": "1차 RO 생산수 유량 A", "unit": "m³/hr", "range": "30~60", "group": "d_ro1_pflow", "sub": "A"},
                    {"key": "ro_pflow_b", "label": "1차 RO 생산수 유량 B", "unit": "m³/hr", "range": "30~60", "group": "d_ro1_pflow", "sub": "B"},
                    {"key": "ro_pflow_c", "label": "1차 RO 생산수 유량 C", "unit": "m³/hr", "range": "30~60", "group": "d_ro1_pflow", "sub": "C"},
                    {"key": "ro_pflow_d", "label": "1차 RO 생산수 유량 D", "unit": "m³/hr", "range": "30~60", "group": "d_ro1_pflow", "sub": "D"},

                    {"key": "ro_bflow_a", "label": "1차 RO 농축수 유량 A", "unit": "m³/hr", "range": "8~15", "group": "d_ro1_bflow", "sub": "A"},
                    {"key": "ro_bflow_b", "label": "1차 RO 농축수 유량 B", "unit": "m³/hr", "range": "8~15", "group": "d_ro1_bflow", "sub": "B"},
                    {"key": "ro_bflow_c", "label": "1차 RO 농축수 유량 C", "unit": "m³/hr", "range": "8~15", "group": "d_ro1_bflow", "sub": "C"},
                    {"key": "ro_bflow_d", "label": "1차 RO 농축수 유량 D", "unit": "m³/hr", "range": "8~15", "group": "d_ro1_bflow", "sub": "D"},

                    {"key": "ro_inlet_cond", "label": "1차 RO 인입수 전도도", "unit": "uS/cm", "range": "20이하"},

                    {"key": "ro_pcond_a", "label": "1차 RO 생산수 전도도 A", "unit": "uS/cm", "range": "10이하", "group": "d_ro1_pcond", "sub": "A"},
                    {"key": "ro_pcond_b", "label": "1차 RO 생산수 전도도 B", "unit": "uS/cm", "range": "10이하", "group": "d_ro1_pcond", "sub": "B"},
                    {"key": "ro_pcond_c", "label": "1차 RO 생산수 전도도 C", "unit": "uS/cm", "range": "10이하", "group": "d_ro1_pcond", "sub": "C"},
                    {"key": "ro_pcond_d", "label": "1차 RO 생산수 전도도 D", "unit": "uS/cm", "range": "10이하", "group": "d_ro1_pcond", "sub": "D"},

                    {"key": "ro_ftemp_a", "label": "R/O Feed Temperature A", "unit": "°C", "range": "23~25", "group": "d_ro1_ftemp", "sub": "A"},
                    {"key": "ro_ftemp_b", "label": "R/O Feed Temperature B", "unit": "°C", "range": "23~25", "group": "d_ro1_ftemp", "sub": "B"},
                    {"key": "ro_ftemp_c", "label": "R/O Feed Temperature C", "unit": "°C", "range": "23~25", "group": "d_ro1_ftemp", "sub": "C"},
                    {"key": "ro_ftemp_d", "label": "R/O Feed Temperature D", "unit": "°C", "range": "23~25", "group": "d_ro1_ftemp", "sub": "D"}
                ]
            },
            {
                "title": "2차 R/O (1,2F & 3F용)",
                "fields": [
                    {"key": "ro2_hppump_ps12_a", "label": "1,2F용 2차 RO 고압 펌프 압력 A", "unit": "Kg/Cm²", "range": "7~12", "group": "d_ro2_ps12_pump", "sub": "A"},
                    {"key": "ro2_hppump_ps12_b", "label": "1,2F용 2차 RO 고압 펌프 압력 B", "unit": "Kg/Cm²", "range": "7~12", "group": "d_ro2_ps12_pump", "sub": "B"},
                    
                    {"key": "ro2_hppump_ps3f_a", "label": "3F용 2차 RO 고압 펌프 압력 A", "unit": "Kg/Cm²", "range": "7~12", "group": "d_ro2_ps3f_pump", "sub": "A"},
                    {"key": "ro2_hppump_ps3f_b", "label": "3F용 2차 RO 고압 펌프 압력 B", "unit": "Kg/Cm²", "range": "7~12", "group": "d_ro2_ps3f_pump", "sub": "B"},

                    {"key": "ro2_fpress_ps12", "label": "2차 RO FEED 압력", "unit": "Kg/Cm²", "range": "7~12", "group": "d_ro2_fpress", "sub": "1,2F"},
                    {"key": "ro2_fpress_ps3f", "label": "3F용 2차 RO FEED 압력", "unit": "Kg/Cm²", "range": "7~12", "group": "d_ro2_fpress", "sub": "3F용"},

                    {"key": "ro2_b1press_ps12", "label": "2차 RO 1st 농축수 압력", "unit": "Kg/Cm²", "range": "7~12", "group": "d_ro2_b1press", "sub": "1,2F"},
                    {"key": "ro2_b1press_ps3f", "label": "3F용 2차 RO 1st 농축수 압력", "unit": "Kg/Cm²", "range": "7~12", "group": "d_ro2_b1press", "sub": "3F용"},

                    {"key": "ro2_b2press_ps12", "label": "2차 RO 2nd 농축수 압력", "unit": "Kg/Cm²", "range": "7~12", "group": "d_ro2_b2press", "sub": "1,2F"},
                    {"key": "ro2_b2press_ps3f", "label": "3F용 2차 RO 2nd 농축수 압력", "unit": "Kg/Cm²", "range": "7~12", "group": "d_ro2_b2press", "sub": "3F용"},

                    {"key": "ro2_udiff_ps12", "label": "2차 RO UNIT 차압", "unit": "Kg/Cm²", "range": "0~5", "group": "d_ro2_udiff", "sub": "1,2F"},
                    {"key": "ro2_udiff_ps3f", "label": "3F용 2차 RO UNIT 차압", "unit": "Kg/Cm²", "range": "0~5", "group": "d_ro2_udiff", "sub": "3F용"},

                    {"key": "ro2_ppress_ps12", "label": "2차 RO 생산수 압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_ro2_ppress", "sub": "1,2F"},
                    {"key": "ro2_ppress_ps3f", "label": "3F용 2차 RO 생산수 압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_ro2_ppress", "sub": "3F용"},

                    {"key": "ro2_pflow_ps12", "label": "2차 RO 생산수 유량", "unit": "m³/hr", "range": "38~50", "group": "d_ro2_pflow", "sub": "1,2F"},
                    {"key": "ro2_pflow_ps3f", "label": "3F용 2차 RO 생산수 유량", "unit": "m³/hr", "range": "38~50", "group": "d_ro2_pflow", "sub": "3F용"},

                    {"key": "ro2_bflow_ps12", "label": "2차 RO 농축수 유량", "unit": "m³/hr", "range": "3~10", "group": "d_ro2_bflow", "sub": "1,2F"},
                    {"key": "ro2_bflow_ps3f", "label": "3F용 2차 RO 농축수 유량", "unit": "m³/hr", "range": "3~10", "group": "d_ro2_bflow", "sub": "3F용"},

                    {"key": "ro2_pcond_ps12", "label": "2차 RO 생산수 전도도", "unit": "uS/cm", "range": "0~5", "group": "d_ro2_pcond", "sub": "1,2F"},
                    {"key": "ro2_pcond_ps3f", "label": "3F용 2차 RO 생산수 전도도", "unit": "uS/cm", "range": "0~5", "group": "d_ro2_pcond", "sub": "3F용"}
                ]
            },
            {
                "title": "EDI \"A\"",
                "fields": [
                    {"key": "edi_a_fpump_a", "label": "A/B) EDI FEED PUMP 압력 A", "unit": "Kg/Cm²", "range": "3~8", "group": "d_edi_fpump", "sub": "A"},
                    {"key": "edi_a_fpump_b", "label": "A/B) EDI FEED PUMP 압력 B", "unit": "Kg/Cm²", "range": "3~8", "group": "d_edi_fpump", "sub": "B"},

                    {"key": "edi_a1_fflow", "label": "A) EDI A-1 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_a_fflow", "sub": "1"},
                    {"key": "edi_a2_fflow", "label": "A) EDI A-2 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_a_fflow", "sub": "2"},
                    {"key": "edi_a3_fflow", "label": "A) EDI A-3 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_a_fflow", "sub": "3"},
                    {"key": "edi_a4_fflow", "label": "A) EDI A-4 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_a_fflow", "sub": "4"},

                    {"key": "edi_a1_bflow", "label": "A) EDI A-1 농축수 유량", "unit": "m³/hr", "range": "0.5~3.5", "group": "d_edi_a_bflow", "sub": "1"},
                    {"key": "edi_a2_bflow", "label": "A) EDI A-2 농축수 유량", "unit": "m³/hr", "range": "0.5~3.5", "group": "d_edi_a_bflow", "sub": "2"},
                    {"key": "edi_a3_bflow", "label": "A) EDI A-3 농축수 유량", "unit": "m³/hr", "range": "0.5~3.5", "group": "d_edi_a_bflow", "sub": "3"},
                    {"key": "edi_a4_bflow", "label": "A) EDI A-4 농축수 유량", "unit": "m³/hr", "range": "0.5~3.5", "group": "d_edi_a_bflow", "sub": "4"},

                    {"key": "edi_a1_inpress", "label": "A) EDI A-1 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "d_edi_a_inpress", "sub": "1"},
                    {"key": "edi_a2_inpress", "label": "A) EDI A-2 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "d_edi_a_inpress", "sub": "2"},
                    {"key": "edi_a3_inpress", "label": "A) EDI A-3 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "d_edi_a_inpress", "sub": "3"},
                    {"key": "edi_a4_inpress", "label": "A) EDI A-4 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "d_edi_a_inpress", "sub": "4"},

                    {"key": "edi_a1_bpress", "label": "A) EDI A-1 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "d_edi_a_bpress", "sub": "1"},
                    {"key": "edi_a2_bpress", "label": "A) EDI A-2 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "d_edi_a_bpress", "sub": "2"},
                    {"key": "edi_a3_bpress", "label": "A) EDI A-3 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "d_edi_a_bpress", "sub": "3"},
                    {"key": "edi_a4_bpress", "label": "A) EDI A-4 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "d_edi_a_bpress", "sub": "4"},

                    {"key": "edi_a1_ppress_out", "label": "A) EDI A-1 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_a_ppress_out", "sub": "1"},
                    {"key": "edi_a2_ppress_out", "label": "A) EDI A-2 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_a_ppress_out", "sub": "2"},
                    {"key": "edi_a3_ppress_out", "label": "A) EDI A-3 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_a_ppress_out", "sub": "3"},
                    {"key": "edi_a4_ppress_out", "label": "A) EDI A-4 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_a_ppress_out", "sub": "4"},

                    {"key": "edi_a1_bpress_out", "label": "A) EDI A-1 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_a_bpress_out", "sub": "1"},
                    {"key": "edi_a2_bpress_out", "label": "A) EDI A-2 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_a_bpress_out", "sub": "2"},
                    {"key": "edi_a3_bpress_out", "label": "A) EDI A-3 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_a_bpress_out", "sub": "3"},
                    {"key": "edi_a4_bpress_out", "label": "A) EDI A-4 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_a_bpress_out", "sub": "4"},

                    {"key": "edi_a1_amp", "label": "A) EDI A-1 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "d_edi_a_amp", "sub": "1"},
                    {"key": "edi_a2_amp", "label": "A) EDI A-2 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "d_edi_a_amp", "sub": "2"},
                    {"key": "edi_a3_amp", "label": "A) EDI A-3 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "d_edi_a_amp", "sub": "3"},
                    {"key": "edi_a4_amp", "label": "A) EDI A-4 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "d_edi_a_amp", "sub": "4"},

                    {"key": "edi_a1_volt", "label": "A) EDI A-1 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "d_edi_a_volt", "sub": "1"},
                    {"key": "edi_a2_volt", "label": "A) EDI A-2 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "d_edi_a_volt", "sub": "2"},
                    {"key": "edi_a3_volt", "label": "A) EDI A-3 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "d_edi_a_volt", "sub": "3"},
                    {"key": "edi_a4_volt", "label": "A) EDI A-4 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "d_edi_a_volt", "sub": "4"},

                    {"key": "edi_a_pflow", "label": "A) EDI 생산수 유량", "unit": "m³/hr", "range": "30~45"},
                    {"key": "edi_a_pcond", "label": "A) EDI 생산수 전도도", "unit": "MΩ·cm", "range": "15~18"}
                ]
            },
            {
                "title": "EDI \"B\"",
                "fields": [
                    {"key": "edi_b1_fflow", "label": "B) EDI B-1 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_b_fflow", "sub": "1"},
                    {"key": "edi_b2_fflow", "label": "B) EDI B-2 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_b_fflow", "sub": "2"},
                    {"key": "edi_b3_fflow", "label": "B) EDI B-3 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_b_fflow", "sub": "3"},
                    {"key": "edi_b4_fflow", "label": "B) EDI B-4 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_b_fflow", "sub": "4"},

                    {"key": "edi_b1_bflow", "label": "B) EDI B-1 농축수 유량", "unit": "m³/hr", "range": "0.5~3.5", "group": "d_edi_b_bflow", "sub": "1"},
                    {"key": "edi_b2_bflow", "label": "B) EDI B-2 농축수 유량", "unit": "m³/hr", "range": "0.5~3.5", "group": "d_edi_b_bflow", "sub": "2"},
                    {"key": "edi_b3_bflow", "label": "B) EDI B-3 농축수 유량", "unit": "m³/hr", "range": "0.5~3.5", "group": "d_edi_b_bflow", "sub": "3"},
                    {"key": "edi_b4_bflow", "label": "B) EDI B-4 농축수 유량", "unit": "m³/hr", "range": "0.5~3.5", "group": "d_edi_b_bflow", "sub": "4"},

                    {"key": "edi_b1_inpress", "label": "B) EDI B-1 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "d_edi_b_inpress", "sub": "1"},
                    {"key": "edi_b2_inpress", "label": "B) EDI B-2 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "d_edi_b_inpress", "sub": "2"},
                    {"key": "edi_b3_inpress", "label": "B) EDI B-3 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "d_edi_b_inpress", "sub": "3"},
                    {"key": "edi_b4_inpress", "label": "B) EDI B-4 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "d_edi_b_inpress", "sub": "4"},

                    {"key": "edi_b1_bpress", "label": "B) EDI B-1 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "d_edi_b_bpress", "sub": "1"},
                    {"key": "edi_b2_bpress", "label": "B) EDI B-2 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "d_edi_b_bpress", "sub": "2"},
                    {"key": "edi_b3_bpress", "label": "B) EDI B-3 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "d_edi_b_bpress", "sub": "3"},
                    {"key": "edi_b4_bpress", "label": "B) EDI B-4 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "d_edi_b_bpress", "sub": "4"},

                    {"key": "edi_b1_ppress_out", "label": "B) EDI B-1 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_b_ppress_out", "sub": "1"},
                    {"key": "edi_b2_ppress_out", "label": "B) EDI B-2 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_b_ppress_out", "sub": "2"},
                    {"key": "edi_b3_ppress_out", "label": "B) EDI B-3 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_b_ppress_out", "sub": "3"},
                    {"key": "edi_b4_ppress_out", "label": "B) EDI B-4 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_b_ppress_out", "sub": "4"},

                    {"key": "edi_b1_bpress_out", "label": "B) EDI B-1 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_b_bpress_out", "sub": "1"},
                    {"key": "edi_b2_bpress_out", "label": "B) EDI B-2 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_b_bpress_out", "sub": "2"},
                    {"key": "edi_b3_bpress_out", "label": "B) EDI B-3 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_b_bpress_out", "sub": "3"},
                    {"key": "edi_b4_bpress_out", "label": "B) EDI B-4 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_b_bpress_out", "sub": "4"},

                    {"key": "edi_b1_amp", "label": "B) EDI B-1 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "d_edi_b_amp", "sub": "1"},
                    {"key": "edi_b2_amp", "label": "B) EDI B-2 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "d_edi_b_amp", "sub": "2"},
                    {"key": "edi_b3_amp", "label": "B) EDI B-2 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "d_edi_b_amp", "sub": "3"},
                    {"key": "edi_b4_amp", "label": "B) EDI B-2 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "d_edi_b_amp", "sub": "4"},

                    {"key": "edi_b1_volt", "label": "B) EDI B-1 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "d_edi_b_volt", "sub": "1"},
                    {"key": "edi_b2_volt", "label": "B) EDI B-2 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "d_edi_b_volt", "sub": "2"},
                    {"key": "edi_b3_volt", "label": "B) EDI B-3 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "d_edi_b_volt", "sub": "3"},
                    {"key": "edi_b4_volt", "label": "B) EDI B-4 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "d_edi_b_volt", "sub": "4"},

                    {"key": "edi_b_pflow", "label": "B) EDI 생산수 유량", "unit": "m³/hr", "range": "30~45"},
                    {"key": "edi_b_pcond", "label": "B) EDI 생산수 전도도", "unit": "MΩ·cm", "range": "15~18"}
                ]
            },
            {
                "title": "EDI \"C\"",
                "fields": [
                    {"key": "edi_c_fpump_a", "label": "C) EDI FEED PUMP 압력 A", "unit": "Kg/Cm²", "range": "3~8", "group": "d_edi_c_fpump", "sub": "A"},
                    {"key": "edi_c_fpump_b", "label": "C) EDI FEED PUMP 압력 B", "unit": "Kg/Cm²", "range": "3~8", "group": "d_edi_c_fpump", "sub": "B"},

                    {"key": "edi_c1_fflow", "label": "C) EDI C-1 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_c_fflow", "sub": "1"},
                    {"key": "edi_c2_fflow", "label": "C) EDI C-2 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_c_fflow", "sub": "2"},
                    {"key": "edi_c3_fflow", "label": "C) EDI C-3 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_c_fflow", "sub": "3"},
                    {"key": "edi_c4_fflow", "label": "C) EDI C-4 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_c_fflow", "sub": "4"},

                    {"key": "edi_c1_bflow", "label": "C) EDI C-1 농축수 유량", "unit": "m³/hr", "range": "0.5~3.5", "group": "d_edi_c_bflow", "sub": "1"},
                    {"key": "edi_c2_bflow", "label": "C) EDI C-2 농축수 유량", "unit": "m³/hr", "range": "0.5~3.5", "group": "d_edi_c_bflow", "sub": "2"},
                    {"key": "edi_c3_bflow", "label": "C) EDI C-3 농축수 유량", "unit": "m³/hr", "range": "0.5~3.5", "group": "d_edi_c_bflow", "sub": "3"},
                    {"key": "edi_c4_bflow", "label": "C) EDI C-4 농축수 유량", "unit": "m³/hr", "range": "0.5~3.5", "group": "d_edi_c_bflow", "sub": "4"},

                    {"key": "edi_c1_inpress", "label": "C) EDI C-1 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "d_edi_c_inpress", "sub": "1"},
                    {"key": "edi_c2_inpress", "label": "C) EDI C-2 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "d_edi_c_inpress", "sub": "2"},
                    {"key": "edi_c3_inpress", "label": "C) EDI C-3 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "d_edi_c_inpress", "sub": "3"},
                    {"key": "edi_c4_inpress", "label": "C) EDI C-4 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "d_edi_c_inpress", "sub": "4"},

                    {"key": "edi_c1_bpress", "label": "C) EDI C-1 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "d_edi_c_bpress", "sub": "1"},
                    {"key": "edi_c2_bpress", "label": "C) EDI C-2 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "d_edi_c_bpress", "sub": "2"},
                    {"key": "edi_c3_bpress", "label": "C) EDI C-3 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "d_edi_c_bpress", "sub": "3"},
                    {"key": "edi_c4_bpress", "label": "C) EDI C-4 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "d_edi_c_bpress", "sub": "4"},

                    {"key": "edi_c1_ppress_out", "label": "C) EDI C-1 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_c_ppress_out", "sub": "1"},
                    {"key": "edi_c2_ppress_out", "label": "C) EDI C-2 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_c_ppress_out", "sub": "2"},
                    {"key": "edi_c3_ppress_out", "label": "C) EDI C-3 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_c_ppress_out", "sub": "3"},
                    {"key": "edi_c4_ppress_out", "label": "C) EDI C-4 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_c_ppress_out", "sub": "4"},

                    {"key": "edi_c1_bpress_out", "label": "C) EDI C-1 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_c_bpress_out", "sub": "1"},
                    {"key": "edi_c2_bpress_out", "label": "C) EDI C-2 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_c_bpress_out", "sub": "2"},
                    {"key": "edi_c3_bpress_out", "label": "C) EDI C-3 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_c_bpress_out", "sub": "3"},
                    {"key": "edi_c4_bpress_out", "label": "C) EDI C-4 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "d_edi_c_bpress_out", "sub": "4"},

                    {"key": "edi_c1_amp", "label": "C) EDI C-1 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "d_edi_c_amp", "sub": "1"},
                    {"key": "edi_c2_amp", "label": "C) EDI C-2 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "d_edi_c_amp", "sub": "2"},
                    {"key": "edi_c3_amp", "label": "C) EDI C-4 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "d_edi_c_amp", "sub": "3"},
                    {"key": "edi_c4_amp", "label": "C) EDI C-4 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "d_edi_c_amp", "sub": "4"},

                    {"key": "edi_c1_volt", "label": "C) EDI C-1 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "d_edi_c_volt", "sub": "1"},
                    {"key": "edi_c2_volt", "label": "C) EDI C-2 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "d_edi_c_volt", "sub": "2"},
                    {"key": "edi_c3_volt", "label": "C) EDI C-3 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "d_edi_c_volt", "sub": "3"},
                    {"key": "edi_c4_volt", "label": "C) EDI C-4 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "d_edi_c_volt", "sub": "4"},

                    {"key": "edi_c_pflow", "label": "C) EDI 생산수 유량", "unit": "m³/hr", "range": "30~45"},
                    {"key": "edi_c_pcond", "label": "C) EDI 생산수 전도도", "unit": "MΩ·cm", "range": "15~18"}
                ]
            },
            {
                "title": "DI / M/B POLISHER",
                "fields": [
                    {"key": "di_feed_pump_press", "label": "DI FEED PUMP 압력", "unit": "Kg/Cm²", "range": "3~7"},
                    {"key": "di_supply_temp", "label": "DI 공급수 온도", "unit": "°C", "range": "23~27"},
                    {"key": "di_polisher_purity", "label": "DI M/B POLISHER 전단 순도", "unit": "MΩ·cm", "range": "10~20"},
                    
                    {"key": "di_resin_trap_press_front", "label": "DI RESIN TRAP 압력 (전단)", "unit": "Kg/Cm²", "range": "2~5", "group": "d_resin_trap", "sub": "전단"},
                    {"key": "di_resin_trap_press_rear", "label": "DI RESIN TRAP 압력 (후단)", "unit": "Kg/Cm²", "range": "2~5", "group": "d_resin_trap", "sub": "후단"},
                    
                    {"key": "di_supply_press", "label": "DI 공급 압력", "unit": "Kg/Cm²", "range": "2~5"},
                    {"key": "di_supply_flow", "label": "DI 공급 유량", "unit": "m³/hr", "range": "40~100"},
                    {"key": "di_supply_purity", "label": "DI 공급 순도", "unit": "MΩ·cm", "range": "10~20"}
                ]
            }
        ]
    },
    "PS_3F": {
        "name": "PS 3F",
        "sections": [
            {
                "title": "PS 3F RO 점검 항목",
                "fields": [
                    {"key": "supply_press", "label": "R/O 공급 압력", "unit": "Kg/Cm²", "range": "4~7"},
                    {"key": "inlet_flow", "label": "1차 R/O 인입수 유량", "unit": "m³/hr", "range": "30~60"},
                    {"key": "hp_pump_press", "label": "1차 R/O 고압 펌프 압력", "unit": "Kg/Cm²", "range": "13~18"},
                    {"key": "feed_press", "label": "1차 RO FEED 압력", "unit": "Kg/Cm²", "range": "7~15"},
                    {"key": "brine_1st_press", "label": "1차 RO 1st 농축수 압력", "unit": "Kg/Cm²", "range": "5~10"},
                    {"key": "brine_2nd_press", "label": "1차 RO 2nd 농축수 압력", "unit": "Kg/Cm²", "range": "5~10"},
                    {"key": "unit_diff_press", "label": "1차 RO UNIT 차압", "unit": "Kg/Cm²", "range": "0~5"},
                    {"key": "prod_press", "label": "1차 RO 생산수 압력", "unit": "Kg/Cm²", "range": "0~3"},
                    {"key": "prod_flow", "label": "1차 RO 생산수 유량", "unit": "m³/hr", "range": "30~60"},
                    {"key": "brine_flow", "label": "1차 RO 농축수 유량", "unit": "m³/hr", "range": "8~15"},
                    {"key": "inlet_cond", "label": "1차 RO 인입수 전도도", "unit": "uS/cm", "range": "20이하"},
                    {"key": "prod_cond", "label": "1차 RO 생산수 전도도", "unit": "uS/cm", "range": "10이하"},
                    {"key": "feed_temp", "label": "R/O Feed Temperature", "unit": "°C", "range": "23~25"}
                ]
            }
        ]
    },
    "E_DONG": {
        "name": "E동",
        "sections": [
            {
                "title": "1차 R/O (RO A, B, C - 3중 2가동)",
                "fields": [
                    {"key": "ro_feed_pump_press_a", "label": "R/O FEED PUMP 압력 A", "unit": "Kg/Cm²", "range": "3~6", "group": "e_ro1_fpump", "sub": "A"},
                    {"key": "ro_feed_pump_press_b", "label": "R/O FEED PUMP 압력 B", "unit": "Kg/Cm²", "range": "3~6", "group": "e_ro1_fpump", "sub": "B"},
                    {"key": "ro_feed_pump_press_c", "label": "R/O FEED PUMP 압력 C", "unit": "Kg/Cm²", "range": "3~6", "group": "e_ro1_fpump", "sub": "C"},

                    {"key": "ro_hp_pump_press_a", "label": "1차 R/O 고압 펌프 압력 A", "unit": "Kg/Cm²", "range": "10~15", "group": "e_ro1_hppump", "sub": "A"},
                    {"key": "ro_hp_pump_press_b", "label": "1차 R/O 고압 펌프 압력 B", "unit": "Kg/Cm²", "range": "10~15", "group": "e_ro1_hppump", "sub": "B"},
                    {"key": "ro_hp_pump_press_c", "label": "1차 R/O 고압 펌프 압력 C", "unit": "Kg/Cm²", "range": "10~15", "group": "e_ro1_hppump", "sub": "C"},

                    {"key": "ro_fpress_a", "label": "1차 RO FEED 압력 A", "unit": "Kg/Cm²", "range": "5~12", "group": "e_ro1_fpress", "sub": "A"},
                    {"key": "ro_fpress_b", "label": "1차 RO FEED 압력 B", "unit": "Kg/Cm²", "range": "5~12", "group": "e_ro1_fpress", "sub": "B"},
                    {"key": "ro_fpress_c", "label": "1차 RO FEED 압력 C", "unit": "Kg/Cm²", "range": "5~12", "group": "e_ro1_fpress", "sub": "C"},

                    {"key": "ro_b1press_a", "label": "1차 RO 1st 농축수 압력 A", "unit": "Kg/Cm²", "range": "5~10", "group": "e_ro1_b1press", "sub": "A"},
                    {"key": "ro_b1press_b", "label": "1차 RO 1st 농축수 압력 B", "unit": "Kg/Cm²", "range": "5~10", "group": "e_ro1_b1press", "sub": "B"},
                    {"key": "ro_b1press_c", "label": "1차 RO 1st 농축수 압력 C", "unit": "Kg/Cm²", "range": "5~10", "group": "e_ro1_b1press", "sub": "C"},

                    {"key": "ro_b2press_a", "label": "1차 RO 2nd 농축수 압력 A", "unit": "Kg/Cm²", "range": "5~10", "group": "e_ro1_b2press", "sub": "A"},
                    {"key": "ro_b2press_b", "label": "1차 RO 2nd 농축수 압력 B", "unit": "Kg/Cm²", "range": "5~10", "group": "e_ro1_b2press", "sub": "B"},
                    {"key": "ro_b2press_c", "label": "1차 RO 2nd 농축수 압력 C", "unit": "Kg/Cm²", "range": "5~10", "group": "e_ro1_b2press", "sub": "C"},

                    {"key": "ro_udiff_a", "label": "1차 RO UNIT 차압 A", "unit": "Kg/Cm²", "range": "0~5", "group": "e_ro1_udiff", "sub": "A"},
                    {"key": "ro_udiff_b", "label": "1차 RO UNIT 차압 B", "unit": "Kg/Cm²", "range": "0~5", "group": "e_ro1_udiff", "sub": "B"},
                    {"key": "ro_udiff_c", "label": "1차 RO UNIT 차압 C", "unit": "Kg/Cm²", "range": "0~5", "group": "e_ro1_udiff", "sub": "C"},

                    {"key": "ro_ppress_a", "label": "1차 RO 생산수 압력 A", "unit": "Kg/Cm²", "range": "0~3", "group": "e_ro1_ppress", "sub": "A"},
                    {"key": "ro_ppress_b", "label": "1차 RO 생산수 압력 B", "unit": "Kg/Cm²", "range": "0~3", "group": "e_ro1_ppress", "sub": "B"},
                    {"key": "ro_ppress_c", "label": "1차 RO 생산수 압력 C", "unit": "Kg/Cm²", "range": "0~3", "group": "e_ro1_ppress", "sub": "C"},

                    {"key": "ro_inflow_a", "label": "1차 RO 인입 유량 A", "unit": "m³/hr", "range": "60~80", "group": "e_ro1_inflow", "sub": "A"},
                    {"key": "ro_inflow_b", "label": "1차 RO 인입 유량 B", "unit": "m³/hr", "range": "60~80", "group": "e_ro1_inflow", "sub": "B"},
                    {"key": "ro_inflow_c", "label": "1차 RO 인입 유량 C", "unit": "m³/hr", "range": "60~80", "group": "e_ro1_inflow", "sub": "C"},

                    {"key": "ro_prod_flow_a", "label": "1차 RO 생산수 유량 A", "unit": "m³/hr", "range": "50~70", "group": "e_ro1_pflow", "sub": "A"},
                    {"key": "ro_prod_flow_b", "label": "1차 RO 생산수 유량 B", "unit": "m³/hr", "range": "50~70", "group": "e_ro1_pflow", "sub": "B"},
                    {"key": "ro_prod_flow_c", "label": "1차 RO 생산수 유량 C", "unit": "m³/hr", "range": "50~70", "group": "e_ro1_pflow", "sub": "C"},

                    {"key": "ro_bflow_a", "label": "1차 RO 농축수 유량 A", "unit": "m³/hr", "range": "10~20", "group": "e_ro1_bflow", "sub": "A"},
                    {"key": "ro_bflow_b", "label": "1차 RO 농축수 유량 B", "unit": "m³/hr", "range": "10~20", "group": "e_ro1_bflow", "sub": "B"},
                    {"key": "ro_bflow_c", "label": "1차 RO 농축수 유량 C", "unit": "m³/hr", "range": "10~20", "group": "e_ro1_bflow", "sub": "C"},

                    {"key": "ro_inlet_cond", "label": "1차 RO 인입수 전도도", "unit": "uS/cm", "range": "30이하"},

                    {"key": "ro_pcond_a", "label": "1차 RO 생산수 전도도 A", "unit": "uS/cm", "range": "10이하", "group": "e_ro1_pcond", "sub": "A"},
                    {"key": "ro_pcond_b", "label": "1차 RO 생산수 전도도 B", "unit": "uS/cm", "range": "10이하", "group": "e_ro1_pcond", "sub": "B"},
                    {"key": "ro_pcond_c", "label": "1차 RO 생산수 전도도 C", "unit": "uS/cm", "range": "10이하", "group": "e_ro1_pcond", "sub": "C"},

                    {"key": "ro_ftemp_a", "label": "R/O Feed Temperature A", "unit": "°C", "range": "22~25", "group": "e_ro1_ftemp", "sub": "A"},
                    {"key": "ro_ftemp_b", "label": "R/O Feed Temperature B", "unit": "°C", "range": "22~25", "group": "e_ro1_ftemp", "sub": "B"},
                    {"key": "ro_ftemp_c", "label": "R/O Feed Temperature C", "unit": "°C", "range": "22~25", "group": "e_ro1_ftemp", "sub": "C"}
                ]
            },
            {
                "title": "2차 R/O (고압 펌프 A/B)",
                "fields": [
                    {"key": "ro_2nd_hp_pump_press_a", "label": "2차 R/O 고압 펌프 압력 A", "unit": "Kg/Cm²", "range": "7~12", "group": "e_ro2_hppump", "sub": "A"},
                    {"key": "ro_2nd_hp_pump_press_b", "label": "2차 R/O 고압 펌프 압력 B", "unit": "Kg/Cm²", "range": "7~12", "group": "e_ro2_hppump", "sub": "B"},
                    {"key": "ro_2nd_feed_press", "label": "2차 R/O FEED 압력", "unit": "Kg/Cm²", "range": "7~12"},
                    {"key": "ro_2nd_brine_1st_press", "label": "2차 R/O 1st 농축수 압력", "unit": "Kg/Cm²", "range": "7~12"},
                    {"key": "ro_2nd_brine_2nd_press", "label": "2차 R/O 2nd 농축수 압력", "unit": "Kg/Cm²", "range": "7~12"},
                    {"key": "ro_2nd_unit_diff_press", "label": "2차 R/O UNIT 차압", "unit": "Kg/Cm²", "range": "0~5"},
                    {"key": "ro_2nd_prod_press", "label": "2차 R/O 생산수 압력", "unit": "Kg/Cm²", "range": "0~2"},
                    {"key": "ro_2nd_inlet_flow", "label": "2차 R/O 인입수 유량", "unit": "m³/hr", "range": "80~120"},
                    {"key": "ro_2nd_prod_flow", "label": "2차 R/O 생산수 유량", "unit": "m³/hr", "range": "80~100"},
                    {"key": "ro_2nd_brine_flow", "label": "2차 R/O 농축수 유량", "unit": "m³/hr", "range": "8~12"},
                    {"key": "ro_2nd_prod_cond", "label": "2차 R/O 생산수 전도도", "unit": "uS/cm", "range": "0~5"}
                ]
            },
            {
                "title": "EDI \"A\"",
                "fields": [
                    {"key": "edi_a_fpump_a", "label": "A/B) EDI FEED PUMP 압력 A", "unit": "Kg/Cm²", "range": "3~8", "group": "e_edi_fpump", "sub": "A"},
                    {"key": "edi_a_fpump_b", "label": "A/B) EDI FEED PUMP 압력 B", "unit": "Kg/Cm²", "range": "3~8", "group": "e_edi_fpump", "sub": "B"},
                    {"key": "edi_a_mdg_air", "label": "A) MDG A AIR 공급압력", "unit": "m³/hr", "range": "30"},

                    {"key": "edi_a1_pflow", "label": "A) EDI A-1 생산수 IN 유량", "unit": "m³/hr", "range": "9~12", "group": "e_edi_a_pflow", "sub": "1"},
                    {"key": "edi_a2_pflow", "label": "A) EDI A-2 생산수 IN 유량", "unit": "m³/hr", "range": "9~12", "group": "e_edi_a_pflow", "sub": "2"},
                    {"key": "edi_a3_pflow", "label": "A) EDI A-3 생산수 IN 유량", "unit": "m³/hr", "range": "9~12", "group": "e_edi_a_pflow", "sub": "3"},
                    {"key": "edi_a4_pflow", "label": "A) EDI A-4 생산수 IN 유량", "unit": "m³/hr", "range": "9~12", "group": "e_edi_a_pflow", "sub": "4"},

                    {"key": "edi_a1_bflow_in", "label": "A) EDI A-1 농축수 IN 유량", "unit": "m³/hr", "range": "1~2", "group": "e_edi_a_bflow_in", "sub": "1"},
                    {"key": "edi_a2_bflow_in", "label": "A) EDI A-2 농축수 IN 유량", "unit": "m³/hr", "range": "1~2", "group": "e_edi_a_bflow_in", "sub": "2"},
                    {"key": "edi_a3_bflow_in", "label": "A) EDI A-3 농축수 IN 유량", "unit": "m³/hr", "range": "1~2", "group": "e_edi_a_bflow_in", "sub": "3"},
                    {"key": "edi_a4_bflow_in", "label": "A) EDI A-4 농축수 IN 유량", "unit": "m³/hr", "range": "1~2", "group": "e_edi_a_bflow_in", "sub": "4"},

                    {"key": "edi_a1_spress", "label": "A) EDI A-1 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "e_edi_a_spress", "sub": "1"},
                    {"key": "edi_a2_spress", "label": "A) EDI A-2 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "e_edi_a_spress", "sub": "2"},
                    {"key": "edi_a3_spress", "label": "A) EDI A-3 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "e_edi_a_spress", "sub": "3"},
                    {"key": "edi_a4_spress", "label": "A) EDI A-4 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "e_edi_a_spress", "sub": "4"},

                    {"key": "edi_a1_bpress", "label": "A) EDI A-1 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "e_edi_a_bpress", "sub": "1"},
                    {"key": "edi_a2_bpress", "label": "A) EDI A-2 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "e_edi_a_bpress", "sub": "2"},
                    {"key": "edi_a3_bpress", "label": "A) EDI A-3 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "e_edi_a_bpress", "sub": "3"},
                    {"key": "edi_a4_bpress", "label": "A) EDI A-4 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "e_edi_a_bpress", "sub": "4"},

                    {"key": "edi_a1_ppress_out", "label": "A) EDI A-1 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "e_edi_a_ppress_out", "sub": "1"},
                    {"key": "edi_a2_ppress_out", "label": "A) EDI A-2 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "e_edi_a_ppress_out", "sub": "2"},
                    {"key": "edi_a3_ppress_out", "label": "A) EDI A-3 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "e_edi_a_ppress_out", "sub": "3"},
                    {"key": "edi_a4_ppress_out", "label": "A) EDI A-4 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "e_edi_a_ppress_out", "sub": "4"},

                    {"key": "edi_a1_bpress_out", "label": "A) EDI A-1 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "e_edi_a_bpress_out", "sub": "1"},
                    {"key": "edi_a2_bpress_out", "label": "A) EDI A-2 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "e_edi_a_bpress_out", "sub": "2"},
                    {"key": "edi_a3_bpress_out", "label": "A) EDI A-3 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "e_edi_a_bpress_out", "sub": "3"},
                    {"key": "edi_a4_bpress_out", "label": "A) EDI A-4 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "e_edi_a_bpress_out", "sub": "4"},

                    {"key": "edi_a1_amp", "label": "A) EDI A-1 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "e_edi_a_amp", "sub": "1"},
                    {"key": "edi_a2_amp", "label": "A) EDI A-2 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "e_edi_a_amp", "sub": "2"},
                    {"key": "edi_a3_amp", "label": "A) EDI A-3 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "e_edi_a_amp", "sub": "3"},
                    {"key": "edi_a4_amp", "label": "A) EDI A-4 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "e_edi_a_amp", "sub": "4"},

                    {"key": "edi_a1_volt", "label": "A) EDI A-1 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "e_edi_a_volt", "sub": "1"},
                    {"key": "edi_a2_volt", "label": "A) EDI A-2 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "e_edi_a_volt", "sub": "2"},
                    {"key": "edi_a3_volt", "label": "A) EDI A-3 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "e_edi_a_volt", "sub": "3"},
                    {"key": "edi_a4_volt", "label": "A) EDI A-4 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "e_edi_a_volt", "sub": "4"},

                    {"key": "edi_a_total_pflow", "label": "A) EDI 생산수 유량", "unit": "m³/hr", "range": "30~50"},
                    {"key": "edi_a_total_bflow", "label": "A) EDI 농축수 유량", "unit": "m³/hr", "range": "5~10"},
                    {"key": "edi_a_total_pcond", "label": "A) EDI 생산수 전도도", "unit": "MΩ·cm", "range": "10~18"}
                ]
            },
            {
                "title": "EDI \"B\"",
                "fields": [
                    {"key": "edi_b_mdg_air", "label": "B) MDG B AIR 공급압력", "unit": "m³/hr", "range": "30"},

                    {"key": "edi_b1_pflow", "label": "B) EDI B-1 생산수 IN 유량", "unit": "m³/hr", "range": "9~12", "group": "e_edi_b_pflow", "sub": "1"},
                    {"key": "edi_b2_pflow", "label": "B) EDI B-2 생산수 IN 유량", "unit": "m³/hr", "range": "9~12", "group": "e_edi_b_pflow", "sub": "2"},
                    {"key": "edi_b3_pflow", "label": "B) EDI B-3 생산수 IN 유량", "unit": "m³/hr", "range": "9~12", "group": "e_edi_b_pflow", "sub": "3"},
                    {"key": "edi_b4_pflow", "label": "B) EDI B-4 생산수 IN 유량", "unit": "m³/hr", "range": "9~12", "group": "e_edi_b_pflow", "sub": "4"},

                    {"key": "edi_b1_bflow_in", "label": "B) EDI B-1 농축수 IN 유량", "unit": "m³/hr", "range": "1~2", "group": "e_edi_b_bflow_in", "sub": "1"},
                    {"key": "edi_b2_bflow_in", "label": "B) EDI B-2 농축수 IN 유량", "unit": "m³/hr", "range": "1~2", "group": "e_edi_b_bflow_in", "sub": "2"},
                    {"key": "edi_b3_bflow_in", "label": "B) EDI B-3 농축수 IN 유량", "unit": "m³/hr", "range": "1~2", "group": "e_edi_b_bflow_in", "sub": "3"},
                    {"key": "edi_b4_bflow_in", "label": "B) EDI B-4 농축수 IN 유량", "unit": "m³/hr", "range": "1~2", "group": "e_edi_b_bflow_in", "sub": "4"},

                    {"key": "edi_b1_spress", "label": "B) EDI B-1 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "e_edi_b_spress", "sub": "1"},
                    {"key": "edi_b2_spress", "label": "B) EDI B-2 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "e_edi_b_spress", "sub": "2"},
                    {"key": "edi_b3_spress", "label": "B) EDI B-3 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "e_edi_b_spress", "sub": "3"},
                    {"key": "edi_b4_spress", "label": "B) EDI B-4 공급 압력", "unit": "Kg/Cm²", "range": "0.5~3.5", "group": "e_edi_b_spress", "sub": "4"},

                    {"key": "edi_b1_bpress", "label": "B) EDI B-1 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "e_edi_b_bpress", "sub": "1"},
                    {"key": "edi_b2_bpress", "label": "B) EDI B-2 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "e_edi_b_bpress", "sub": "2"},
                    {"key": "edi_b3_bpress", "label": "B) EDI B-3 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "e_edi_b_bpress", "sub": "3"},
                    {"key": "edi_b4_bpress", "label": "B) EDI B-4 농축수 압력", "unit": "Kg/Cm²", "range": "0.5~2.0", "group": "e_edi_b_bpress", "sub": "4"},

                    {"key": "edi_b1_ppress_out", "label": "B) EDI B-1 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "e_edi_b_ppress_out", "sub": "1"},
                    {"key": "edi_b2_ppress_out", "label": "B) EDI B-2 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "e_edi_b_ppress_out", "sub": "2"},
                    {"key": "edi_b3_ppress_out", "label": "B) EDI B-3 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "e_edi_b_ppress_out", "sub": "3"},
                    {"key": "edi_b4_ppress_out", "label": "B) EDI B-4 생산수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "e_edi_b_ppress_out", "sub": "4"},

                    {"key": "edi_b1_bpress_out", "label": "B) EDI B-1 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "e_edi_b_bpress_out", "sub": "1"},
                    {"key": "edi_b2_bpress_out", "label": "B) EDI B-2 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "e_edi_b_bpress_out", "sub": "2"},
                    {"key": "edi_b3_bpress_out", "label": "B) EDI B-3 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "e_edi_b_bpress_out", "sub": "3"},
                    {"key": "edi_b4_bpress_out", "label": "B) EDI B-4 농축수 토출압력", "unit": "Kg/Cm²", "range": "0~2", "group": "e_edi_b_bpress_out", "sub": "4"},

                    {"key": "edi_b1_amp", "label": "B) EDI B-1 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "e_edi_b_amp", "sub": "1"},
                    {"key": "edi_b2_amp", "label": "B) EDI B-2 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "e_edi_b_amp", "sub": "2"},
                    {"key": "edi_b3_amp", "label": "B) EDI B-2 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "e_edi_b_amp", "sub": "3"},
                    {"key": "edi_b4_amp", "label": "B) EDI B-2 MODULE AMP", "unit": "AMP", "range": "2~10", "group": "e_edi_b_amp", "sub": "4"},

                    {"key": "edi_b1_volt", "label": "B) EDI B-1 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "e_edi_b_volt", "sub": "1"},
                    {"key": "edi_b2_volt", "label": "B) EDI B-2 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "e_edi_b_volt", "sub": "2"},
                    {"key": "edi_b3_volt", "label": "B) EDI B-3 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "e_edi_b_volt", "sub": "3"},
                    {"key": "edi_b4_volt", "label": "B) EDI B-4 MODULE VOLT", "unit": "VOLT", "range": "20~250", "group": "e_edi_b_volt", "sub": "4"},

                    {"key": "edi_b_total_pflow", "label": "B) EDI 생산수 유량", "unit": "m³/hr", "range": "30~50"},
                    {"key": "edi_b_total_bflow", "label": "B) EDI 농축수 유량", "unit": "m³/hr", "range": "5~10"},
                    {"key": "edi_b_total_pcond", "label": "B) EDI 생산수 전도도", "unit": "MΩ·cm", "range": "10~18"}
                ]
            },
            {
                "title": "DI / M/B POLISHER",
                "fields": [
                    {"key": "di_feed_pump_press", "label": "DI FEED PUMP 압력", "unit": "Kg/Cm²", "range": "3~7"},
                    {"key": "di_supply_temp", "label": "DI 공급수 온도", "unit": "°C", "range": "22~27"},
                    {"key": "di_polisher_purity", "label": "DI M/B POLISHER 후단 순도", "unit": "MΩ·cm", "range": "10~18"},

                    {"key": "di_supply_press", "label": "DI 공급 압력", "unit": "Kg/Cm²", "range": "2~5", "group": "e_di_press", "sub": "공급 압력"},
                    {"key": "di_return_press", "label": "DI 리턴 압력", "unit": "Kg/Cm²", "range": "2~5", "group": "e_di_press", "sub": "리턴 압력"},

                    {"key": "di_supply_flow", "label": "DI 공급 유량", "unit": "m³/hr", "range": "0~50", "group": "e_di_flow", "sub": "공급 유량"},
                    {"key": "di_return_flow", "label": "DI 리턴 유량", "unit": "m³/hr", "range": "0~50", "group": "e_di_flow", "sub": "리턴 유량"},

                    {"key": "di_supply_purity", "label": "DI 공급 순도", "unit": "MΩ·cm", "range": "10~18", "group": "e_di_purity", "sub": "공급 순도"},
                    {"key": "di_return_purity", "label": "DI 리턴 순도", "unit": "MΩ·cm", "range": "10~18", "group": "e_di_purity", "sub": "리턴 순도"}
                ]
            }
        ]
    }
}

# Authentication API
@app.post("/api/login")
def login(payload: LoginRequest):
    if payload.user_id == "1234" and payload.password == "5678":
        token = database.create_session("1234")
        return {"token": token, "message": "Login successful"}
    raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

@app.get("/api/verify")
def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")
    token = authorization.replace("Bearer ", "").strip()
    if database.verify_session(token):
        return {"status": "ok", "user": "1234"}
    raise HTTPException(status_code=401, detail="Invalid token")

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
    filename = f"RO_EDI_Inspection_Logs_{building_code or 'ALL'}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
