import os
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

print("git-cm: Developed by Saru Koirala - 188083232")
print("Run Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("--------------------------------------------------------------")

load_dotenv(find_dotenv())

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("❌ Error: OPENROUTER_API_KEY not found")
    sys.exit(1)

is_creative = "--creative" in sys.argv

try:
    result = subprocess.run(
        ["git", "diff", "--staged"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
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

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

system_prompt = (
    "You are an LLM running in a CLI tool which writes semantic commit messages. "
    "Output ONLY the commit message using Conventional Commits format."
)

temperature = 0.1

if is_creative:
    system_prompt = (
        "You are a pirate writing funny git commit messages using Gitmoji and 17th century pirate slang."
    )
    temperature = 1.2

response = client.chat.completions.create(
    model="google/gemma-4-31b-it:free",
    messages=[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": diff
        }
    ],
    temperature=temperature
)

print("\nGenerated Commit Message:")
print(response.choices[0].message.content)


# ai integration test
# screenshot test
# creative mode screenshot