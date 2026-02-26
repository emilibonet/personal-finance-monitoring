import os
import logging

from types import SimpleNamespace

colors = SimpleNamespace(
    savings="#008DEB",
    green="#5AA800",
    red="#AF0000",
    observed="#008DEB",
    forecast="#5AA800"
)

def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

def find_project_root(start_path=None):
    if start_path is None:
        start_path = os.path.dirname(os.path.abspath(__file__))
    
    current_path = start_path
    while True:
        if os.path.exists(os.path.join(current_path, '.env')):
            return current_path
        parent_path = os.path.dirname(current_path)
        if parent_path == current_path:  # Reached the root directory
            raise FileNotFoundError("No .env file found in any parent directory.")
        current_path = parent_path

ROOT_DIR = find_project_root()

## LOGGING CONFIGURATION ##

import os
import logging
from datetime import datetime

class SimpleFormatter(logging.Formatter):
    RESET = "\033[0m"
    COLOURS = {
        "DEBUG": "\033[36m",             # cyan
        "INFO": "\033[32m",              # green
        "WARNING": "\033[33m",           # yellow
        "ERROR": "\033[31m",             # red
        "CRITICAL": "\033[41m\033[97m",  # white on red
    }

    def format(self, record):
        record.asctime = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")

        colour = self.COLOURS.get(record.levelname, "")
        level = f"{colour}{record.levelname:<8}{self.RESET}"

        logger_name = f"{record.name:<15}"

        msg = record.getMessage()

        return f"{record.asctime} | {logger_name} : {level} ─ {msg}"

# Setup
handler = logging.StreamHandler()
handler.setFormatter(SimpleFormatter())

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    handlers=[handler]
)
