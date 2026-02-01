# Revibe npm Package

This is a Node.js wrapper for the [Revibe](https://revibe.help) Python package.

## Usage

Run with npx (no install needed):

```bash
npx revibe scan ./my-project
```

Or install globally:

```bash
npm install -g revibe
revibe scan ./my-project
```

## Requirements

- Node.js 16+
- Python 3.9+ (will be detected automatically)

The npm package will automatically install the Python `revibe` package via pip if it's not already installed.

## Commands

```bash
# Scan current directory
revibe scan .

# Generate HTML report
revibe scan ./project --html

# Generate copy-paste fix instructions
revibe scan ./project --fix

# Generate Cursor rules
revibe scan ./project --cursor

# Generate all outputs
revibe scan ./project --all
```

## More Info

- Website: [revibe.help](https://revibe.help)
- PyPI: [pypi.org/project/revibe](https://pypi.org/project/revibe/)
- GitHub: [github.com/AK-Issac/revibe](https://github.com/AK-Issac/revibe)
