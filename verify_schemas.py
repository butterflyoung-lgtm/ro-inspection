import urllib.request
import json

url = "http://localhost:8000/api/buildings"
try:
    res = urllib.request.urlopen(url)
    data = json.loads(res.read().decode('utf-8'))
    
    print("=== LIVE SERVER BUILDING SCHEMAS ===")
    for b_code, b_schema in data.items():
        print(f"\n[{b_code}] {b_schema['name']}")
        for sec_idx, sec in enumerate(b_schema['sections']):
            print(f"  Section {sec_idx+1}: {sec['title']} (Total fields: {len(sec['fields'])})")
            for f in sec['fields']:
                g_str = f" [group:{f['group']} sub:{f['sub']}]" if 'group' in f else ""
                print(f"    - {f['key']}: {f['label']} ({f['unit']}) range:{f['range']}{g_str}")
except Exception as e:
    print("Error connecting to server:", e)
