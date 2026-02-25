from dotenv import dotenv_values
import os

try:
    # Read existing values
    config = dotenv_values(".env")
    
    new_lines = []
    
    # Check for keys and clean them
    open_router_val = None
    
    for k, v in config.items():
        if k:
            clean_k = k.replace('\ufeff', '').strip()
            if clean_k.upper() == 'OPEN_ROUTER' or clean_k == 'open_router':
                open_router_val = v
            # Preservation of other keys? 
            # We better just act on the file content directly to be safe about preserving everything else exactly.
            
    # Direct file manipulation is safer to avoid dropping things dotenv doesn't parse well or comments.
    with open(".env", "r", encoding="utf-8-sig") as f: # utf-8-sig handles BOM
        lines = f.readlines()
        
    with open(".env", "w", encoding="utf-8") as f:
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                if key == "OPEN_ROUTER":
                    key = "open_router"
                f.write(f"{key}={val}\n")
            else:
                f.write(f"{line}\n")
                
    print("Fixed .env file key names and encoding.")

except Exception as e:
    print(f"Error: {e}")
