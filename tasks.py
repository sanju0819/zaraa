import json
import os

TASK_FILE = "data/tasks.json"
if not os.path.exists(TASK_FILE):
    with open(TASK_FILE, "w") as f:
        json.dump([], f)

def add_task(task):
    tasks = list_tasks()
    tasks.append({"task": task, "done": False})
    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def list_tasks():
    with open(TASK_FILE, "r") as f:
        return json.load(f)
