# D:\atliq-hr-assistant\dashboard_api.py
# Backend API supporting visual upgrades (CSV export, Light/Dark Mode, skeletons, counts)
import sqlite3
import os
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '.env')))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

from groq import Groq
client = Groq(api_key=GROQ_API_KEY)

import server  # to execute tools dynamically

app = FastAPI(title="HR Dashboard API")

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'hr_database.db'))

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_data(query: str, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def fetch_one(query: str, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

class LeaveBalanceRequest(BaseModel):
    emp_id: str
    balance: int

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, Any]]

SYSTEM_PROMPT = """You are an HR Assistant mapping natural language to tool calls.
Return ONLY a valid JSON array of objects, with no markdown formatting. Format:
[{"tool": "tool_name", "params": {"param_name": "value"}}]

Available tools:
- add_employee(emp_name, manager_id, email)
- get_employee_details(name)
- send_email(to_emails, subject, body, html)
- create_ticket(emp_id, item, reason)
- update_ticket_status(ticket_id, status)
- list_tickets(employee_id, status)
- schedule_meeting(employee_id, meeting_datetime, topic)
- get_meetings(employee_id)
- cancel_meeting(employee_id, meeting_datetime, topic)
- get_employee_leave_balance(emp_id)
- apply_leave(emp_id, leave_dates)
- get_leave_history(emp_id)
- send_welcome_email(emp_id)
- send_manager_notification(emp_id)
- send_ticket_update_email(ticket_id)
- onboard_employee(emp_name, manager_id, email)
- get_ticket_details(ticket_id)
- list_all_tickets(status)
- close_resolved_tickets(emp_id)

Note: For datetime parameters, use ISO format strings. leave_dates is a list of strings.
"""

def clean_json(text):
    text = text.strip()
    if text.startswith("```json"): text = text[7:-3].strip()
    elif text.startswith("```"): text = text[3:-3].strip()
    return json.loads(text)

def execute_tool(tool_name, params):
    func = getattr(server, tool_name, None)
    if not func:
        raise ValueError(f"Tool {tool_name} not found in server.py")
    if hasattr(func, "__wrapped__"):
        func = func.__wrapped__
    return func(**params)

@app.get("/api/employees")
def get_employees():
    return fetch_data("SELECT * FROM employees")

@app.get("/api/leave")
def get_leave():
    return fetch_data("SELECT * FROM leave_balances")

@app.get("/api/tickets")
def get_tickets():
    return fetch_data("SELECT * FROM tickets")

@app.get("/api/meetings")
def get_meetings():
    return fetch_data("SELECT * FROM meetings")

@app.get("/api/employee/{emp_id}/full")
def get_employee_full_details(emp_id: str):
    employee = fetch_one("SELECT * FROM employees WHERE emp_id = ?", (emp_id,))
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    leave_balance = fetch_one("SELECT balance FROM leave_balances WHERE emp_id = ?", (emp_id,))
    leave_history = fetch_data("SELECT * FROM leave_history WHERE emp_id = ? ORDER BY leave_date DESC", (emp_id,))
    tickets = fetch_data("SELECT * FROM tickets WHERE emp_id = ? ORDER BY created_at DESC", (emp_id,))
    meetings = fetch_data("SELECT * FROM meetings WHERE emp_id = ? ORDER BY date DESC", (emp_id,))
    
    return {
        "employee": employee,
        "leave_balance": leave_balance["balance"] if leave_balance else 0,
        "leave_history": leave_history,
        "tickets": tickets,
        "meetings": meetings
    }

@app.get("/api/stats")
def get_stats():
    total_emp = fetch_one("SELECT COUNT(*) as count FROM employees")['count']
    open_tickets = fetch_one("SELECT COUNT(*) as count FROM tickets WHERE status='Open'")['count']
    
    # Meetings today
    today_str = datetime.now().strftime('%Y-%m-%d')
    meetings_today = fetch_one("SELECT COUNT(*) as count FROM meetings WHERE date LIKE ?", (f"{today_str}%",))['count']
    
    total_leave = fetch_one("SELECT SUM(balance) as sum FROM leave_balances")['sum'] or 0
    
    return {
        "total_employees": total_emp,
        "open_tickets": open_tickets,
        "meetings_today": meetings_today,
        "total_leave_days": total_leave
    }

@app.post("/api/leave/add")
def add_leave(req: LeaveBalanceRequest):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO leave_balances (emp_id, balance) VALUES (?, ?)", (req.emp_id, req.balance))
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"Added {req.balance} days for {req.emp_id}"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail=f"Balance for {req.emp_id} already exists!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    history = req.history
    user_msg = req.message
    
    history.append({"role": "user", "content": f"User command: {user_msg}. Current Time: {datetime.now().isoformat()}"})
    
    if len(history) > 10:
        history = history[-10:]
        
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=msgs,
            temperature=0
        )
        resp_content = response.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq API error: {str(e)}")
        
    try:
        actions = clean_json(resp_content)
        if not isinstance(actions, list): 
            actions = [actions]
    except Exception as e:
        # Not a JSON action, treat as direct conversational assistant reply
        history.append({"role": "assistant", "content": resp_content})
        return {"result": resp_content, "history": history, "actions": []}

    # If actions list is empty, treat as direct conversational reply
    if not actions:
        history.append({"role": "assistant", "content": resp_content})
        return {"result": resp_content, "history": history, "actions": []}

    # Add the JSON tool call command to history
    history.append({"role": "assistant", "content": resp_content})

    results = []
    actions_run = []
    for act in actions:
        tool, params = act.get("tool"), act.get("params", {})
        try:
            res = execute_tool(tool, params)
            results.append(f"Tool {tool} output:\n{res}")
            actions_run.append({"tool": tool, "params": params, "status": "success", "result": str(res)})
        except Exception as e:
            results.append(f"Tool {tool} failed:\n{str(e)}")
            actions_run.append({"tool": tool, "params": params, "status": "error", "result": str(e)})
            
    final_output = "\n\n".join(results)
    history.append({"role": "system", "content": f"Execution result: {final_output}"})
    
    # Second LLM call for a conversational summary of execution results
    system_summary_prompt = "You are a helpful HR Assistant. Provide a brief, friendly, natural language summary of the actions taken and their results. Do not output JSON or code snippets unless necessary."
    msgs_summary = [{"role": "system", "content": system_summary_prompt}] + history
    
    try:
        summary_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=msgs_summary,
            temperature=0.3
        )
        final_reply = summary_response.choices[0].message.content.strip()
    except Exception as e:
        final_reply = f"I have executed the requested actions. Here is the output:\n{final_output}"
        
    history.append({"role": "assistant", "content": final_reply})
    return {"result": final_reply, "history": history, "actions": actions_run}

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    html_path = os.path.join(os.path.dirname(__file__), 'dashboard.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        return f.read()
