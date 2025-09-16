#!/usr/bin/env python3
"""
Very simple TODO MCP Server: only add and list tasks
"""
import asyncio
import json
import sys
import os
import uuid

# File to store tasks
TODO_FILE = "tasks.json"

def load_tasks():
    if os.path.exists(TODO_FILE):
        try:
            with open(TODO_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_tasks(tasks):
    with open(TODO_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

async def add_task(description: str) -> str:
    tasks = load_tasks()
    task_id = str(uuid.uuid4())
    task = {"id": task_id, "description": description}
    tasks.append(task)
    save_tasks(tasks)
    return f"Task added with ID: {task_id}"

async def list_tasks() -> str:
    tasks = load_tasks()
    if not tasks:
        return "No tasks found"
    return "\n".join([f"{t['id']}: {t['description']}" for t in tasks])

# ----------------- MCP part -----------------
class MCPServer:
    def __init__(self):
        self.tools = {
            "add_task": {"function": add_task, "description": "Add a new task"},
            "list_tasks": {"function": list_tasks, "description": "List all tasks"}
        }

    async def handle_message(self, message):
        method = message.get("method")
        msg_id = message.get("id")

        if method == "initialize":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"serverInfo": {"name": "todo", "version": "1.0"}}}

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [{"name": n, "description": t["description"]} for n, t in self.tools.items()]
                }
            }

        elif method == "tools/call":
            name = message["params"]["name"]
            args = message["params"].get("arguments", {})
            if name in self.tools:
                result = await self.tools[name]["function"](**args)
                return {"jsonrpc": "2.0", "id": msg_id, "result": {"content": [{"type": "text", "text": result}]}}
            else:
                return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "Tool not found"}}

        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "Unknown method"}}

    async def run_stdio(self):
        while True:
            line = await asyncio.to_thread(sys.stdin.readline)
            if not line:
                break
            try:
                message = json.loads(line.strip())
                response = await self.handle_message(message)
                print(json.dumps(response), flush=True)
            except:
                continue

def main():
    asyncio.run(MCPServer().run_stdio())

if __name__ == "__main__":
    main()
