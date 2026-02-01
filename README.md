# 🔍 Revibe

**Your vibe-coded project deserves a second pass. And a fix plan.**

[![PyPI version](https://badge.fury.io/py/revibe.svg)](https://badge.fury.io/py/revibe)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

Revibe scans your codebase and tells you:

- 🐛 **How many bugs** are probably hiding in your code
- 🧪 **Whether you have enough tests** (spoiler: you probably don't)
- 🤖 **Which parts smell like AI-generated code**
- 📏 **Whether your codebase is bigger than it needs to be**
- 🔗 **How complex your feature interactions are**

**Then it generates copy-paste fix instructions you can hand right back to Cursor, Claude, or your AI tool.**

---

## ⚡ Quick Start

### pip (recommended)

```bash
pip install revibe
revibe scan ./my-project
```

### npx (no install needed)

```bash
npx revibe scan ./my-project
```

### Homebrew (macOS)

```bash
brew tap webmyc/revibe
brew install revibe
revibe scan ./my-project
```

---

## 🔧 Get Fix Instructions

The real power of Revibe isn't just finding problems — it's generating **AI-ready fix instructions** you can copy-paste directly into your AI coding tool.

```bash
# Generate copy-paste prompts for your AI tool
revibe scan ./my-project --fix

# Generate Cursor rules file
revibe scan ./my-project --cursor

# Generate CLAUDE.md section
revibe scan ./my-project --claude

# Full HTML report + all fix formats
revibe scan ./my-project --all
```

### Example Output

Running `revibe scan . --fix` generates a `REVIBE_FIXES.md` file with prompts like:

```markdown
## 🔴 CRITICAL: Add Tests (you have almost none)

Your codebase has 1,234 lines of source code and only 47 lines of tests (3.8% ratio).
The recommended minimum is 80%.

### Prompt 1: Generate tests for critical paths

Analyze this codebase and generate comprehensive test files for the following
critical modules that currently have ZERO test coverage:

- src/api/payments.py (12 functions, 0 tests) — Focus on: process_payment, refund
- src/auth/login.py (5 functions, 0 tests) — Focus on: authenticate, verify_token

For each module, create a test file in tests/ that:
1. Tests happy path for each function
2. Tests edge cases (null inputs, invalid data, boundary values)
3. Tests error conditions
4. Uses pytest fixtures for shared setup

Start with src/api/payments.py as it handles money.
```

---

## 📊 What It Finds

### 8 AI Code Smell Detectors

| Smell | What It Detects |
|-------|-----------------|
| **Excessive Comments** | High ratio of comments to code (AI tends to over-explain) |
| **Verbose Naming** | Function/variable names > 35 characters |
| **Boilerplate Heavy** | Many imports relative to actual functions |
| **Inconsistent Patterns** | Mixed naming conventions (camelCase vs snake_case) |
| **Dead Code Indicators** | Same function defined in multiple files |
| **Over-engineering** | Too many classes relative to codebase size |
| **Missing Error Handling** | Functions without try/catch or error handling |
| **Copy-paste Artifacts** | Repeated string patterns across files |

### Health Metrics

- **Health Score**: 0-100 based on test coverage, code smells, duplicates, and more
- **Risk Level**: LOW, MODERATE, ELEVATED, HIGH, or CRITICAL
- **Estimated Defects**: Based on industry research (25/KLOC baseline, 1.7x for AI code)
- **Feature Interactions**: Complexity metric using 2^n - 1 - n formula
- **Test-to-Code Ratio**: How much of your code is tested

---

## 🧮 The Math Behind It

Revibe's defect estimation is based on industry research:

- **Human code**: ~15-50 defects per 1000 lines of code (KLOC)
- **AI-generated code**: 1.7x more defects than human code (Stanford/UIUC research)
- **Vibe-coded projects**: We use 42.5 defects/KLOC as the baseline

The feature interaction formula `2^n - 1 - n` calculates how many ways your features can interact:

| Features | Interaction Paths |
|----------|-------------------|
| 3 | 4 |
| 5 | 26 |
| 10 | 1,013 |
| 15 | 32,752 |

More features = exponentially more things that can break.

---

## 📋 CLI Reference

```bash
# Basic scan with terminal output
revibe scan <path>

# Output formats
revibe scan <path> --html       # HTML report (dark theme, copy buttons)
revibe scan <path> --json       # JSON output to stdout
revibe scan <path> --fix        # Generate REVIBE_FIXES.md
revibe scan <path> --cursor     # Generate .cursorrules
revibe scan <path> --claude     # Generate CLAUDE.md section
revibe scan <path> --all        # All formats

# Options
revibe scan <path> --output ./reports/  # Custom output directory
revibe scan <path> --ignore vendor,tmp  # Additional directories to ignore
revibe scan <path> --quiet              # Suppress terminal output
revibe scan <path> --no-color           # Disable colors

# Meta
revibe --version
revibe --help
```

---

## 🌐 Supported Languages

Revibe supports 30+ programming languages:

**Primary support** (function/class detection, feature detection):
Python, JavaScript, TypeScript, Go, Rust, Java, Kotlin, Swift, C#, PHP, Ruby, Dart

**Basic support** (LOC counting, file detection):
C, C++, Scala, Elixir, Lua, Perl, R, Shell, Vue, Svelte, SQL, Haskell, OCaml, F#, Clojure, Erlang, Zig, Nim, Crystal, Groovy

---

## ❓ FAQ

### Is this just for vibe-coded projects?

It works on any codebase, but it's specifically tuned for patterns common in AI-generated code. The smell detectors and fix prompts are designed for the kinds of issues AI tools create.

### Does it actually fix my code?

It generates instructions that your AI tool can execute. You run the scan, copy the prompt, paste it into Cursor/Claude/Copilot, and the AI applies the fix. Revibe is the auditor; your AI tool is the fixer.

### Is the CLI free forever?

Yes. MIT licensed. Free forever. We also have a web app at [revibe.help](https://revibe.help) if you want shareable reports and monitoring.

### What about false positives?

The health score and smell detectors are based on heuristics. They're meant to surface potential issues, not definitive bugs. Use your judgment when reviewing the suggestions.

### Can I use this in CI/CD?

Yes! Use `revibe scan . --json` for machine-readable output. The exit code is 0 for successful scans (regardless of health score). You can parse the JSON and fail builds based on health thresholds.

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

```bash
# Clone the repo
git clone https://github.com/webmyc/revibe.git
cd revibe

# Install in development mode
pip install -e ".[dev,pretty]"

# Run tests
pytest tests/ -v

# Run the CLI
revibe scan .
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=revibe --cov-report=term-missing

# Specific test file
pytest tests/test_fixer.py -v
```

---

## 📜 License

MIT — do whatever you want with it.

---

## 🔗 Links

- **Website**: [revibe.help](https://revibe.help)
- **PyPI**: [pypi.org/project/revibe](https://pypi.org/project/revibe)
- **npm**: [npmjs.com/package/revibe](https://www.npmjs.com/package/revibe)
- **GitHub**: [github.com/webmyc/revibe](https://github.com/webmyc/revibe)

---

*Built with ❤️ for vibe coders everywhere.*
