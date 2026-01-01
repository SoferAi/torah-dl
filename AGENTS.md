# AGENTS.md

## Commands
- **Install**: `uv sync`
- **Test all**: `uv run pytest -vv -s --cov=torah_dl`
- **Test single**: `uv run pytest test/path/to_test.py::test_function -vv -s`
- **Lint**: `uv run ruff check .`
- **Format**: `uv run ruff format .`
- **Fix lint**: `uv run ruff check . --fix`

## Architecture
- Python library + CLI for downloading Torah content from various websites
- **src/torah_dl/core/**: Core library - models, extractors, download logic
- **src/torah_dl/core/extractors/**: Site-specific extractors (inherit from `Extractor` ABC)
- **src/torah_dl/cli.py**: Typer-based CLI interface
- **test/**: Tests mirror src structure (test_core/, test_cli/)

## Code Style
- Python 3.10+, Pydantic for models, uses `|` union syntax
- Ruff for linting/formatting (line-length 120, double quotes)
- Type hints required; package is `py.typed`
- New extractors: subclass `Extractor`, define `url_patterns`, `extract()`, and `EXAMPLES`
- Tests download from real sites; maintain 85%+ coverage
