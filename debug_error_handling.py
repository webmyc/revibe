
from pathlib import Path
from revibe.scanner import scan_codebase
from revibe.analyzer import analyze_file

root = Path(".").resolve()
files = scan_codebase(str(root))

print(f"Scanning {len(files)} files in {root}...")

for f in files:        
    analysis = analyze_file(f)
    if analysis and not analysis.has_error_handling:
        print(f"MISSING: {f.relative_path} (is_test={f.is_test}) ({len(analysis.functions)} funcs)")
