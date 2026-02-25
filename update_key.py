import os

new_key = "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"
env_path = ".env"

try:
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    with open(env_path, "w", encoding="utf-8") as f:
        found = False
        for line in lines:
            if line.strip().startswith("open_router="):
                f.write(f"open_router={new_key}\n")
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f"\nopen_router={new_key}\n")
            
    print("Updated .env with new key.")
except Exception as e:
    print(f"Error updating .env: {e}")
