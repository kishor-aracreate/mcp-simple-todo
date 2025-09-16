#!/usr/bin/env python3
"""
Very simple TODO MCP Client: only add and list tasks
"""
import asyncio
import json
import subprocess
import sys

class TodoClient:
    def __init__(self):
        self.server = None
        self.msg_id = 1

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
        # initialize
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

    async def repl(self):
        print("Simple TODO Client")
        print("Commands:\n  add <task>\n  list\n  quit")
        while True:
            cmd = input("todo> ").strip()
            if cmd == "quit":
                self.server.terminate()
                break
            elif cmd.startswith("add task"):
                task = cmd[9:]
                result = await self.call_tool("add_task", {"description": task})
                print(result)
            elif cmd.startswith("list "):
                result = await self.call_tool("list_tasks")
                print(result)
            else:
                print("Unknown command")

async def main():
    client = TodoClient()
    await client.connect([sys.executable, "simple_todo.py"])
    await client.repl()

if __name__ == "__main__":
    asyncio.run(main())
