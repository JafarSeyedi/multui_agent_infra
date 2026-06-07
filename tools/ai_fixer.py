#!/usr/bin/env python3
"""
Professional mypy + ruff fixer using the FREE DeepSeek Chat web interface.
- Uses Playwright to control an already‑logged‑in Chrome on Windows.
- Prompts the model to return a JSON with fixes (diff) and uncertain errors.
- Simulates human typing / delays to avoid rate limits.
- Iterative process; most‑erroneous files first.
"""

import os
import re
import sys
import json
import shutil
import tempfile
import subprocess
import time
import random
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ════════════════ Configuration ════════════════
# WSL ↔ Windows remote debugging
WINDOWS_HOST_IP = os.environ.get("WINDOWS_HOST_IP", "127.0.0.1")
# WINDOWS_HOST_IP = os.environ.get("WINDOWS_HOST_IP", "172.28.16.1")

DEBUG_PORT = int(os.environ.get("DEBUG_PORT", "9222"))

PROJECT_ROOT = Path(".").resolve()
MAX_OUTER_ITER = 10
MAX_FILE_CONTENT_CHARS = 50000
PATCH_PREFIX_LEVEL = 1
UNCERTAIN_FILE = PROJECT_ROOT / "uncertain_errors.txt"

# Human‑behavior delays (seconds)
MIN_DELAY_BETWEEN_MESSAGES = 4
MAX_DELAY_BETWEEN_MESSAGES = 10
TYPING_DELAY_MS = 50          # ms between each character when “typing”

# ════════════════ Browser helper ════════════════
def connect_browser():
    """Connect to the Chrome instance with remote debugging enabled."""
    playwright = sync_playwright().start()
    browser = playwright.chromium.connect_over_cdp(
        f"http://{WINDOWS_HOST_IP}:{DEBUG_PORT}"
    )
    return playwright, browser

def get_chat_page(browser):
    """Return a page on chat.deepseek.com, already logged‑in."""
    context = browser.contexts[0]
    page = context.new_page()
    page.goto("https://chat.deepseek.com/")
    # Wait for the chat input to be ready
    page.wait_for_selector("textarea[placeholder*='Send a message']", timeout=15000)
    return page

def human_type(page, text: str):
    """Type text char‑by‑char with a small delay to look human."""
    for char in text:
        page.keyboard.type(char, delay=random.randint(TYPING_DELAY_MS-20, TYPING_DELAY_MS+30))

def send_message_and_get_response(page, message: str) -> str:
    """
    Send a message to DeepSeek chat and return the full text of the assistant reply.
    Handles the clipboard paste trick because very long text can’t be typed reliably.
    """
    textarea = page.locator("textarea[placeholder*='Send a message']")
    # Clear any leftover text
    textarea.click()
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")

    # For very long messages, use clipboard paste (more human than always)
    if len(message) > 200:
        # Use Playwright's clipboard API
        page.evaluate("navigator.clipboard.writeText(arguments[0])", message)
        page.keyboard.press("Control+V")
    else:
        human_type(page, message)

    # Random short pause before sending (like a human thinking)
    time.sleep(random.uniform(0.5, 2))
    page.keyboard.press("Enter")

    # Wait for the response to finish (the "Stop generating" button disappears)
    try:
        page.wait_for_selector(
            "button:has-text('Stop generating')",
            state="detached",
            timeout=120000,
        )
    except PlaywrightTimeout:
        # If timeout, just try to grab whatever is there
        pass

    # Small additional wait to ensure the response is fully rendered
    time.sleep(random.uniform(1, 2))

    # Get all assistant messages, return the last one
    assistant_messages = page.locator(".message.assistant")
    if assistant_messages.count() == 0:
        raise Exception("No assistant response found.")
    return assistant_messages.last.inner_text()

# ════════════════ Prompt construction ════════════════
SYSTEM_INSTRUCTION = (
    "You are an elite Python static analysis fixer. You receive a single file's content "
    "(or relevant excerpt) and a list of its mypy/ruff errors.\n\n"
    "**Your output must be a valid JSON object with exactly two keys:**\n"
    "1. `\"fixes\"`: a JSON object mapping filename (string) to a unified diff (string). "
    "If you can confidently fix all errors, put the diff here. If you are not fully confident, set the diff to `null`.\n"
    "2. `\"uncertain\"`: a JSON array of error descriptions you intentionally leave for human review because:\n"
    "   - The fix would change runtime behavior.\n"
    "   - The correct type annotation is ambiguous.\n"
    "   - You need more context than provided.\n"
    "   Describe each uncertain error with: `{\"line\": <int>, \"code\": \"<code>\", \"reason\": \"<brief reason>\"}`.\n\n"
    "**RULES for generating diffs:**\n"
    "- Diffs must be applicable with `patch -p1` from the project root.\n"
    "- Use minimal, safe edits. Preserve existing code style.\n"
    "- If the file is an excerpt and you cannot safely produce a diff that applies to the real file, "
    "set `\"fixes\"` to `null` and include the error in `\"uncertain\"`.\n"
    "- Do NOT include any text outside the JSON. No explanations, no markdown besides the JSON object.\n\n"
    "**Token economy:**\n"
    "- Do not repeat unchanged parts of the file in the diff.\n"
    "- Return only the unified diff, not the whole file.\n\n"
    "Here is an example valid response:\n"
    "```json\n"
    "{\n"
    '  "fixes": {\n'
    '    "src/util.py": "--- a/src/util.py\\n+++ b/src/util.py\\n@@ -12,7 +12,7 @@\\n-    x = foo()\\n+    x: int = foo()"\n'
    "  },\n"
    '  "uncertain": [\n'
    '    {"line": 25, "code": "arg-type", "reason": "Could not determine correct type due to dynamic dispatch"}\n'
    "  ]\n"
    "}\n"
    "```"
)

def build_full_prompt(file_rel: str, content: str, errors: List[dict]) -> str:
    error_lines = "\n".join(f"  Line {e['line']}: [{e['code']}] {e['msg']}" for e in errors)
    return (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"File: {file_rel}\n"
        f"Content:\n```python\n{content}\n```\n\n"
        f"Errors to fix:\n{error_lines}\n\n"
        "Now output ONLY the required JSON."
    )

# ════════════════ Response parser ════════════════
def parse_chat_response(raw: str, file_rel: str, errors: List[dict]) -> Tuple[Optional[str], list]:
    """Extract JSON from the chat response and return (diff, uncertain)."""
    # Strip any surrounding text, find JSON block
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    json_str = m.group(1) if m else raw

    # Remove any leading/trailing whitespace that might interfere
    json_str = json_str.strip()
    # Sometimes the model wraps the JSON in a dict key? Try to extract just the JSON object
    if not json_str.startswith("{"):
        # Try to find the first '{'
        start = json_str.find("{")
        if start != -1:
            json_str = json_str[start:]
        end = json_str.rfind("}")
        if end != -1:
            json_str = json_str[:end+1]

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        # If still fails, treat entire response as uncertain
        print("   JSON decode error; treating all errors as uncertain.")
        uncertain = [{"line": e["line"], "code": e["code"], "reason": "Chat response not parseable"} for e in errors]
        return None, uncertain

    fixes = data.get("fixes", {})
    uncertain = data.get("uncertain", [])
    diff = fixes.get(file_rel)

    if not isinstance(diff, str) or not diff.strip():
        diff = None
        found_uncertain_lines = {item.get("line") for item in uncertain if "line" in item}
        for e in errors:
            if e["line"] not in found_uncertain_lines:
                uncertain.append({
                    "line": e["line"],
                    "code": e["code"],
                    "reason": "Model was not confident enough to fix"
                })

    return diff, uncertain

# ════════════════ Tool runners & patches (unchanged) ════════════════
def run_tool(cmd: List[str], timeout=120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=PROJECT_ROOT)

def parse_mypy(text: str) -> Dict[str, List[dict]]:
    errors: Dict[str, List[dict]] = defaultdict(list)
    for m in re.finditer(r"^(?P<file>.+?):(?P<line>\d+): error: (?P<msg>.*?)  \[(?P<code>\S+)\]", text, re.MULTILINE):
        errors[m.group("file")].append({
            "line": int(m.group("line")),
            "code": m.group("code"),
            "msg": m.group("msg").strip()
        })
    return dict(errors)

def parse_ruff(text: str) -> Dict[str, List[dict]]:
    errors: Dict[str, List[dict]] = defaultdict(list)
    for m in re.finditer(r"^(?P<file>.+?):(?P<line>\d+):(?P<col>\d+): (?P<code>\S+) (?P<msg>.+)$", text, re.MULTILINE):
        errors[m.group("file")].append({
            "line": int(m.group("line")),
            "code": m.group("code"),
            "msg": m.group("msg").strip()
        })
    return dict(errors)

def get_combined_errors() -> Dict[str, List[dict]]:
    print("🔍 Running mypy...")
    mypy_res = run_tool(["mypy", ".", "--show-error-codes", "--no-error-summary"])
    mypy_errors = parse_mypy(mypy_res.stdout)
    print(f"   mypy: {sum(len(v) for v in mypy_errors.values())} errors in {len(mypy_errors)} files")

    print("🔍 Running ruff...")
    ruff_res = run_tool(["ruff", "check", "."])
    ruff_errors = parse_ruff(ruff_res.stdout)
    print(f"   ruff: {sum(len(v) for v in ruff_errors.values())} errors in {len(ruff_errors)} files")

    combined = defaultdict(list)
    for f, errs in mypy_errors.items():
        combined[f].extend(errs)
    for f, errs in ruff_errors.items():
        combined[f].extend(errs)
    return dict(combined)

def get_file_excerpt(file_path: Path, errors: List[dict], max_chars: int = MAX_FILE_CONTENT_CHARS) -> str:
    try:
        full = file_path.read_text(encoding="utf-8")
    except Exception:
        return ""
    if len(full) <= max_chars:
        return full

    needed_lines: set = set()
    for e in errors:
        for delta in range(-5, 6):
            line_no = e["line"] + delta
            if line_no > 0:
                needed_lines.add(line_no)

    lines = full.splitlines(keepends=True)
    excerpt_lines = []
    last_written = 0
    for i, line in enumerate(lines, start=1):
        if i in needed_lines:
            if last_written and i > last_written + 1:
                excerpt_lines.append(f"... (lines {last_written+1}-{i-1} omitted)\n")
            excerpt_lines.append(line)
            last_written = i

    result = "".join(excerpt_lines)
    if len(result) > max_chars:
        result = "\n".join(
            f"Line {e['line']}: {lines[e['line']-1].rstrip()}" for e in errors if e['line'] <= len(lines)
        )
    return result[:max_chars]

def apply_patch(file_rel: str, diff_text: str) -> bool:
    file_path = PROJECT_ROOT / file_rel
    backup_dir = PROJECT_ROOT / ".fix_backups"
    backup_dir.mkdir(exist_ok=True)
    backup = backup_dir / file_path.name
    shutil.copy2(file_path, backup)

    tmp_diff = tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False)
    tmp_diff.write(diff_text)
    tmp_diff.close()
    try:
        cmd = ["patch", f"-p{PATCH_PREFIX_LEVEL}", "--no-backup-if-mismatch", "-i", tmp_diff.name]
        proc = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
        if proc.returncode == 0:
            print("   ✅ Patch applied")
            return True
        else:
            print(f"   ❌ Patch failed: {proc.stderr.strip()}")
            shutil.copy2(backup, file_path)
            return False
    finally:
        Path(tmp_diff.name).unlink(missing_ok=True)

# ════════════════ Main loop ════════════════
def main():
    print("=== Chat‑based DeepSeek fixer (no API key) ===")
    playwright, browser = None, None
    try:
        # Connect to already‑open Chrome
        playwright, browser = connect_browser()
        page = get_chat_page(browser)

        total_files_processed = 0
        total_uncertain = 0
        UNCERTAIN_FILE.write_text("", encoding="utf-8")

        for outer in range(1, MAX_OUTER_ITER + 1):
            print(f"\n{'='*60}")
            print(f"🔄 Outer iteration {outer}/{MAX_OUTER_ITER}")
            print("="*60)

            combined = get_combined_errors()
            if not combined:
                print("✅ No errors left. Exiting.")
                break

            sorted_files = sorted(combined.items(), key=lambda kv: len(kv[1]), reverse=True)
            total_errors_this_round = sum(len(errs) for _, errs in sorted_files)
            print(f"📊 {total_errors_this_round} errors across {len(sorted_files)} files.")

            for idx, (file_rel, errors) in enumerate(sorted_files, start=1):
                file_path = PROJECT_ROOT / file_rel
                if not file_path.exists():
                    print(f"  ⚠️  {file_rel} not found, skipping.")
                    continue

                print(f"\n📄 [{idx}/{len(sorted_files)}] {file_rel} ({len(errors)} errors)")

                content = get_file_excerpt(file_path, errors)
                print(f"   Content size: {len(content)} chars")

                prompt_text = build_full_prompt(file_rel, content, errors)

                # Retry logic for unreadable responses
                max_tries = 3
                diff = None
                uncertain = []
                for attempt in range(1, max_tries+1):
                    try:
                        raw_response = send_message_and_get_response(page, prompt_text)
                        diff, uncertain = parse_chat_response(raw_response, file_rel, errors)
                        break   # success
                    except Exception as e:
                        print(f"   Attempt {attempt} failed: {e}")
                        if attempt == max_tries:
                            uncertain = [{"line": e2["line"], "code": e2["code"], "reason": f"Failed after {max_tries} attempts"} for e2 in errors]
                        else:
                            time.sleep(random.uniform(10, 20))

                # Write uncertain errors
                if uncertain:
                    with UNCERTAIN_FILE.open("a", encoding="utf-8") as uf:
                        for u in uncertain:
                            uf.write(f"{file_rel}:{u.get('line','?')} [{u.get('code','?')}] {u.get('reason','')}\n")
                    total_uncertain += len(uncertain)
                    print(f"   {len(uncertain)} uncertain errors saved.")

                if diff:
                    if apply_patch(file_rel, diff):
                        total_files_processed += 1

                # Human‑like pause between files
                delay = random.uniform(MIN_DELAY_BETWEEN_MESSAGES, MAX_DELAY_BETWEEN_MESSAGES)
                print(f"   ⏳ Pausing {delay:.1f}s before next file...")
                time.sleep(delay)

            print(f"\n📈 End of iteration {outer}. Files modified this round: {len(sorted_files)}, total fixed: {total_files_processed}")
            print(f"   Uncertain errors accumulated: {total_uncertain}")

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        if browser and playwright:
            browser.close()
            playwright.stop()

    print(f"\n🎉 Done. Check `{UNCERTAIN_FILE}` for remaining issues.")

if __name__ == "__main__":
    main()