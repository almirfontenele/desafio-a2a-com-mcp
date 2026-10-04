#!/usr/bin/env python3
"""
Step Runner and Verification Orchestrator for A2A-MCP Bridge Challenge

This script enforces step-by-step development and verification according to
the technical specifications (docs/spec/SPEC-a2a-mcp-bridge.md) and wire examples
(exemplos/wire/*.json). It prevents AI hallucination and ensures deterministic execution.

Usage:
    python3 run_steps.py --list
    python3 run_steps.py --step <1-6>
    python3 run_steps.py --all
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.request
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
TASKS_DIR = BASE_DIR / "docs" / "tasks"

STEP_MAP = {
    1: {
        "title": "MCP Transport & Metadata Validation",
        "file": TASKS_DIR / "step-01-mcp-transport-and-meta-validation.md",
        "checks": [1, 4, 5],
        "mcp_required": True,
        "agent_required": False,
    },
    2: {
        "title": "MCP Domain Tools & Resource Exposure",
        "file": TASKS_DIR / "step-02-mcp-tools-and-resources.md",
        "checks": [2, 3, 6, 7, 8, 9, 10, 11, 12],
        "mcp_required": True,
        "agent_required": False,
    },
    3: {
        "title": "MCP MRTR Elicitation & State Protection",
        "file": TASKS_DIR / "step-03-mcp-mrtr-elicitation-and-state.md",
        "checks": [13, 14, 15, 16, 17, 18, 19, 20],
        "mcp_required": True,
        "agent_required": False,
    },
    4: {
        "title": "A2A Agent Card & Server Endpoints",
        "file": TASKS_DIR / "step-04-a2a-agent-card-and-endpoints.md",
        "checks": [21, 22, 23],
        "mcp_required": False,
        "agent_required": True,
    },
    5: {
        "title": "A2A-MCP Bridge & Task Lifecycle Management",
        "file": TASKS_DIR / "step-05-a2a-mcp-bridge-and-workflow.md",
        "checks": list(range(24, 37)),
        "mcp_required": True,
        "agent_required": True,
    },
    6: {
        "title": "Full Compliance & End-to-End Verification",
        "file": TASKS_DIR / "step-06-full-compliance-verification.md",
        "checks": list(range(1, 37)),
        "mcp_required": True,
        "agent_required": True,
    },
    7: {
        "title": "Unit Testing & Component Isolation Suite",
        "file": TASKS_DIR / "step-07-unit-tests-suite.md",
        "checks": [],
        "mcp_required": False,
        "agent_required": False,
        "is_unit_test": True,
    },
}


def print_banner(text: str, char: str = "=") -> None:
    line = char * 80
    print(f"\n{line}\n{text}\n{line}")


def check_env_vars() -> bool:
    secret = os.environ.get("REQUEST_STATE_SECRET")
    if not secret:
        print("[WARNING] REQUEST_STATE_SECRET environment variable is NOT set.")
        print("  Run: export REQUEST_STATE_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')")
        return False
    if len(secret) < 32:
        print("[WARNING] REQUEST_STATE_SECRET should be at least 32 bytes (64 hex chars).")
        return False
    return True


def is_service_listening(url: str) -> bool:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=2):
            return True
    except urllib.error.HTTPError:
        return True  # Received HTTP status (e.g. 404 or 405), server is listening
    except Exception:
        return False


def display_step_info(step_num: int) -> None:
    info = STEP_MAP[step_num]
    print_banner(f"STEP {step_num:02d}: {info['title']}")
    
    if info["file"].exists():
        content = info["file"].read_text()
        print(content)
    else:
        print(f"[ERROR] Task file not found: {info['file']}")


def run_step_verification(step_num: int, mcp_url: str, agent_url: str) -> bool:
    info = STEP_MAP[step_num]
    print_banner(f"VERIFYING STEP {step_num:02d}: {info['title']}", "-")

    if info.get("is_unit_test"):
        print("Executing Unit Testing suite via python unittest...")
        cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        if result.returncode == 0:
            print(f"\n[RESULT] Step {step_num} (Unit Testing) PASSED clean!")
            return True
        else:
            print(f"\n[RESULT] Step {step_num} (Unit Testing) FAILED.")
            return False

    # Check required services
    if info["mcp_required"] and not is_service_listening(mcp_url):
        print(f"[ERROR] MCP Server is NOT reachable at {mcp_url}")
        print("  Ensure your MCP server is running on port 7301 before running verification.")
        return False

    if info["agent_required"] and not is_service_listening(agent_url):
        print(f"[ERROR] A2A Agent is NOT reachable at {agent_url}")
        print("  Ensure your A2A agent is running on port 7300 before running verification.")
        return False

    # Reset in-memory state if server supports /reset
    try:
        req = urllib.request.Request(f"{mcp_url.rstrip('/')}/reset", data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=1):
            pass
    except Exception:
        pass
    try:
        req = urllib.request.Request(f"{agent_url.rstrip('/')}/reset", data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=1):
            pass
    except Exception:
        pass

    print(f"Target Checks for Step {step_num}: {info['checks']}")
    print("Executing full validator suite...")

    cmd = [
        sys.executable,
        str(BASE_DIR / "validador" / "validar.py"),
        "--agente",
        agent_url,
        "--mcp",
        mcp_url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout + result.stderr

    # Parse output lines for target checks
    step_checks = info["checks"]
    passed_step_checks = []
    failed_step_checks = []

    for line in output.splitlines():
        for chk in step_checks:
            tag = f"{chk:02d}"
            if f"PASS {tag}" in line:
                passed_step_checks.append(line)
            elif f"FAIL {tag}" in line:
                failed_step_checks.append(line)

    print("\n--- STEP VERIFICATION SUMMARY ---")
    for pass_line in passed_step_checks:
        print(f"  [OK] {pass_line}")
    for fail_line in failed_step_checks:
        print(f"  [FAIL] {fail_line}")

    if failed_step_checks:
        print(f"\n[RESULT] Step {step_num} FAILED ({len(failed_step_checks)} checks failed).")
        return False

    if len(passed_step_checks) == len(step_checks):
        print(f"\n[RESULT] Step {step_num} PASSED all {len(step_checks)} designated checks!")
        return True
    else:
        print(f"\n[RESULT] Partial execution: {len(passed_step_checks)}/{len(step_checks)} checks passed.")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="A2A-MCP Bridge Step Task Runner & Anti-Hallucination Verifier")
    parser.add_argument("--step", type=int, choices=range(1, 8), help="Step number (1-7) to display and verify")
    parser.add_argument("--list", action="store_true", help="List all development steps")
    parser.add_argument("--all", action="store_true", help="Execute verification across all steps 1 to 6")
    parser.add_argument("--mcp", default="http://localhost:7301", help="MCP server URL (default: http://localhost:7301)")
    parser.add_argument("--agente", default="http://localhost:7300", help="A2A agent URL (default: http://localhost:7300)")

    args = parser.parse_args()

    check_env_vars()

    if args.list:
        print_banner("A2A-MCP BRIDGE IMPLEMENTATION STEPS")
        for num, info in STEP_MAP.items():
            print(f"  Step {num:02d}: {info['title']}")
            print(f"          Target Checks: PASS {min(info['checks']):02d} to PASS {max(info['checks']):02d}")
            print(f"          File: {info['file'].relative_to(BASE_DIR)}")
            print()
        return

    if args.step:
        display_step_info(args.step)
        run_step_verification(args.step, args.mcp, args.agente)
        return

    if args.all:
        print_banner("RUNNING FULL E2E STEP VERIFICATION")
        all_passed = True
        for step_num in range(1, 7):
            success = run_step_verification(step_num, args.mcp, args.agente)
            if not success:
                all_passed = False
                print(f"[STOP] Halting step execution due to failure in Step {step_num}.")
                break
        if all_passed:
            print_banner("SUCCESS: ALL STEPS PASSED 100% COMPLIANCE GATE!")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
