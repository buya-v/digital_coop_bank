#!/usr/bin/env python3
import os
import sys
import json
import argparse
import shutil
import subprocess
import time
from agent_prompts import PROMPTS, COMMON_RULES

# All paths are anchored to this script's directory, so the pipeline behaves
# the same no matter which directory you run it from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "pipeline_state.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "requirements_output")
LEARNINGS_FILE = os.path.join(OUTPUT_DIR, "sprint_learnings.md")

# The Sprint Planner (PO scoping pass) now runs BEFORE the story writer, so
# downstream agents receive an explicit in-scope list instead of guessing.
# The PO orchestrator still closes the sprint with the PRD synthesis.
PHASES = [
    ("market_researcher", "Phase 1: Market & Competitor Research"),
    ("business_analyst", "Phase 2: Domain Analysis & Scope Mapping"),
    ("sprint_planner", "Phase 3: Sprint Scoping & Prioritization"),
    ("user_story_writer", "Phase 4: User Story Drafting"),
    ("qa_writer", "Phase 5: Acceptance Criteria Writing"),
    ("technical_architect", "Phase 6: Technical Architecture Mapping"),
    ("po_orchestrator", "Phase 7: PRD Synthesis & Roadmap"),
]

# Which previous-sprint deliverables are carried forward as context.
# The PRD (po_orchestrator) carries decisions/roadmap; the architecture doc
# carries the data model that must be extended rather than redefined.
CARRYOVER_PHASES = ["po_orchestrator", "technical_architect"]

LLM_TIMEOUT_SECONDS = 900
LLM_RETRIES = 2

PLACEHOLDER_BLOCKLIST = ["marcus aurelius", "john doe", "jane doe", "lorem ipsum", "tbd later", "[insert"]


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "project_name": "",
        "vision": "",
        "sprint": 1,
        "current_phase_index": 0,
        "history": [],
    }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def run_llm(prompt):
    """Executes a prompt using the agy CLI tool and returns the response.

    The prompt is passed via stdin (not argv) so large accumulated context
    never hits OS argument-length limits. Includes a timeout and simple
    retry with backoff for transient failures.
    """
    print("🤖 Communicating with Antigravity engine...")
    last_err = ""
    for attempt in range(1, LLM_RETRIES + 2):
        try:
            # Prefer piping the prompt via stdin so large accumulated context
            # never hits OS argv-length limits; fall back to the original
            # argument style if this agy version doesn't read stdin.
            result = subprocess.run(
                ["agy", "--print"],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=LLM_TIMEOUT_SECONDS,
            )
            if result.returncode != 0 or not result.stdout.strip():
                result = subprocess.run(
                    ["agy", "--print", prompt],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=LLM_TIMEOUT_SECONDS,
                )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            last_err = f"timed out after {LLM_TIMEOUT_SECONDS}s"
        except subprocess.CalledProcessError as e:
            last_err = (e.stderr or "").strip()
        except FileNotFoundError:
            print("❌ 'agy' command not found. Please ensure the Antigravity CLI is installed and in your PATH.", file=sys.stderr)
            sys.exit(1)
        if attempt <= LLM_RETRIES:
            wait = 2 ** attempt
            print(f"⚠️ LLM call failed ({last_err}). Retrying in {wait}s (attempt {attempt + 1}/{LLM_RETRIES + 1})...")
            time.sleep(wait)
    print(f"❌ Error communicating with agy CLI after {LLM_RETRIES + 1} attempts: {last_err}", file=sys.stderr)
    sys.exit(1)


def validate_output(text):
    """Sanity-checks a deliverable before it is accepted.

    Returns a list of problem descriptions (empty list = OK). Catches the
    real failure modes seen in earlier runs: truncated output, a document
    that restarts itself (duplicated H1), and placeholder filler names.
    """
    problems = []
    stripped = text.strip()
    if len(stripped) < 300:
        problems.append(f"output suspiciously short ({len(stripped)} chars)")
    # Duplicated document restart: the same H1 appearing more than once.
    h1s = [line.strip() for line in stripped.splitlines() if line.startswith("# ")]
    if len(h1s) != len(set(h1s)) and len(h1s) > 1:
        problems.append("document appears to restart itself (duplicate top-level heading)")
    lower = stripped.lower()
    for word in PLACEHOLDER_BLOCKLIST:
        if word in lower:
            problems.append(f"placeholder content detected: '{word}'")
    if stripped and stripped[-1] not in ".!?)`|:*-":
        problems.append("output may be truncated (ends mid-sentence)")
    return problems


def get_learnings():
    if os.path.exists(LEARNINGS_FILE):
        with open(LEARNINGS_FILE, "r") as f:
            return f.read()
    return "No custom learnings or sprint retro rules registered yet."


def get_carryover_context(sprint):
    """Returns key deliverables from PREVIOUS sprints so agents extend prior
    work instead of re-inventing it. This was the missing piece that made
    each sprint a parallel universe."""
    context = []
    for prev in range(1, sprint):
        for phase_name in CARRYOVER_PHASES:
            filepath = os.path.join(OUTPUT_DIR, f"sprint_{prev}", f"{phase_name}.md")
            if os.path.exists(filepath):
                with open(filepath, "r") as f:
                    context.append(f"### CARRY-OVER — Sprint {prev} {phase_name.upper()} (source of truth, extend, do not redefine):\n{f.read()}\n")
    return "\n".join(context)


def get_previous_deliverables(sprint, phase_index):
    """Gathers all markdown deliverables from earlier phases of THIS sprint."""
    context = []
    sprint_dir = os.path.join(OUTPUT_DIR, f"sprint_{sprint}")
    if not os.path.exists(sprint_dir):
        return ""
    for i in range(phase_index):
        phase_name = PHASES[i][0]
        filepath = os.path.join(sprint_dir, f"{phase_name}.md")
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                context.append(f"### Output of {phase_name.upper()} (this sprint):\n{f.read()}\n")
    return "\n".join(context)


def build_prompt(state, agent_name):
    system_instruction = PROMPTS[agent_name]
    learnings = get_learnings()
    carryover = get_carryover_context(state["sprint"])
    previous_outputs = get_previous_deliverables(state["sprint"], state["current_phase_index"])

    return f"""You are executing the role of: {agent_name.upper()}
SYSTEM INSTRUCTIONS:
{system_instruction}
{COMMON_RULES}
ACCUMULATED RULES & RETROSPECTIVE LEARNINGS TO FOLLOW:
{learnings}

CONTEXT:
Project Name: {state['project_name']}
Overall Vision: {state['vision']}
Current Sprint: {state['sprint']}

CARRY-OVER FROM PREVIOUS SPRINTS:
{carryover if carryover else "None — this is the first sprint."}

PREVIOUS DELIVERABLES FROM THIS SPRINT:
{previous_outputs if previous_outputs else "No previous phases run for this sprint yet."}

CRITICAL: Do NOT create any external artifacts, files, or links. Write your entire response directly in this output text. Your output will be written directly to a file by the system, so you must write the full detailed content here, not a summary. Do NOT write source code."""


def execute_phase(state, phase_index):
    """Runs one phase, validates the output, saves it. Returns True on success."""
    agent_name, phase_title = PHASES[phase_index]
    print(f"\n🚀 Running {phase_title}...")

    output_text = run_llm(build_prompt(state, agent_name))

    problems = validate_output(output_text)
    if problems:
        print("⚠️ Validation issues detected; regenerating once:")
        for p in problems:
            print(f"   - {p}")
        output_text = run_llm(build_prompt(state, agent_name))
        problems = validate_output(output_text)

    sprint_dir = os.path.join(OUTPUT_DIR, f"sprint_{state['sprint']}")
    os.makedirs(sprint_dir, exist_ok=True)
    filepath = os.path.join(sprint_dir, f"{agent_name}.md")
    with open(filepath, "w") as f:
        f.write(output_text)

    if problems:
        print("❌ Output still failed validation and was saved for inspection:")
        for p in problems:
            print(f"   - {p}")
        print(f"📄 See: {filepath}")
        print("   Fix or re-run with: python3 run_pipeline.py redo")
        return False

    print(f"✅ Deliverable written to: {filepath}")
    return True


def init_pipeline(args):
    state = load_state()
    state["project_name"] = args.name
    state["vision"] = args.vision
    state["sprint"] = 1
    state["current_phase_index"] = 0
    state["history"] = []
    save_state(state)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not os.path.exists(LEARNINGS_FILE):
        with open(LEARNINGS_FILE, "w") as f:
            f.write(
                "# Sprint Learnings & Agent Rules\n\n"
                "This file stores accumulated feedback and custom rules from retrospectives to guide the agents.\n\n"
                "## Global Rules\n"
                "- Maintain clear, professional markdown formatting.\n"
                "- Never output code snippets unless explicitly requested by a retrospective rule.\n"
            )

    print(f"✨ Project '{args.name}' initialized successfully!")
    print("Sprint: 1")
    print(f"Next phase: {PHASES[0][1]}")


def run_next_phase(args):
    state = load_state()
    if not state["project_name"]:
        print("❌ Pipeline not initialized. Run 'python3 run_pipeline.py init --name <name> --vision <vision>' first.")
        return

    idx = state["current_phase_index"]
    if idx >= len(PHASES):
        print(f"🎉 Sprint {state['sprint']} requirements are fully complete! Please run 'python3 run_pipeline.py retro' to provide feedback, improve the agents, and start the next sprint.")
        return

    if not execute_phase(state, idx):
        return  # do not advance past a failed deliverable

    state["current_phase_index"] += 1
    save_state(state)

    if state["current_phase_index"] < len(PHASES):
        _, next_title = PHASES[state["current_phase_index"]]
        print(f"➡️ Next phase up: {next_title}")
    else:
        print(f"🎉 Sprint {state['sprint']} requirements are complete! Compile final documents and run a sprint retro.")


def redo_phase(args):
    """Re-runs a phase of the current sprint without advancing the pipeline.
    Defaults to the most recently completed phase."""
    state = load_state()
    if not state["project_name"]:
        print("❌ Pipeline not initialized.")
        return

    if args.phase:
        names = [p[0] for p in PHASES]
        if args.phase not in names:
            print(f"❌ Unknown phase '{args.phase}'. Valid phases: {', '.join(names)}")
            return
        idx = names.index(args.phase)
    else:
        idx = min(state["current_phase_index"], len(PHASES)) - 1
        if idx < 0:
            print("❌ No phase has been run yet in this sprint.")
            return

    if idx > state["current_phase_index"]:
        print(f"❌ Phase '{PHASES[idx][0]}' has not been reached yet this sprint.")
        return

    # Temporarily point the context builder at the redo target.
    original_idx = state["current_phase_index"]
    state["current_phase_index"] = idx
    ok = execute_phase(state, idx)
    state["current_phase_index"] = max(original_idx, idx + 1 if ok else original_idx)
    save_state(state)
    if ok and idx < original_idx:
        print("ℹ️ Note: later phases of this sprint were generated from the OLD version of this deliverable. Consider redoing them too.")


def run_retro(args):
    state = load_state()
    if not state["project_name"]:
        print("❌ Pipeline not initialized.")
        return

    if state["current_phase_index"] < len(PHASES):
        print(f"⚠️ Sprint {state['sprint']} is not finished yet. Current phase is: {PHASES[state['current_phase_index']][1]}")
        confirm = input("Are you sure you want to run retro early? (y/N): ").strip().lower()
        if confirm != "y":
            return

    print(f"\n🔄 Running Retrospective for Sprint {state['sprint']}...")
    print(f'Your feedback: "{args.feedback}"')

    prompt = f"""You are a Scrum Master and Process Improver.
Your task is to take the user's retrospective feedback and translate it into clear, actionable rules for specific subagents in our PO Team.

The subagent roles are:
- market_researcher (Competitor Analysis)
- business_analyst (Personas, KPIs, Capabilities, Glossary)
- sprint_planner (Sprint scoping, MoSCoW)
- user_story_writer (Stories, Backlog)
- qa_writer (Given-When-Then Acceptance Criteria)
- technical_architect (Data models, API contracts, NFRs)
- po_orchestrator (PRD, Roadmap)

CURRENT FEEDBACK RECEIVED:
"{args.feedback}"

Here is the current content of the 'sprint_learnings.md' file:
{get_learnings()}

Please output an updated version of the 'sprint_learnings.md' file content, keeping ALL old rules that are still valid, but adding or amending rules based on the new feedback.
Only output the raw markdown content of the file. Do NOT include markdown wrappers (like ```markdown) or introductory chat."""

    updated_learnings = run_llm(prompt)

    # Safety: never let a bad generation wipe accumulated rules.
    if os.path.exists(LEARNINGS_FILE):
        backup = os.path.join(OUTPUT_DIR, f"sprint_learnings.backup_sprint{state['sprint']}.md")
        shutil.copyfile(LEARNINGS_FILE, backup)
        print(f"🗄  Previous learnings backed up to: {backup}")
    if len(updated_learnings.strip()) < 50:
        print("❌ Retro output looked empty/corrupt; keeping the existing learnings file unchanged.")
    else:
        with open(LEARNINGS_FILE, "w") as f:
            f.write(updated_learnings)
        print(f"✅ Learning memory updated in: {LEARNINGS_FILE}")

    state["history"].append({"sprint": state["sprint"], "feedback": args.feedback})
    state["sprint"] += 1
    state["current_phase_index"] = 0
    save_state(state)

    print(f"🚀 Sprint {state['sprint'] - 1} complete. Sprint {state['sprint']} is now active and will use the updated rules (and carry over the previous sprint's PRD + architecture as context)!")


def print_status(args):
    state = load_state()
    if not state["project_name"]:
        print("Pipeline Status: Not Initialized")
        return

    print("==========================================")
    print(f"📋 Project: {state['project_name']}")
    print(f"👁️  Vision: {state['vision']}")
    print(f"🏃 Sprint: {state['sprint']}")

    idx = state["current_phase_index"]
    if idx < len(PHASES):
        print(f"⚙️  Current Phase: {PHASES[idx][1]}")
    else:
        print(f"🎉 Current Phase: Completed Sprint {state['sprint']} (Pending Retro)")

    print("==========================================")
    print("📂 Deliverables:")
    if os.path.exists(OUTPUT_DIR):
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for file in sorted(files):
                rel_path = os.path.relpath(os.path.join(root, file), OUTPUT_DIR)
                print(f"  - {rel_path}")
    else:
        print("  (None generated yet)")
    print("==========================================")


def main():
    parser = argparse.ArgumentParser(description="Product Owner Team Requirements Pipeline")
    subparsers = parser.add_subparsers(dest="command")

    parser_init = subparsers.add_parser("init", help="Initialize a new project")
    parser_init.add_argument("--name", required=True, help="Name of the platform")
    parser_init.add_argument("--vision", required=True, help="High level vision of the platform")

    subparsers.add_parser("next", help="Run the next agent in the pipeline")

    parser_redo = subparsers.add_parser("redo", help="Re-run a phase of the current sprint (defaults to the last completed one)")
    parser_redo.add_argument("--phase", required=False, help="Phase name to re-run (e.g. technical_architect)")

    parser_retro = subparsers.add_parser("retro", help="Provide retro feedback to update agent rules")
    parser_retro.add_argument("--feedback", required=True, help="Retrospective feedback from the sprint review")

    subparsers.add_parser("status", help="Print pipeline status and generated deliverables")

    args = parser.parse_args()

    if args.command == "init":
        init_pipeline(args)
    elif args.command == "next":
        run_next_phase(args)
    elif args.command == "redo":
        redo_phase(args)
    elif args.command == "retro":
        run_retro(args)
    elif args.command == "status":
        print_status(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
