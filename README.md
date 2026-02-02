<div align="center">
  <img src="src/revibe/revibe%20logo.svg" alt="Revibe Logo" width="150" />
  <h1>Revibe</h1>
  <p>
    <b>Your vibe-coded project deserves a second pass. And a fix plan.</b>
  </p>
</div>

Revibe is a code health scanner built for the AI-assisted development era.

It analyzes a codebase, surfaces structural and quality risks, and converts them into clear, scoped prompts you can hand directly to AI coding tools like Cursor, Claude, or Copilot.

Revibe does not enforce rules.
It helps humans and AI reason about code quality together.

## Why Revibe Exists

AI has changed how code is written, refactored, and maintained.
Most tooling has not caught up.

Traditional analyzers assume:
- static rules
- binary pass or fail outcomes
- human only workflows

Revibe assumes:
- AI is already in the loop
- judgment matters
- clarity beats enforcement

Revibe answers a simple question:
**If I gave this codebase to a senior engineer and an AI pair programmer, what should they fix first?**

## What Revibe Does

Revibe scans a repository and produces:

### Code Health Signals
- complexity hotspots
- bug prone patterns
- brittle or low confidence areas

### Structural Insights
- oversized or unclear modules
- duplicated or tightly coupled logic
- unclear responsibilities

### Test Signals
- missing tests
- shallow or misleading coverage
- untested critical paths

### AI Ready Improvement Prompts
- concrete and scoped instructions
- written for review, not blind execution
- easy to paste into AI tools

### Output Formats
Revibe can generate:
- **Markdown**: Human readable reports with AI ready prompts
- **JSON**: Structured output for automation or tooling
- **HTML**: Shareable static reports

## Signal Confidence Vocabulary

Revibe assigns a confidence level to every signal.
This reflects how strongly the signal correlates with real-world problems, not how severe it sounds.

### High Confidence
Repeatedly observed in production systems.
- Strong correlation with bugs, regressions, or refactor pain
- Rarely false positives

**How to treat it:**
Act unless you have a clear reason not to.

### Medium Confidence
Common source of friction.
- Context-dependent
- Often becomes a problem as the codebase grows

**How to treat it:**
Review with intent. Decide consciously.

### Low Confidence
Weak signal.
- Often stylistic or situational
- Included to prompt curiosity, not action

**How to treat it:**
Optional. Ignore without guilt.

### Important Note
Revibe confidence is not certainty.
It is a prior, not a verdict.

Revibe helps you decide where to spend attention, not what is correct.

## What Revibe Is Not

Revibe is intentionally not:
- a linter replacement
- a formal static analyzer
- a CI gatekeeper
- a magic "fix my code" button

It does not claim correctness.
It optimizes for insight.

## CLI Usage

### Design Principles
The CLI is designed to be:
- quiet by default
- explicit when needed
- predictable
- readable without documentation

If a command surprises you, it is a bug.

### Basic Scan

```bash
revibe scan <path>
```

Examples:

```bash
revibe scan .
```
Scan the current repository.

```bash
revibe scan ./src
```
Scan a specific directory.

### Output Control

```bash
revibe scan . --fix
```
Generate `REVIBE_FIXES.md` with human readable report and AI prompts.

```bash
revibe scan . --json
```
Output structured results to stdout.

```bash
revibe scan . --html
```
Generate static shareable report (`revibe_report.html`).

### Scope Control

```bash
revibe scan . --ignore vendor,dist
```
Exclude generated or third party directories.

### AI Prompt Output

```bash
revibe scan . --cursor
```
Generate `.cursorrules` optimized for Cursor.

```bash
revibe scan . --claude
```
Generate `REVIBE_CLAUDE.md` notes for Claude.

Revibe never applies changes automatically.

### Exit Codes

- **0**: scan completed successfully
- **1**: invalid usage or configuration
- **2**: internal error

Revibe does not fail builds unless you explicitly wire it to do so.

## Typical Workflow

1. Run Revibe on a codebase
2. Review the report
3. Pick one concrete issue
4. Paste the prompt into your AI tool
5. Review the output like a senior engineer would
6. Repeat

This fits naturally into:
- refactoring sessions
- onboarding to unfamiliar code
- AI heavy development workflows
- pre release sanity checks

## Why Not SonarQube?

SonarQube is a strong tool.
Revibe is not trying to replace it.

They solve different problems.

### SonarQube Optimizes For
- enforcement
- standardized rules
- CI pipelines
- organizational governance
- long term metric tracking

It answers: *Does this code meet our standards? Should this build fail?*

### Revibe Optimizes For
- insight
- context
- AI assisted workflows
- human judgment
- early understanding

It answers: *Where should I look first? What feels risky but is not obviously broken?*

### Key Differences

| SonarQube | Revibe |
|-----------|--------|
| Rule based | Heuristic based |
| Enforces | Suggests |
| CI first | Developer first |
| Pass or fail | Gradient signals |
| Dashboards | Prompts |

### When SonarQube Wins
- large teams
- regulated environments
- strict quality gates
- enterprise systems

If you need guarantees, use SonarQube.

### When Revibe Wins
- AI first development
- solo developers or small teams
- refactoring and exploration
- legacy code onboarding
- early stage products

If you need clarity before certainty, use Revibe.

### The Short Version
SonarQube tells you whether code is acceptable.
Revibe helps you decide what to do next.

They coexist well.

## Project Status

Revibe is early stage and experimental.

- heuristics will evolve
- APIs may change
- output quality improves with feedback

If you want something polished and static, this is not it.
If you enjoy tools that grow through real use, welcome.

## Contributing

Revibe is opinionated by design.

See [CONTRIBUTING.md](CONTRIBUTING.md) for our design principles and guide.

Expect discussion around why something is flagged, not just how.

## License

MIT

---

**Final note, straight up**

Do not turn Revibe into a rule engine.

Its value is not precision.
Its value is taste, judgment, and good questions.
