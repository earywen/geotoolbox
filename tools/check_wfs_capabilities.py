import requests
import xml.etree.ElementTree as ET

def check_georisques():
    url = "https://georisques.gouv.fr/services"
    print(f"Checking {url}...")
    try:
        r = requests.get(url, params={"service":"WFS", "version":"1.1.0", "request":"GetCapabilities"}, timeout=15)
        if r.status_code != 200:
            print(f"Error {r.status_code}")
            return
            
        root = ET.fromstring(r.content)
        layers = []
        for elem in root.iter():
            if 'FeatureType' in elem.tag:
                for child in elem:
                    if 'Name' in child.tag and child.text:
                        layers.append(child.text)
                        
        print(f"Found {len(layers)} layers.")
        print("\n--- ZONING LAYERS (Key: ZON, PERI, PPR, ALEA) ---")
        keywords = ["ZON", "PERI", "PPR", "ALEA"]
        for ln in layers:
            if any(k in ln.upper() for k in keywords):
                print(f" * {ln}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_georisques()
