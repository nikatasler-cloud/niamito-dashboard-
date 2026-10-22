"""Deployment entry point. appreal.py remains supported for existing hosting."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name("appreal.py")), run_name="__main__")
