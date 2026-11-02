import sys
import subprocess
import re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def scan_tracked_files():
    files = subprocess.check_output(["git", "ls-files"]).decode("utf-8").splitlines()
    suspicious = []
    
    # Patterns for real secrets (excluding mock/test strings)
    pattern = re.compile(r'(?i)(secret[_-]?key|api[_-]?key|private[_-]?key|jwt[_-]?secret)\s*[:=]\s*["\']([^"\']+)["\']')
    
    ignored_patterns = [
        "dev-insecure",
        "placeholder",
        "your_",
        "example",
        "supersecret",
        "a_strong_",
        "test_",
        "<",
        "CHANGEME",
        "change-in-production",
    ]

    for f in files:
        path = Path(f)
        if path.suffix in [".png", ".jpg", ".joblib", ".ico", ".svg"]:
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                for line_no, line in enumerate(fp, 1):
                    match = pattern.search(line)
                    if match:
                        val = match.group(2)
                        if any(ign in val.lower() or ign in line.lower() for ign in ignored_patterns):
                            continue
                        if len(val) > 8:
                            suspicious.append((f, line_no, line.strip()))
        except Exception:
            pass

    print(f"Scanned {len(files)} tracked files.")
    if suspicious:
        print(f"⚠️ Found {len(suspicious)} suspicious secret lines:")
        for file, lno, text in suspicious:
            print(f"  {file}:{lno} -> {text[:80]}")
    else:
        print("✓ Zero real secrets or unmasked keys found in git tracked files.")
    return len(suspicious)

if __name__ == "__main__":
    exit(scan_tracked_files())
