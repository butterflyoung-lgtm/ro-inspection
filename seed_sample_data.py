import database
from datetime import datetime, timedelta

def seed():
    database.init_db()
    logs = database.get_logs()
    if len(logs) > 0:
        return
        
    print("Seeding initial sample inspection logs for ROEDI schema...")
    
    today = datetime.now()
    
    for i in range(7, -1, -1):
        date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        
        # Seed B_DONG
        b_vals = {
            "pre_feed_pump_press": 4.5,
            "pre_feed_pump_flow_a": 55.0,
            "pre_feed_pump_flow_b": "비가동",
            "ro_1st_feed_pump_press_a": 4.2,
            "ro_1st_feed_pump_press_b": 4.1,
            "ro_1st_feed_pump_press_c": "비가동",
            "ro_1st_hp_pump_press_a": 11.5,
            "ro_1st_hp_pump_press_b": 11.8,
            "ro_1st_hp_pump_press_c": "비가동",
            "ro_1st_feed_press_a": 10.2,
            "ro_1st_feed_press_b": "비가동",
            "ro_1st_brine_1st_press_a": 9.5,
            "ro_1st_brine_1st_press_b": "비가동",
            "ro_1st_brine_2nd_press_a": 8.8,
            "ro_1st_brine_2nd_press_b": "비가동",
            "ro_1st_unit_diff_press_a": 1.4,
            "ro_1st_unit_diff_press_b": "비가동",
            "ro_1st_prod_press_a": 0.5,
            "ro_1st_prod_press_b": "비가동",
            "ro_1st_prod_flow_a": 48.0,
            "ro_1st_prod_flow_b": "비가동",
            "ro_1st_brine_flow_a": 25.0,
            "ro_1st_brine_flow_b": "비가동",
            "ro_1st_prod_cond_a": 5.2,
            "ro_1st_prod_cond_b": "비가동",
            "ro_1st_feed_temp_a": 24.1,
            "ro_1st_feed_temp_b": "비가동",
            "ro_2nd_hp_pump_press_a": 9.8,
            "ro_2nd_hp_pump_press_b": "비가동",
            "ro_2nd_feed_press": 9.2,
            "ro_2nd_brine_1st_press": 8.5,
            "ro_2nd_brine_2nd_press": 7.8,
            "ro_2nd_unit_diff_press": 1.4,
            "ro_2nd_prod_press": 0.8,
            "ro_2nd_prod_flow": 42.0,
            "ro_2nd_brine_flow": 4.1,
            "ro_2nd_prod_cond": 0.65,
            "edi_feed_pump_press_a": 4.2,
            "edi_feed_pump_press_b": "비가동",
            "edi_feed_flow_a": 11.5,
            "edi_feed_flow_b": 11.2,
            "edi_feed_flow_c": 11.8,
            "edi_feed_flow_d": 11.0,
            "edi_brine_flow_a": 0.9,
            "edi_brine_flow_b": 0.8,
            "edi_brine_flow_c": 1.0,
            "edi_brine_flow_d": 0.9,
            "edi_inlet_press_a": 2.5,
            "edi_inlet_press_b": 2.4,
            "edi_inlet_press_c": 2.6,
            "edi_inlet_press_d": 2.5,
            "edi_amp_a": 3.8,
            "edi_amp_b": 4.0,
            "edi_amp_c": 3.9,
            "edi_amp_d": 3.7,
            "edi_volt_a": 120.0,
            "edi_volt_b": 125.0,
            "edi_volt_c": 118.0,
            "edi_volt_d": 122.0,
            "edi_total_prod_flow": 32.5,
            "edi_total_prod_cond": 16.8,
            "di_feed_pump_press_a": 4.5,
            "di_feed_pump_press_b": "비가동",
            "di_supply_temp": 24.5,
            "di_polisher_purity": 17.2,
            "di_resin_trap_press_front": 1.0,
            "di_resin_trap_press_rear": 0.8,
            "uf_brine_flow": 2.0,
            "di_supply_press": 3.2,
            "di_supply_flow": 35.0,
            "di_supply_purity": 18.0
        }
        
        database.create_log("B_DONG", "", date_str, "홍길동", b_vals, "정상 가동 중")

if __name__ == "__main__":
    seed()
