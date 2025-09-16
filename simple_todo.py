#!/usr/bin/env python3
"""
Very simple TODO MCP Server with MongoDB storage
"""
import asyncio
import json
import sys
from datetime import datetime
import uuid
from pymongo import MongoClient

# ----------------- MongoDB Setup -----------------
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "todo_db"
COLLECTION = "tasks"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
tasks_col = db[COLLECTION]

# ----------------- Task Functions -----------------
async def add_task(description: str) -> str:
    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "description": description,
        "status": "todo",
        "created_at": datetime.now().isoformat()
    }
    tasks_col.insert_one(task)
    return f"Task added with ID: {task_id}"

async def list_tasks() -> str:
    tasks = list(tasks_col.find())
    if not tasks:
        return "No tasks found"
    return "\n".join([f"{t['id']}: {t['description']} ({t.get('status','todo')})" for t in tasks])

# ----------------- MCP Server -----------------
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
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "serverInfo": {"name": "todo", "version": "1.0"}
                }
            }

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
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": result}]}
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": "Tool not found"}
                }

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": "Unknown method"}
        }

    async def run_stdio(self):
        print("TODO MCP Server with MongoDB starting...", file=sys.stderr)
        sys.stderr.flush()
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
