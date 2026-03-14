#!/usr/bin/env python3
"""
Playwright-CLI Agent
Give it plain English instructions → it drives the browser using playwright-cli.

Usage:
  python pw_agent.py "Log into github.com with user@email.com and password abc123"
  python pw_agent.py instructions.txt

Setup:
  npm install -g @playwright/cli@latest
  pip install anthropic
  export ANTHROPIC_API_KEY=your_key
"""

import os
import sys
import subprocess
import anthropic
from dotenv import load_dotenv


SKILL = """
# Browser Automation with playwright-cli

## Core workflow
1. Navigate: `playwright-cli open https://example.com`
2. Run `playwright-cli snapshot` to see the page and element refs (e1, e2, ...)
3. Interact using those refs
4. Re-snapshot after changes to get updated refs

## Commands

### Navigation
playwright-cli open <url>
playwright-cli go-back
playwright-cli go-forward
playwright-cli reload
playwright-cli close

### Interaction
playwright-cli snapshot                    # see page + element refs
playwright-cli click <ref>                 # e.g. playwright-cli click e5
playwright-cli fill <ref> "<text>"         # fill input field
playwright-cli type "<text>"               # type into focused element
playwright-cli press <Key>                 # e.g. Enter, Tab, ArrowDown
playwright-cli check <ref>
playwright-cli uncheck <ref>
playwright-cli select <ref> "<value>"
playwright-cli hover <ref>
playwright-cli dblclick <ref>

### Output
playwright-cli screenshot                  # saves screenshot
playwright-cli pdf                         # saves PDF
playwright-cli eval "document.title"       # run JS
playwright-cli console                     # show console logs
playwright-cli network                     # show network requests

### Tabs
playwright-cli tab-new <url>
playwright-cli tab-list
playwright-cli tab-select <index>
playwright-cli tab-close
"""

SYSTEM = f"""You are a browser automation agent. The user gives you plain English instructions.
You execute them step by step using playwright-cli commands.

{SKILL}

Rules:
- Always start with `playwright-cli open <url> --headed` then `playwright-cli snapshot`
- Use snapshot output to find element refs before clicking/filling
- Re-snapshot after page changes to get fresh refs
- Print a brief note before each command explaining what you're doing
- When done, summarize what was accomplished
"""

tools = [{
    "name": "run",
    "description": "Run a playwright-cli shell command and return its output",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The playwright-cli command to run"},
            "reason": {"type": "string", "description": "What this command does"}
        },
        "required": ["command", "reason"]
    }
}]

def run(command: str) -> str:
    print(f"\n  $ {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip()
    if output:
        # Truncate very long snapshots to avoid flooding context
        if len(output) > 3000:
            output = output[:3000] + "\n... (truncated)"
        print(f"  {output}")
    return output or "(no output)"

def run_agent(instructions: str):
    load_dotenv()
    print(f"\nTask: {instructions}\n{'─'*50}")
    api_key_from_env = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key_from_env)
    messages = [{"role": "user", "content": instructions}]

    while True:
        response = client.messages.create(model="claude-opus-4-6",max_tokens=4096,
            system=SYSTEM,tools=tools,messages=messages
        )

        for block in response.content:
            if hasattr(block, "text") and block.text:
                print(f"\nAgent: {block.text}")

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"\n→ {block.input.get('reason', '')}")
                    output = run(block.input["command"])
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    print(f"\n{'─'*50}\nDone.")


def read_from_file(file_name):
    try:
        with open(file_name, "r") as file:
            content = file.read()
            print(content)
            return content
    except FileNotFoundError:
        print("Error: The file 'my_file.txt' was not found.")


def main():
    file_name = "testdescription1.txt"
    test_description = read_from_file(file_name)
    print("Testing")
    instructions = ("Go to bet365 nba and get me the over/under.Fee free to take screen shot to evalueat")
    run_agent(test_description)




if __name__ == "__main__":
    main()




