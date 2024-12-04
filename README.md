<!--intro-start-->
# `torah-dl` - tools for downloading media from Torah websites.
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
![PyPI - Version](https://img.shields.io/pypi/v/torah-dl)
[![image](https://img.shields.io/pypi/pyversions/torah-dl.svg)](https://pypi.python.org/pypi/torah-dl)
[![image](https://img.shields.io/pypi/l/torah-dl.svg)](https://pypi.python.org/pypi/torah-dl)
[![Actions status](https://github.com/soferai/torah-dl/actions/workflows/workflow.yml/badge.svg)](https://github.com/soferai/torah-dl/actions)
[![Coverage Status](./docs/assets/coverage.svg)](https://soferai.github.io/torah-dl/)

## Why `torah-dl`?
Most of our generation's Torah content is locked up in websites that are not easily accessible. Sofer.Ai is building a platform to make Torah accessible to everyone, and we decided to build key parts of that platform in the open. We intend to support every website with Torah audio on our platform, and realized quickly that even finding all the sites with audio would be a full-time job. So we open-sourced `torah-dl` to make it easier for others to download Torah audio from any website, and make Torah more accessible!

## How does it work?
`torah-dl` is a library and a set of command-line tools for downloading media from Torah websites. You can use it as a command-line tool with `uvx` (preferred), `pipx`, `pip`, `poetry`, `venv`, or any Python tool installer of your choice, simply by running `uvx torah-dl`.

For those who want to integrate `torah-dl` into their Python application, you can simply install it via `uv add torah-dl` or `pip install torah-dl`. You can then use the library in your code as you would any other Python library:

```python
from torah_dl import extract

extraction = extract("https://www.yutorah.org/lectures/details?shiurid=1117416")

print(extraction.download_url)
```
## What sites does it support?
Here is the list of sites that `torah-dl` supports already, and what's coming soon:

- [x] [Yutorah](https://www.yutorah.org)
- [x] [TorahAnytime](https://www.torahanytime.com)
- [ ] [OUTorah.org](https://www.outorah.org)
- [ ] [TorahDownloads.org](https://www.torahdownloads.org)
- [ ] Help us out by adding your favorite Torah website!

## Contributing
We'd love your help! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for more information on how to get involved.

## Frequently Asked Questions
<details>

<summary>Am I allowed to download Torah audio from these websites?</summary>

### You are responsible for ensuring that you follow all Terms of Service agreements, Copyright agreements, and other legal agreements with these websites.
 TODO: get a lawyer to review this.
</details>

<details>
<summary>How do I download audio from a site that is not on the list?</summary>

### We'd love your help! Please see our [CONTRIBUTING.md](docs/CONTRIBUTING.md) for more information on how to get involved.
</details>

<details>
<summary>What are the usecases for `torah-dl`?</summary>

Allowing transcription services to make Torah more accessible 😉

Other uses include downloading Torah audio for offline listening, or for use in Torah study tools, or for training AI models to understand Torah, or for other purposes (please see question above about permissions).
</details>
<!--intro-end-->
