from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).parent.parent
BASE_URL=os.getenv("BASE_URL")
