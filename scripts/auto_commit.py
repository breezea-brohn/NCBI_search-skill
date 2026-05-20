#!/usr/bin/env python3
"""
GitHub 活跃度自动提交脚本 v2 — 每天自动生成计划，按计划执行

流程：
  1. 每天首次运行时生成当天计划：提交几次、每次什么时间
  2. 后续运行检查计划，到时间了就执行
  3. 每次执行完在本地 commit_log.md 记录详情

cron 每小时触发一次，脚本自己决定要不要动。
"""
import json
import os
import random
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

CST = timezone(timedelta(hours=8))
REPO_DIR = Path.home() / "projects" / "NCBI_search-skill"
LOG_FILE = REPO_DIR / "activity.log"          # repo 内的开发日志
COMMIT_LOG = Path.home() / ".hermes" / "gh_commit_log.md"  # 本地提交记录
PLAN_FILE = Path.home() / ".hermes" / "gh_commit_plan.json"
SSH_KEY = Path.home() / ".ssh" / "id_ed26520"

# ──────────────────── commit message 池 ────────────────────
COMMIT_MSGS = [
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

COMMIT_BATCH_THEMES = [
    ["refactor: extract search query builder",
     "refactor: simplify result formatting logic",
     "test: add edge case for empty results"],
    ["docs: rewrite README quick-start section",
     "docs: add API usage examples",
     "fix: correct broken link in documentation"],
    ["fix: handle PubMed API timeout gracefully",
     "fix: retry logic for transient network errors",
     "chore: update error message formatting"],
    ["feat: add journal impact factor lookup",
     "docs: document new impact factor feature",
     "chore: update version to reflect new feature"],
    ["refactor: move constants to config module",
     "refactor: decouple search from formatting",
     "chore: update imports after refactor"],
]

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
MODULES = ["pubmed_search.py", "SKILL.md", "README.md", "scripts/",
           "query builder", "result parser", "config module", "error handler", "API client"]
ISSUES = ["empty author field caused crash", "duplicate results appeared",
           "date range filter was off by one", "special chars broke query",
           "rate limit wasn't respected", "timeout wasn't caught",
           "results were truncated silently", "pagination skipped last page"]
SCENARIOS = ["API rate limiting", "network timeout", "malformed response",
              "empty result set", "concurrent requests", "large result pagination",
              "invalid query syntax", "authentication failure"]


# ──────────────────── git helpers ────────────────────
def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=REPO_DIR, capture_output=True, text=True)
    return r.stdout.strip(), r.returncode

def make_commit(msg):
    git("add", "-A")
    _, code = git("commit", "-m", msg, "--allow-empty")
    return code == 0

def push():
    _, code = git("push", "origin", "main")
    return code == 0


# ──────────────────── log helpers ────────────────────
def gen_activity():
    return random.choice(ACTIVITY_TEMPLATES).format(
        module=random.choice(MODULES), issue=random.choice(ISSUES), scenario=random.choice(SCENARIOS))

def update_activity_log(n):
    now = datetime.now()
    lines = [f"[{now.strftime('%Y-%m-%d %a %H:%M:%S')}] {gen_activity()}" for _ in range(n)]
    with open(LOG_FILE, "a") as f:
        f.write("\n".join(lines) + "\n")

def write_commit_log(entries):
    """Write to local commit log (~/.hermes/gh_commit_log.md)."""
    COMMIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(COMMIT_LOG, "a") as f:
        for e in entries:
            f.write(f"- {e['time']} | {e['msg']} | {'✓ push' if e['pushed'] else '✗ push fail'}\n")


# ──────────────────── plan ────────────────────
def load_plan():
    if PLAN_FILE.exists():
        data = json.loads(PLAN_FILE.read_text())
        if data.get("date") == datetime.now(CST).strftime("%Y-%m-%d"):
            return data
    return None

def save_plan(plan):
    PLAN_FILE.parent.mkdir(parents=True, exist_ok=True)
    PLAN_FILE.write_text(json.dumps(plan, ensure_ascii=False, indent=2))

def generate_daily_plan():
    """随机决定今天提交几次（1~5），每次在哪个时间点。"""
    count = random.randint(1, 5)
    # 生成 count 个不重复的小时（8~22 点之间），按时间排序
    hours = sorted(random.sample(range(8, 23), min(count, 15)))
    # 如果 count > 可选小时数（不太可能），就允许重复
    while len(hours) < count:
        hours.append(random.choice(range(8, 23)))
    hours = sorted(hours[:count])

    # 每次提交 1~3 个 commit
    slots = []
    for h in hours:
        m = random.randint(0, 59)
        commit_count = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
        slots.append({"hour": h, "minute": m, "commits": commit_count, "done": False})

    plan = {
        "date": datetime.now(CST).strftime("%Y-%m-%d"),
        "total_planned": count,
        "slots": slots,
    }
    save_plan(plan)
    return plan


# ──────────────────── main ────────────────────
def run():
    os.environ["GIT_SSH_COMMAND"] = f"ssh -i {SSH_KEY} -o StrictHostKeyChecking=no"
    now = datetime.now(CST)
    hour, minute = now.hour, now.minute

    # 凌晨不跑
    if 0 <= hour <= 7:
        return

    # 加载或生成今日计划
    plan = load_plan()
    if plan is None:
        plan = generate_daily_plan()
        print(f"[{now.strftime('%H:%M')}] 今日计划已生成：{plan['total_planned']} 次提交")
        for s in plan["slots"]:
            print(f"  → {s['hour']:02d}:{s['minute']:02d}  ({s['commits']} commits)")

    # 检查是否有到时间且未执行的 slot
    for slot in plan["slots"]:
        if slot["done"]:
            continue
        # 到时间了（当前时间 >= 计划时间，且在 2 小时窗口内）
        slot_minutes = slot["hour"] * 60 + slot["minute"]
        now_minutes = hour * 60 + minute
        if now_minutes < slot_minutes:
            continue  # 还没到
        if now_minutes - slot_minutes > 180:
            # 超过 2 小时没执行，跳过（避免深夜补跑）
            slot["done"] = True
            save_plan(plan)
            continue

        # 执行这个 slot
        count = slot["commits"]
        print(f"[{now.strftime('%H:%M')}] 执行计划：{count} commit(s)")
        log_entries = []

        if count == 1:
            update_activity_log(1)
            msg = random.choice(COMMIT_MSGS)
            ok = make_commit(msg)
            pushed = push() if ok else False
            status = "✓" if ok else "✗"
            print(f"  {status} {msg} | push: {'✓' if pushed else '✗'}")
            log_entries.append({"time": now.strftime("%Y-%m-%d %H:%M"), "msg": msg, "pushed": pushed})
        else:
            theme = random.choice(COMMIT_BATCH_THEMES)
            for i in range(count):
                update_activity_log(1)
                msg = theme[i] if i < len(theme) else random.choice(COMMIT_MSGS)
                ok = make_commit(msg)
                status = "✓" if ok else "✗"
                print(f"  {status} {msg}")
                log_entries.append({"time": now.strftime("%Y-%m-%d %H:%M"), "msg": msg, "pushed": False})
            pushed = push()
            print(f"  → Push: {'✓' if pushed else '✗'}")
            for e in log_entries:
                e["pushed"] = pushed

        # 记录到本地日志
        write_commit_log(log_entries)
        slot["done"] = True
        save_plan(plan)
        return  # 一轮只执行一个 slot

    # 没有需要执行的
    remaining = sum(1 for s in plan["slots"] if not s["done"])
    if remaining:
        next_slot = next(s for s in plan["slots"] if not s["done"])
        print(f"[{now.strftime('%H:%M')}] 等待中，下次 {next_slot['hour']:02d}:{next_slot['minute']:02d}（剩余 {remaining} 次）")
    else:
        print(f"[{now.strftime('%H:%M')}] 今日计划全部完成 ✓")


if __name__ == "__main__":
    run()
