#!/usr/bin/env python3
"""
Simple TODO MCP Client with Gemini integration
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
        You are a TODO assistant. User says: "{query}".
        Decide:
        - If it's about adding a task, output: ADD <task description>
        - If it's about listing tasks, output: LIST
        - Otherwise, just reply with plain text.
        """
        response = self.model.generate_content(prompt)
        answer = response.text.strip()

        if answer.startswith("ADD "):
            task = answer[4:]
            return await self.call_tool("add_task", {"description": task})
        elif answer.startswith("LIST"):
            return await self.call_tool("list_tasks")
        else:
            return answer

    async def repl(self):
        print("Simple TODO Client with Gemini")
        print("Type natural language (e.g., 'remind me to buy milk', 'show my tasks')")
        print("Or type 'quit' to exit")
        while True:
            query = input("todo> ").strip()
            if query == "quit":
                self.server.terminate()
                break
            result = await self.gemini_interpret(query)
            print(result)

async def main():
    client = TodoClient()
    await client.connect([sys.executable, "simple_todo.py"])
    await client.repl()

if __name__ == "__main__":
    asyncio.run(main())
