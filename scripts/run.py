#!/usr/bin/env python3
"""
Run script for Binance Terminal
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

try:
    from main import main
    main()
except ImportError as e:
    print(f"Error importing main module: {e}")
    print("Please make sure you're running from the project root directory")
    sys.exit(1)
except Exception as e:
    print(f"Error running application: {e}")
    sys.exit(1)
