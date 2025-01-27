<!--contributing-start-->
# Contributing to `torah-dl`

## How to contribute

1. Fork the repository
2. Create a new branch for your changes
3. Make your changes and commit them
4. Open a pull request

## Code of Conduct

We follow the [Contributor Covenant](https://www.contributor-covenant.org/) code of conduct. Additionally, we expect everyone contributing to behave _Al Kiddush Hashem_ and not engage in any behavior that could be considered inappropriate or offensive.

## How to run the project

We use [Hermit](https://cashapp.github.io/hermit/) to manage our development environment. To get started, install Hermit with:

```bash
curl -fsSL https://github.com/cashapp/hermit/releases/download/stable/install.sh | /bin/bash
```

Hermit will automatically install and manage `uv` and `task` for you when you run any of the project commands.

Once Hermit is installed, you can install the project's dependencies by running `uv sync`.

To run the project, use `uv run pytest -vv -s --cov=torah_dl` to run the tests, or `task test` if you have [task](https://taskfile.dev/) installed.

This is foundational software, and we maintain a very high standard for code quality. Please make sure your code passes `ruff check --fix` before submitting a pull request. While code coverage is a poor metric for judging the quality of this project, we strive to maintain the existing 90%+ coverage. Additionally, our tests actually download and extract the metadata from the target sites, which means we are constantly ensuring that our tooling works as intended. Please help us maintain that level of service with your tests.
<!--contributing-end-->