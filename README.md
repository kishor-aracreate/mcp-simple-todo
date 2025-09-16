# ✅ MCP TODO App with MongoDB + Gemini

A simple **Task Manager** built on **Model Context Protocol (MCP)**.
It supports:

* Adding tasks
* Listing tasks (all or by status: `todo`, `in_progress`, `done`)
* Deleting tasks (by ID, description, or interactive choice)
* Updating task status (`mark_in_progress`, `mark_done`)
* **Natural language control** with Google **Gemini** AI

---

## ⚡ Features

* Store tasks in **MongoDB** (`todo_db.tasks`)
* Command-based client **or** free-text input interpreted by Gemini
* Delete tasks smartly (by ID, description, or choose from numbered list)
* Natural language like:

  * `"remind me to buy milk"` → add task
  * `"show my tasks"` → list tasks
  * `"start homework"` → mark task in progress
  * `"finish report"` → mark task done
  * `"remove buy milk"` → delete task

---

## 📦 Installation

1. **Clone repo** (or copy files):

   ```bash
   git clone <your-repo-url>
   cd mcp-simple-todo
   ```

2. **Create virtual environment**:

   ```bash
   python -m venv env
   source env/bin/activate     # Linux / Mac
   env\Scripts\activate        # Windows
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:

   ```bash
   pip install pymongo google-generativeai
   ```

4. **Setup MongoDB**:

   * Install & run MongoDB locally (default: `mongodb://localhost:27017`)
   * It will create a database `todo_db` and collection `tasks` automatically.

5. **Set Gemini API key**:
   Get an API key from [Google AI Studio](https://aistudio.google.com/)

   ```bash
   export GEMINI_API_KEY="your_api_key_here"   # Linux / Mac
   setx GEMINI_API_KEY "your_api_key_here"     # Windows PowerShell
   ```

---

## ▶️ Running

Start the **server**:

```bash
python simple_todo.py
```

Then start the **client**:

```bash
python client.py
```

---

## 🖥️ Usage

You’ll see a REPL like this:

```
TODO Client with Gemini
Commands:
  add <task>
  list [status]
  delete <task_id or description>
  mark_in_progress <task_id>
  mark_done <task_id>
  quit
Natural language supported (e.g., 'start homework', 'finish report').
```

### Examples

#### Add tasks

```
todo> add Buy groceries
Task added with ID: 1234-abcd...

todo> remind me to finish homework   # Natural language
Task added with ID: 5678-efgh...
```

#### List tasks

```
todo> list
1234-abcd: Buy groceries (todo)
5678-efgh: finish homework (todo)

todo> list todo
todo> list in_progress
todo> list done
```

#### Update status

```
todo> mark_in_progress 1234-abcd
Task 1234-abcd marked as in progress

todo> start homework   # Natural language
Task 5678-efgh marked as in progress

todo> finish homework
Task 5678-efgh marked as done
```

#### Delete tasks

```
todo> delete 1234-abcd
Task 1234-abcd deleted successfully

todo> delete homework   # Natural language
Which task do you want to delete?
1. finish homework (done)
Enter the number of the task to delete:
todo> 1
Task 5678-efgh deleted successfully
```

---

## 📂 Project Structure

```
mcp-simple-todo/
│── client.py         # Client with Gemini + REPL
│── todo.py           # MCP server with MongoDB
│── requirements.txt  # Python dependencies
│── README.md         # Documentation
```

---

## ✅ Requirements

* Python 3.9+
* MongoDB running locally (`mongodb://localhost:27017`)
* Google Gemini API key
