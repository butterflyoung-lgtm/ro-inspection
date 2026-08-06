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

app = FastAPI(title="RO/EDI 순수 운영점검일지 통합 관리 API", version="2.5.0")

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

# Building Schemas with Clean Labels (No confusing "A 압력" labels!)
BUILDING_SCHEMAS = {
    "B_DONG": {
        "name": "B동",
        "sections": [
            {
                "title": "전처리 FEED PUMP",
                "fields": [
                    {"key": "pre_feed_pump_press", "label": "전처리 FEED PUMP 압력", "unit": "Kg/Cm²", "range": "3~6"},
                    {"key": "pre_feed_pump_flow_a", "label": "전처리 FEED PUMP 유량 A", "unit": "m³/hr", "range": "30~80", "group": "b_pre_pump", "sub": "A"},
                    {"key": "pre_feed_pump_flow_b", "label": "전처리 FEED PUMP 유량 B", "unit": "m³/hr", "range": "30~80", "group": "b_pre_pump", "sub": "B"}
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
                    
                    {"key": "ro_1st_feed_press_a", "label": "1차 RO FEED 압력 A", "unit": "Kg/Cm²", "range": "7~15", "group": "b_ro1_line", "sub": "A"},
                    {"key": "ro_1st_feed_press_b", "label": "1차 RO FEED 압력 B", "unit": "Kg/Cm²", "range": "7~15", "group": "b_ro1_line", "sub": "B"},
                    
                    {"key": "ro_1st_brine_1st_press_a", "label": "1차 RO 1st 농축수 압력 A", "unit": "Kg/Cm²", "range": "7~15", "group": "b_ro1_line", "sub": "A"},
                    {"key": "ro_1st_brine_1st_press_b", "label": "1차 RO 1st 농축수 압력 B", "unit": "Kg/Cm²", "range": "7~15", "group": "b_ro1_line", "sub": "B"},
                    
                    {"key": "ro_1st_brine_2nd_press_a", "label": "1차 RO 2nd 농축수 압력 A", "unit": "Kg/Cm²", "range": "7~15", "group": "b_ro1_line", "sub": "A"},
                    {"key": "ro_1st_brine_2nd_press_b", "label": "1차 RO 2nd 농축수 압력 B", "unit": "Kg/Cm²", "range": "7~15", "group": "b_ro1_line", "sub": "B"},
                    
                    {"key": "ro_1st_unit_diff_press_a", "label": "1차 RO UNIT 차압 A", "unit": "Kg/Cm²", "range": "0~5", "group": "b_ro1_line", "sub": "A"},
                    {"key": "ro_1st_unit_diff_press_b", "label": "1차 RO UNIT 차압 B", "unit": "Kg/Cm²", "range": "0~5", "group": "b_ro1_line", "sub": "B"},
                    
                    {"key": "ro_1st_prod_press_a", "label": "1차 RO 생산수 압력 A", "unit": "Kg/Cm²", "range": "0~1", "group": "b_ro1_line", "sub": "A"},
                    {"key": "ro_1st_prod_press_b", "label": "1차 RO 생산수 압력 B", "unit": "Kg/Cm²", "range": "0~1", "group": "b_ro1_line", "sub": "B"},
                    
                    {"key": "ro_1st_prod_flow_a", "label": "1차 RO 생산수 유량 A", "unit": "m³/hr", "range": "30~60", "group": "b_ro1_line", "sub": "A"},
                    {"key": "ro_1st_prod_flow_b", "label": "1차 RO 생산수 유량 B", "unit": "m³/hr", "range": "30~60", "group": "b_ro1_line", "sub": "B"},
                    
                    {"key": "ro_1st_brine_flow_a", "label": "1차 RO 농축수 유량 A", "unit": "m³/hr", "range": "15~155", "group": "b_ro1_line", "sub": "A"},
                    {"key": "ro_1st_brine_flow_b", "label": "1차 RO 농축수 유량 B", "unit": "m³/hr", "range": "15~155", "group": "b_ro1_line", "sub": "B"},
                    
                    {"key": "ro_1st_prod_cond_a", "label": "1차 RO 생산수 전도도 A", "unit": "uS/cm", "range": "10이하", "group": "b_ro1_line", "sub": "A"},
                    {"key": "ro_1st_prod_cond_b", "label": "1차 RO 생산수 전도도 B", "unit": "uS/cm", "range": "10이하", "group": "b_ro1_line", "sub": "B"},
                    
                    {"key": "ro_1st_feed_temp_a", "label": "R/O Feed Temperature A", "unit": "°C", "range": "23~25", "group": "b_ro1_line", "sub": "A"},
                    {"key": "ro_1st_feed_temp_b", "label": "R/O Feed Temperature B", "unit": "°C", "range": "23~25", "group": "b_ro1_line", "sub": "B"}
                ]
            },
            {
                "title": "2차 R/O",
                "fields": [
                    {"key": "ro_2nd_hp_pump_press_a", "label": "2차 R/O 고압 펌프 압력 A", "unit": "Kg/Cm²", "range": "7~12", "group": "b_ro2_hp_pump", "sub": "A"},
                    {"key": "ro_2nd_hp_pump_press_b", "label": "2차 R/O 고압 펌프 압력 B", "unit": "Kg/Cm²", "range": "7~12", "group": "b_ro2_hp_pump", "sub": "B"},
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
                "title": "EDI (2x2 / 4열 그리드)",
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
                "title": "R/O 구분 (A/B운전 - 2중 1가동)",
                "fields": [
                    {"key": "ro_status", "label": "R/O 운전 구분", "type": "select", "options": ["A운전", "B운전", "전체정지"], "unit": "", "range": "-"},
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
                "title": "1차 R/O (RO A/B/C/D 2x2 / 4열 그리드)",
                "fields": [
                    {"key": "ro_feed_pump_press_a", "label": "1차 R/O FEED PUMP 압력 A", "unit": "Kg/Cm²", "range": "4~7", "group": "d_ro1_fpump", "sub": "A"},
                    {"key": "ro_feed_pump_press_b", "label": "1차 R/O FEED PUMP 압력 B", "unit": "Kg/Cm²", "range": "4~7", "group": "d_ro1_fpump", "sub": "B"},
                    {"key": "ro_feed_pump_press_c", "label": "1차 R/O FEED PUMP 압력 C", "unit": "Kg/Cm²", "range": "4~7", "group": "d_ro1_fpump", "sub": "C"},
                    {"key": "ro_feed_pump_press_d", "label": "1차 R/O FEED PUMP 압력 D", "unit": "Kg/Cm²", "range": "4~7", "group": "d_ro1_fpump", "sub": "D"},

                    {"key": "ro_inlet_flow_a", "label": "1차 R/O 인입 유량 A", "unit": "m³/hr", "range": "30~60", "group": "d_ro1_inflow", "sub": "A"},
                    {"key": "ro_inlet_flow_b", "label": "1차 R/O 인입 유량 B", "unit": "m³/hr", "range": "30~60", "group": "d_ro1_inflow", "sub": "B"},
                    {"key": "ro_inlet_flow_c", "label": "1차 R/O 인입 유량 C", "unit": "m³/hr", "range": "30~60", "group": "d_ro1_inflow", "sub": "C"},
                    {"key": "ro_inlet_flow_d", "label": "1차 R/O 인입 유량 D", "unit": "m³/hr", "range": "30~60", "group": "d_ro1_inflow", "sub": "D"},

                    {"key": "ro_hp_pump_press_a", "label": "1차 R/O 고압 펌프 압력 A", "unit": "Kg/Cm²", "range": "13~18", "group": "d_ro1_hppump", "sub": "A"},
                    {"key": "ro_hp_pump_press_b", "label": "1차 R/O 고압 펌프 압력 B", "unit": "Kg/Cm²", "range": "13~18", "group": "d_ro1_hppump", "sub": "B"},
                    {"key": "ro_hp_pump_press_c", "label": "1차 R/O 고압 펌프 압력 C", "unit": "Kg/Cm²", "range": "13~18", "group": "d_ro1_hppump", "sub": "C"},
                    {"key": "ro_hp_pump_press_d", "label": "1차 R/O 고압 펌프 압력 D", "unit": "Kg/Cm²", "range": "13~18", "group": "d_ro1_hppump", "sub": "D"},

                    {"key": "ro_prod_flow_a", "label": "1차 R/O 생산수 유량 A", "unit": "m³/hr", "range": "30~60", "group": "d_ro1_pflow", "sub": "A"},
                    {"key": "ro_prod_flow_b", "label": "1차 R/O 생산수 유량 B", "unit": "m³/hr", "range": "30~60", "group": "d_ro1_pflow", "sub": "B"},
                    {"key": "ro_prod_flow_c", "label": "1차 R/O 생산수 유량 C", "unit": "m³/hr", "range": "30~60", "group": "d_ro1_pflow", "sub": "C"},
                    {"key": "ro_prod_flow_d", "label": "1차 R/O 생산수 유량 D", "unit": "m³/hr", "range": "30~60", "group": "d_ro1_pflow", "sub": "D"}
                ]
            },
            {
                "title": "2차 R/O (PS 1/2F용 & PS 3F용)",
                "fields": [
                    {"key": "ro_2nd_ps12_hp_pump_press_a", "label": "PS 1/2F용 2차 RO 고압 펌프 압력 A", "unit": "Kg/Cm²", "range": "7~12", "group": "d_ro2_ps12_pump", "sub": "A"},
                    {"key": "ro_2nd_ps12_hp_pump_press_b", "label": "PS 1/2F용 2차 RO 고압 펌프 압력 B", "unit": "Kg/Cm²", "range": "7~12", "group": "d_ro2_ps12_pump", "sub": "B"},
                    
                    {"key": "ro_2nd_ps3f_hp_pump_press_a", "label": "PS 3F용 2차 RO 고압 펌프 압력 A", "unit": "Kg/Cm²", "range": "7~12", "group": "d_ro2_ps3f_pump", "sub": "A"},
                    {"key": "ro_2nd_ps3f_hp_pump_press_b", "label": "PS 3F용 2차 RO 고압 펌프 압력 B", "unit": "Kg/Cm²", "range": "7~12", "group": "d_ro2_ps3f_pump", "sub": "B"},

                    {"key": "ro_2nd_ps12_prod_flow", "label": "PS 1/2F용 2차 RO 생산수 유량", "unit": "m³/hr", "range": "38~50"},
                    {"key": "ro_2nd_ps3f_prod_flow", "label": "PS 3F용 2차 RO 생산수 유량", "unit": "m³/hr", "range": "38~50"}
                ]
            },
            {
                "title": "EDI (EDI A, B, C 2x2 / 4열 그리드)",
                "fields": [
                    {"key": "edi_a_feed_pump_press_a", "label": "EDI A FEED PUMP 압력 A", "unit": "Kg/Cm²", "range": "3~8", "group": "d_edi_a_fpump", "sub": "A"},
                    {"key": "edi_a_feed_pump_press_b", "label": "EDI A FEED PUMP 압력 B", "unit": "Kg/Cm²", "range": "3~8", "group": "d_edi_a_fpump", "sub": "B"},
                    {"key": "edi_b_feed_pump_press_a", "label": "EDI B FEED PUMP 압력 A", "unit": "Kg/Cm²", "range": "3~8", "group": "d_edi_b_fpump", "sub": "A"},
                    {"key": "edi_b_feed_pump_press_b", "label": "EDI B FEED PUMP 압력 B", "unit": "Kg/Cm²", "range": "3~8", "group": "d_edi_b_fpump", "sub": "B"},
                    {"key": "edi_c_feed_pump_press_a", "label": "EDI C FEED PUMP 압력 A", "unit": "Kg/Cm²", "range": "3~8", "group": "d_edi_c_fpump", "sub": "A"},
                    {"key": "edi_c_feed_pump_press_b", "label": "EDI C FEED PUMP 압력 B", "unit": "Kg/Cm²", "range": "3~8", "group": "d_edi_c_fpump", "sub": "B"},

                    {"key": "edi_a1_flow", "label": "EDI A-1 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_a_flow", "sub": "1"},
                    {"key": "edi_a2_flow", "label": "EDI A-2 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_a_flow", "sub": "2"},
                    {"key": "edi_a3_flow", "label": "EDI A-3 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_a_flow", "sub": "3"},
                    {"key": "edi_a4_flow", "label": "EDI A-4 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_a_flow", "sub": "4"},

                    {"key": "edi_b1_flow", "label": "EDI B-1 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_b_flow", "sub": "1"},
                    {"key": "edi_b2_flow", "label": "EDI B-2 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_b_flow", "sub": "2"},
                    {"key": "edi_b3_flow", "label": "EDI B-3 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_b_flow", "sub": "3"},
                    {"key": "edi_b4_flow", "label": "EDI B-4 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_b_flow", "sub": "4"},

                    {"key": "edi_c1_flow", "label": "EDI C-1 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_c_flow", "sub": "1"},
                    {"key": "edi_c2_flow", "label": "EDI C-2 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_c_flow", "sub": "2"},
                    {"key": "edi_c3_flow", "label": "EDI C-3 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_c_flow", "sub": "3"},
                    {"key": "edi_c4_flow", "label": "EDI C-4 공급유량", "unit": "m³/hr", "range": "10~14", "group": "d_edi_c_flow", "sub": "4"},

                    {"key": "edi_total_prod_flow", "label": "EDI 생산수 유량", "unit": "m³/hr", "range": "30~45"},
                    {"key": "edi_total_prod_cond", "label": "EDI 생산수 전도도", "unit": "MΩ·cm", "range": "15~18"}
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
                    {"key": "prod_press", "label": "1차 RO 생산수 압력", "unit": "Kg/Cm²", "range": "0~2"},
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
                    {"key": "ro_feed_pump_press_a", "label": "1차 R/O FEED PUMP 압력 A", "unit": "Kg/Cm²", "range": "3~6", "group": "e_ro1_fpump", "sub": "A"},
                    {"key": "ro_feed_pump_press_b", "label": "1차 R/O FEED PUMP 압력 B", "unit": "Kg/Cm²", "range": "3~6", "group": "e_ro1_fpump", "sub": "B"},
                    {"key": "ro_feed_pump_press_c", "label": "1차 R/O FEED PUMP 압력 C", "unit": "Kg/Cm²", "range": "3~6", "group": "e_ro1_fpump", "sub": "C"},

                    {"key": "ro_hp_pump_press_a", "label": "1차 R/O 고압 펌프 압력 A", "unit": "Kg/Cm²", "range": "10~15", "group": "e_ro1_hppump", "sub": "A"},
                    {"key": "ro_hp_pump_press_b", "label": "1차 R/O 고압 펌프 압력 B", "unit": "Kg/Cm²", "range": "10~15", "group": "e_ro1_hppump", "sub": "B"},
                    {"key": "ro_hp_pump_press_c", "label": "1차 R/O 고압 펌프 압력 C", "unit": "Kg/Cm²", "range": "10~15", "group": "e_ro1_hppump", "sub": "C"},

                    {"key": "ro_prod_flow_a", "label": "1차 R/O 생산수 유량 A", "unit": "m³/hr", "range": "50~70", "group": "e_ro1_pflow", "sub": "A"},
                    {"key": "ro_prod_flow_b", "label": "1차 R/O 생산수 유량 B", "unit": "m³/hr", "range": "50~70", "group": "e_ro1_pflow", "sub": "B"},
                    {"key": "ro_prod_flow_c", "label": "1차 R/O 생산수 유량 C", "unit": "m³/hr", "range": "50~70", "group": "e_ro1_pflow", "sub": "C"}
                ]
            },
            {
                "title": "2차 R/O (고압 펌프 A/B - 2중 1가동)",
                "fields": [
                    {"key": "ro_2nd_hp_pump_press_a", "label": "2차 R/O 고압 펌프 압력 A", "unit": "Kg/Cm²", "range": "7~12", "group": "e_ro2_pump", "sub": "A"},
                    {"key": "ro_2nd_hp_pump_press_b", "label": "2차 R/O 고압 펌프 압력 B", "unit": "Kg/Cm²", "range": "7~12", "group": "e_ro2_pump", "sub": "B"},
                    {"key": "ro_2nd_prod_flow", "label": "2차 R/O 생산수 유량", "unit": "m³/hr", "range": "80~100"}
                ]
            },
            {
                "title": "EDI (EDI A, B - 2중 1가동)",
                "fields": [
                    {"key": "edi_feed_pump_press_a", "label": "EDI FEED PUMP 압력 A", "unit": "Kg/Cm²", "range": "3~8", "group": "e_edi_fpump", "sub": "A"},
                    {"key": "edi_feed_pump_press_b", "label": "EDI FEED PUMP 압력 B", "unit": "Kg/Cm²", "range": "3~8", "group": "e_edi_fpump", "sub": "B"},
                    {"key": "edi_prod_in_flow_a", "label": "EDI 생산수 IN 유량 A", "unit": "m³/hr", "range": "9~12", "group": "e_edi_pflow", "sub": "A"},
                    {"key": "edi_prod_in_flow_b", "label": "EDI 생산수 IN 유량 B", "unit": "m³/hr", "range": "9~12", "group": "e_edi_pflow", "sub": "B"},
                    {"key": "edi_prod_flow", "label": "EDI 생산수 유량", "unit": "m³/hr", "range": "30~50"},
                    {"key": "edi_prod_cond", "label": "EDI 생산수 전도도", "unit": "MΩ·cm", "range": "10~18"}
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
