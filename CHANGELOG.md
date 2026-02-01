# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-02-01

### Added
- Initial release of Revibe CLI
- Codebase health scanner with support for 30+ languages
- 8 AI code smell detectors
- Exact and near-duplicate file detection
- Defect density estimation based on research
- Feature interaction complexity analysis
- Health score calculation (0-100)
- **Fixer engine** — generates AI-ready fix instructions:
  - `REVIBE_FIXES.md` with copy-paste prompts
  - `.cursorrules` for Cursor IDE
  - `CLAUDE.md` section for Claude projects
- HTML report with dark theme and copy buttons
- JSON output for programmatic use
- Pretty terminal output with optional `rich`
- npm wrapper for `npx revibe`
- Homebrew formula template

[Unreleased]: https://github.com/webmyc/revibe/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/webmyc/revibe/releases/tag/v0.1.0
