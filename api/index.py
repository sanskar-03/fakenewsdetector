import os
import sys

# Add the project root to the sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.app import app
