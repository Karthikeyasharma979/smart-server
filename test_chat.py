import os
import sys
from dotenv import load_dotenv

# Ensure the parent directory is in sys.path to import utils
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), ".")))

from utils.GenerativeAI import chat

load_dotenv()

def test_chat():
    text = "Artificial Intelligence is significantly transforming various industries by enhancing efficiency and enabling data-driven decision-making. Its impact continues to grow across sectors such as healthcare, education, and finance."
    tone = "friendly"
    print(f"Testing Chat with tone: {tone}")
    try:
        result = chat(text, tone)
        print(f"Result:\n{result}")
    except Exception as e:
        print(f"Chat failed with error: {e}")

if __name__ == "__main__":
    test_chat()
