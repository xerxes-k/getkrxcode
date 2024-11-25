# __init__.py
from .project import *  # Import all symbols from core.py

# Optional: Define __all__ for clarity and to limit what is exported when using `from getkrxcode import *`
__all__ = [name for name in dir() if not name.startswith("_")]