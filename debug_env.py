from dotenv import load_dotenv
import os

load_dotenv()
print("--- ENV DEBUG ---")
print(f"open_router from getenv: '{os.getenv('open_router')}'")
print(f"All keys: {list(os.environ.keys())}")
print("--- END DEBUG ---")
