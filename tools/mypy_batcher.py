import re
from pathlib import Path
from collections import defaultdict

# ═════════════════ Settings ═════════════════
BATCH_SIZE = 5
ERRORS_FILE = Path("mypy_errors.txt")
PROMPTS_DIR = Path("prompts")

# mypy error patterns
ERROR_PATTERN = re.compile(
    r"(?P<file>.*?):(?P<line>\d+): error: (?P<msg>.*?) \[(?P<code>.*?)\]"
)

# ═════════════════ 1. Reading errors ═════════════════
errors_by_file: dict[str, list[dict]] = defaultdict(list)
errors_by_code: dict[str, int] = defaultdict(int)

if not ERRORS_FILE.exists():
    print(f"File {ERRORS_FILE} not found.")
    exit(1)

with ERRORS_FILE.open(encoding="utf-8") as fh:
    for line in fh:
        m = ERROR_PATTERN.match(line)
        if not m:
            continue
        file = m.group("file")
        code = m.group("code")
        msg = m.group("msg")
        line_no = m.group("line")
        errors_by_file[file].append({
            "line": line_no,
            "code": code,
            "msg": msg,
        })
        errors_by_code[code] += 1

# display most frequent codes (optional)
print("Top error codes:")
for code, count in sorted(errors_by_code.items(), key=lambda x: -x[1])[:20]:
    print(f"{code:20} {count}")

# ═════════════════ 2. Building batches (each file once) ═════════════════
all_files = sorted(errors_by_file.keys())  # uniform ordering for stability
batches = [
    all_files[i:i + BATCH_SIZE]
    for i in range(0, len(all_files), BATCH_SIZE)
]

PROMPTS_DIR.mkdir(exist_ok=True)

# ═════════════════ 3. Generating prompt files ═════════════════
BASE_INSTRUCTIONS = (
    "You are a mypy error fixer. Below are the contents of one or more Python files "
    "and the mypy errors they contain. Your task is to fix ALL listed errors in each file.\n\n"
    "CRITICAL RULES:\n"
    "- Return ONLY a unified diff (patch) for each modified file.\n"
    "- Do NOT return the entire file.\n"
    "- Preserve existing code style and formatting.\n"
    "- Apply the minimal safe changes that satisfy mypy.\n"
    "- If a file needs no changes, do not include it in the output.\n\n"
    "Reply with a JSON object mapping filenames to their respective diffs. "
    "Example: {\"path/to/file.py\": \"--- a/path/to/file.py\\n+++ b/path/to/file.py\\n...\"}"
)

for idx, batch_files in enumerate(batches, start=1):
    prompt_parts = [
        BASE_INSTRUCTIONS,
        "=" * 60,
        f"Batch {idx} — files:",
        "\n".join(f"  - {f}" for f in batch_files),
        "=" * 60,
    ]

    for file_path in batch_files:
        p = Path(file_path)
        # file content (if it exists)
        if p.exists():
            file_content = p.read_text(encoding="utf-8")
        else:
            file_content = "# File not found (possibly deleted)"

        prompt_parts.append(f"\n{'─' * 60}")
        prompt_parts.append(f"File: {file_path}\n{file_content}\n")
        prompt_parts.append("Mypy errors in this file:")
        for err in errors_by_file[file_path]:
            prompt_parts.append(
                f"  Line {err['line']}: [{err['code']}] {err['msg']}"
            )
        prompt_parts.append("")  # empty line as separator

    prompt_text = "\n".join(prompt_parts)

    prompt_file = PROMPTS_DIR / f"batch_{idx:03d}.txt"
    prompt_file.write_text(prompt_text, encoding="utf-8")
    print(f"Created: {prompt_file}")

print(f"\nTotal {len(batches)} prompt files in folder '{PROMPTS_DIR}' ready.")