#!/usr/bin/env python3
"""
GitHub 活跃度自动提交脚本 — 模拟真实开发行为
每次运行：
  - 随机决定是否提交 (概率 ~55%)
  - 如果提交，随机 1~3 次 commit
  - commit message 从真实开发场景中随机选取
  - activity.log 记录开发活动
"""
import os
import random
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 服务器 UTC，用户 UTC+8
CST = timezone(timedelta(hours=8))

REPO_DIR = Path.home() / "projects" / "NCBI_search-skill"
LOG_FILE = REPO_DIR / "activity.log"
SSH_KEY = Path.home() / ".ssh" / "id_ed26520"


def setup_ssh_agent():
    """Ensure SSH agent is running and key is loaded."""
    # Check if agent is already running and key is loaded
    result = subprocess.run(["ssh-add", "-l"], capture_output=True, text=True)
    if result.returncode == 0 and "id_ed26520" in result.stdout:
        return  # Already set up

    # Start ssh-agent and add key
    result = subprocess.run(
        ["ssh-agent", "-s"], capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        if line.startswith("SSH_AUTH_SOCK="):
            os.environ["SSH_AUTH_SOCK"] = line.split("=")[1].rstrip(";")
        elif line.startswith("SSH_AGENT_PID="):
            os.environ["SSH_AGENT_PID"] = line.split("=")[1].rstrip(";")

    subprocess.run(
        ["ssh-add", str(SSH_KEY)],
        capture_output=True, text=True
    )

# 真实的 commit message 模板（conventional commits 风格）
COMMIT_MSGS_SINGLE = [
    "chore: update activity log",
    "docs: minor README tweaks",
    "fix: correct search result parsing edge case",
    "refactor: clean up imports in pubmed_search.py",
    "chore: update .gitignore patterns",
    "docs: improve usage examples in SKILL.md",
    "fix: handle empty query response gracefully",
    "chore: bump version metadata",
    "refactor: simplify error handling flow",
    "docs: add notes on rate limiting",
    "fix: timeout handling for slow API responses",
    "chore: update dependencies comment",
    "refactor: extract helper functions",
    "docs: clarify installation steps",
    "fix: handle unicode characters in article titles",
    "chore: reorganize project structure notes",
    "perf: cache repeated API lookups",
    "fix: correct date formatting in log entries",
    "docs: add troubleshooting section",
    "chore: clean up debug print statements",
]

# 批量提交时的 message 组合（按主题分组）
COMMIT_BATCH_THEMES = [
    [
        "refactor: extract search query builder",
        "refactor: simplify result formatting logic",
        "test: add edge case for empty results",
    ],
    [
        "docs: rewrite README quick-start section",
        "docs: add API usage examples",
        "fix: correct broken link in documentation",
    ],
    [
        "fix: handle PubMed API timeout gracefully",
        "fix: retry logic for transient network errors",
        "chore: update error message formatting",
    ],
    [
        "feat: add journal impact factor lookup",
        "docs: document new impact factor feature",
        "chore: update version to reflect new feature",
    ],
    [
        "refactor: move constants to config module",
        "refactor: decouple search from formatting",
        "chore: update imports after refactor",
    ],
]

# activity.log 随机记录内容
ACTIVITY_TEMPLATES = [
    "Reviewed and refactored {module} — cleaner separation of concerns",
    "Fixed edge case in {module} where {issue}",
    "Updated documentation for {module}",
    "Investigated performance bottleneck in {module}",
    "Added error handling for {scenario}",
    "Cleaned up unused imports and dead code in {module}",
    "Tested search queries with various edge cases",
    "Reviewed PubMed API response format changes",
    "Optimized {module} for better readability",
    "Paired debugging session — resolved {issue}",
    "Code review: improved {module} error messages",
    "Refactored {module} to use configuration constants",
    "Added logging for {scenario} debugging",
    "Updated type hints in {module}",
    "Implemented retry mechanism for {scenario}",
]

MODULES = [
    "pubmed_search.py", "SKILL.md", "README.md",
    "scripts/", "query builder", "result parser",
    "config module", "error handler", "API client",
]

ISSUES = [
    "empty author field caused crash", "duplicate results appeared",
    "date range filter was off by one", "special chars broke query",
    "rate limit wasn't respected", "timeout wasn't caught",
    "results were truncated silently", "pagination skipped last page",
]

SCENARIOS = [
    "API rate limiting", "network timeout", "malformed response",
    "empty result set", "concurrent requests", "large result pagination",
    "invalid query syntax", "authentication failure",
]


def git(*args):
    """Run git command in repo directory."""
    result = subprocess.run(
        ["git"] + list(args),
        cwd=REPO_DIR,
        capture_output=True, text=True
    )
    return result.stdout.strip(), result.returncode


def make_commit(message: str):
    """Stage all changes and commit."""
    git("add", "-A")
    out, code = git("commit", "-m", message, "--allow-empty")
    return code == 0


def push():
    """Push to remote."""
    out, code = git("push", "origin", "main")
    return code == 0


def generate_activity_line() -> str:
    """Generate a realistic activity log entry."""
    template = random.choice(ACTIVITY_TEMPLATES)
    return template.format(
        module=random.choice(MODULES),
        issue=random.choice(ISSUES),
        scenario=random.choice(SCENARIOS),
    )


def update_log(num_entries: int):
    """Append random entries to activity.log."""
    now = datetime.now()
    lines = []
    for _ in range(num_entries):
        ts = now.strftime("[%Y-%m-%d %a %H:%M:%S]")
        lines.append(f"{ts} {generate_activity_line()}")
    with open(LOG_FILE, "a") as f:
        f.write("\n".join(lines) + "\n")


def run():
    setup_ssh_agent()
    now = datetime.now(CST)
    hour = now.hour

    # 凌晨 0~6 点不提交（中国时间，模拟睡觉）
    if 0 <= hour <= 6:
        print(f"[{now.strftime('%H:%M')} CST] Sleeping hours, skip.")
        return

    # 每次运行有 55% 概率提交
    if random.random() > 0.55:
        print(f"[{now}] No commit this round (random skip).")
        return

    # 决定提交几次（1~3 次，权重偏向 1 次）
    count = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
    print(f"[{now}] Making {count} commit(s)...")

    if count == 1:
        # 单次提交
        update_log(1)
        msg = random.choice(COMMIT_MSGS_SINGLE)
        if make_commit(msg):
            print(f"  ✓ {msg}")
        else:
            print("  ✗ Nothing to commit")
            return
    else:
        # 批量提交（使用主题组）
        theme = random.choice(COMMIT_BATCH_THEMES)
        for i in range(count):
            update_log(1)
            msg = theme[i] if i < len(theme) else random.choice(COMMIT_MSGS_SINGLE)
            if make_commit(msg):
                print(f"  ✓ {msg}")
            else:
                print(f"  ✗ Nothing to commit (step {i+1})")

    # 推送
    if push():
        print("  → Pushed to origin/main")
    else:
        print("  → Push failed (will retry next run)")


if __name__ == "__main__":
    run()
