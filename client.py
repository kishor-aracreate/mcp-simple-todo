#!/usr/bin/env python3
"""
TODO MCP Client with Gemini integration
Supports: add_task, list_tasks, delete_task, mark_in_progress, mark_done
Smart handling:
- Delete by ID, description, or interactive choice
- Natural language for statuses: in progress, done
"""
import asyncio
import json
import subprocess
import sys
import os
import google.generativeai as genai

class TodoClient:
    def __init__(self, model_name="gemini-1.5-flash"):
        self.server = None
        self.msg_id = 1
        self.pending_delete_map = None  # maps number -> task_id

        # Setup Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Error: Please set GEMINI_API_KEY")
            sys.exit(1)
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def _next_id(self):
        self.msg_id += 1
        return self.msg_id

    async def connect(self, command):
        self.server = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        init_msg = {"jsonrpc": "2.0", "id": self._next_id(), "method": "initialize"}
        await self.send(init_msg)

    async def send(self, message):
        self.server.stdin.write(json.dumps(message) + "\n")
        self.server.stdin.flush()
        response = self.server.stdout.readline().strip()
        if response:
            return json.loads(response)

    async def call_tool(self, name, args=None):
        msg = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": name, "arguments": args or {}}
        }
        response = await self.send(msg)
        if "result" in response:
            return response["result"]["content"][0]["text"]
        return response

    async def gemini_interpret(self, query: str):
        """Send query to Gemini and decide what tool to call"""
        prompt = f"""
        You are a TODO assistant. The user says: "{query}".
        Decide the action:
        - If it's about adding a task → output: ADD <task description>
        - If it's about listing tasks → output: LIST [status]
        - If it's about deleting a task → output: DELETE <task_id or description or blank>
        - If it's about marking in progress → output: INPROGRESS <task_id or description>
        - If it's about marking done → output: DONE <task_id or description>
        - Otherwise, reply with plain text.
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()

    async def handle_delete_without_id(self, description_hint=None):
        """Interactive delete with numbers if no ID"""
        tasks_text = await self.call_tool("list_tasks")
        if tasks_text == "No tasks found":
            print("No tasks available to delete.")
            return

        tasks = tasks_text.splitlines()
        matched_tasks = []

        if description_hint:
            for line in tasks:
                task_id, rest = line.split(":", 1)
                if description_hint.lower() in rest.lower():
                    matched_tasks.append((task_id.strip(), rest.strip()))

        if description_hint and len(matched_tasks) == 1:
            task_id, rest = matched_tasks[0]
            result = await self.call_tool("delete_task", {"task_id": task_id})
            print(result)
            return

        if description_hint and len(matched_tasks) == 0:
            print(f"No task found matching '{description_hint}'")
            return

        if description_hint and len(matched_tasks) > 1:
            print(f"Multiple tasks match '{description_hint}':")
            tasks = [f"{tid}: {desc}" for tid, desc in matched_tasks]

        self.pending_delete_map = {}
        print("Which task do you want to delete?")
        for idx, line in enumerate(tasks, start=1):
            task_id, rest = line.split(":", 1)
            self.pending_delete_map[str(idx)] = task_id.strip()
            print(f"{idx}. {rest.strip()}")
        print("Enter the number of the task to delete:")

    async def handle_status_update(self, action: str, description_hint: str, tool_name: str):
        """Mark tasks in_progress or done"""
        tasks_text = await self.call_tool("list_tasks")
        if tasks_text == "No tasks found":
            print("No tasks available.")
            return

        tasks = tasks_text.splitlines()
        matched_tasks = []
        for line in tasks:
            task_id, rest = line.split(":", 1)
            if description_hint.lower() in rest.lower():
                matched_tasks.append((task_id.strip(), rest.strip()))

        if len(matched_tasks) == 1:
            task_id, rest = matched_tasks[0]
            result = await self.call_tool(tool_name, {"task_id": task_id})
            print(result)
        elif len(matched_tasks) > 1:
            print(f"Multiple tasks match '{description_hint}':")
            for idx, (tid, desc) in enumerate(matched_tasks, start=1):
                print(f"{idx}. {desc}")
            print("Please refine your request.")
        else:
            print(f"No task found matching '{description_hint}'")

    async def repl(self):
        print("TODO Client with Gemini")
        print("Commands:")
        print("  add <task>")
        print("  list [status]")
        print("  delete <task_id or description>")
        print("  mark_in_progress <task_id>")
        print("  mark_done <task_id>")
        print("  quit")
        print("Natural language supported (e.g., 'start homework', 'finish report').")
        while True:
            query = input("todo> ").strip()
            if query == "quit":
                self.server.terminate()
                break

            if self.pending_delete_map:
                choice = query.strip()
                if choice in self.pending_delete_map:
                    task_id = self.pending_delete_map[choice]
                    result = await self.call_tool("delete_task", {"task_id": task_id})
                    print(result)
                else:
                    print("Invalid choice.")
                self.pending_delete_map = None
                continue

            # Direct commands
            if query.startswith("add "):
                task = query[4:]
                result = await self.call_tool("add_task", {"description": task})
                print(result)

            elif query.startswith("list"):
                parts = query.split()
                status = parts[1] if len(parts) > 1 else None
                args = {"status": status} if status else {}
                result = await self.call_tool("list_tasks", args)
                print(result)

            elif query.startswith("delete "):
                arg = query.split(" ", 1)[1]
                if len(arg) > 20:  # UUID
                    result = await self.call_tool("delete_task", {"task_id": arg})
                    print(result)
                else:
                    await self.handle_delete_without_id(description_hint=arg)

            elif query.startswith("mark_in_progress "):
                task_id = query.split(" ", 1)[1]
                result = await self.call_tool("mark_in_progress", {"task_id": task_id})
                print(result)

            elif query.startswith("mark_done "):
                task_id = query.split(" ", 1)[1]
                result = await self.call_tool("mark_done", {"task_id": task_id})
                print(result)

            else:
                # Natural language via Gemini
                action = await self.gemini_interpret(query)

                if action.startswith("ADD "):
                    task = action[4:]
                    result = await self.call_tool("add_task", {"description": task})
                    print(result)

                elif action.startswith("LIST"):
                    parts = action.split(" ", 1)
                    status = parts[1] if len(parts) > 1 else None
                    args = {"status": status} if status else {}
                    result = await self.call_tool("list_tasks", args)
                    print(result)

                elif action.startswith("DELETE"):
                    parts = action.split(" ", 1)
                    if len(parts) == 2 and parts[1]:
                        arg = parts[1]
                        if len(arg) > 20:  # UUID
                            result = await self.call_tool("delete_task", {"task_id": arg})
                            print(result)
                        else:
                            await self.handle_delete_without_id(description_hint=arg)
                    else:
                        await self.handle_delete_without_id()

                elif action.startswith("INPROGRESS "):
                    desc = action.split(" ", 1)[1]
                    await self.handle_status_update("in progress", desc, "mark_in_progress")

                elif action.startswith("DONE "):
                    desc = action.split(" ", 1)[1]
                    await self.handle_status_update("done", desc, "mark_done")

                else:
                    print(action)

async def main():
    client = TodoClient()
    await client.connect([sys.executable, "todo.py"])
    await client.repl()

if __name__ == "__main__":
    asyncio.run(main())
