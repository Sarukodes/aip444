import os
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

print("git-cm: Developed by Saru Koirala - 188083232")
print("Run Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("--------------------------------------------------------------")

load_dotenv(find_dotenv())

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("❌ Error: OPENROUTER_API_KEY not found")
    sys.exit(1)

try:
    result = subprocess.run(
        ["git", "diff", "--staged"],
        capture_output=True,
        text=True,
        check=True
    )

    diff = result.stdout.strip()

    if not diff:
        print("❌ No staged changes found")
        sys.exit(1)

    print(f"✅ Diff found: {len(diff)} characters")

except subprocess.CalledProcessError:
    print("❌ Not a git repo.")
    sys.exit(1)