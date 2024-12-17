import importlib
import inspect
from pathlib import Path

import pytest

from torah_dl.core.models import Extractor


def get_all_the_tests(only_valid: bool = False) -> list[pytest.param]:
    extractors_path = Path(__file__).parent.parent.parent / "src" / "torah_dl" / "core" / "extractors"
    tests: list[pytest.param] = []

    for file in extractors_path.glob("*.py"):
        if file.stem in ["__init__", "base"]:
            continue

        module_path = f"torah_dl.core.extractors.{file.stem}"
        module = importlib.import_module(module_path)

        for _, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, Extractor) and obj != Extractor:
                for ex in obj.EXAMPLES:
                    if only_valid and not ex.valid:
                        continue
                    tests.append(
                        pytest.param(
                            obj(),
                            ex.url,
                            ex.download_url,
                            ex.title,
                            ex.file_format,
                            ex.valid,
                            id=f"{obj.__name__}.{ex.name}",
                        )
                    )
    return tests
