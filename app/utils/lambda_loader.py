from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Callable


def load_lambda_handler(
    lambda_file_path: Path,
    module_name: str,
) -> Callable:
    """
    Dynamically loads a lambda_function.py in isolation and returns lambda_handler.
    Ensures no cross-module pollution via sys.modules.
    """

    if not lambda_file_path.exists():
        raise FileNotFoundError(f"Lambda file not found: {lambda_file_path}")

    # Ensure clean module namespace
    sys.modules.pop(module_name, None)

    spec = importlib.util.spec_from_file_location(
        module_name,
        lambda_file_path,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load spec for {lambda_file_path}")

    module: ModuleType = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    if not hasattr(module, "lambda_handler"):
        raise AttributeError("lambda_handler not found in module")

    return getattr(module, "lambda_handler")
