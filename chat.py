import os
import json
import urllib.request
import sys
from dotenv import load_dotenv  

load_dotenv(r'D:\atliq-hr-assistant\.env')
from datetime import datetime
from colorama import init, Fore, Style
import server

init(autoreset=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

from groq import Groq
client = Groq(api_key=GROQ_API_KEY)

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

history = []

def call_groq(messages):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0
    )
    return response.choices[0].message.content.strip()

def execute_tool(tool_name, params):
    func = getattr(server, tool_name, None)
    if not func:
        raise ValueError(f"Tool {tool_name} not found in server.py")
    if hasattr(func, "__wrapped__"):
        func = func.__wrapped__
    return func(**params)

def suggest(tool_name):
    sugs = {
        "add_employee": ["onboard_employee", "send_welcome_email"],
        "create_ticket": ["list_tickets", "update_ticket_status"],
        "apply_leave": ["get_leave_history", "get_employee_leave_balance"]
    }
    return sugs.get(tool_name, [])

def clean_json(text):
    text = text.strip()
    if text.startswith("```json"): text = text[7:-3].strip()
    elif text.startswith("```"): text = text[3:-3].strip()
    return json.loads(text)

def chat_loop():
    global history
    print(f"{Fore.CYAN}HR Assistant Chat started. Type 'exit' or 'quit' to stop.")
    while True:
        try:
            user_in = input(f"\n{Fore.GREEN}You: {Style.RESET_ALL}").strip()
            if user_in.lower() in ('exit', 'quit'):
                break
            if not user_in: continue

            history.append({"role": "user", "content": f"User command: {user_in}. Current Time: {datetime.now().isoformat()}"})
            if len(history) > 10:
                del history[:-10]

            msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + history
            resp = call_groq(msgs)
            
            try:
                actions = clean_json(resp)
                if not isinstance(actions, list): actions = [actions]
            except Exception as e:
                print(f"{Fore.RED}Failed to parse LLM response: {resp}")
                continue

            history.append({"role": "assistant", "content": resp})

            for act in actions:
                tool, params = act.get("tool"), act.get("params", {})
                print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] Calling {tool}({params})...")
                
                success = False
                for attempt in range(3):
                    try:
                        res = execute_tool(tool, params)
                        print(f"{Fore.CYAN}Result: {res}")
                        success = True
                        sugs = suggest(tool)
                        if sugs: print(f"{Fore.MAGENTA}Suggestions: {', '.join(sugs)}")
                        break
                    except Exception as e:
                        print(f"{Fore.RED}Attempt {attempt+1} failed: {e}")
                        err_msgs = msgs + [{"role": "assistant", "content": json.dumps([act])},
                                         {"role": "user", "content": f"Tool call failed: {e}. Return fixed JSON array."}]
                        try:
                            resp2 = call_groq(err_msgs)
                            act = clean_json(resp2)[0]
                            tool, params = act.get("tool"), act.get("params", {})
                        except Exception:
                            pass
                
                if not success:
                    print(f"{Fore.RED}All retries failed for {tool}. Please try again with valid arguments.")
                    
            print(f"{Fore.BLUE}{'-'*40}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"{Fore.RED}Unexpected error: {e}")

if __name__ == "__main__":
    if not GROQ_API_KEY:
        print(f"{Fore.RED}Error: GROQ_API_KEY is not loaded properly.")
        print(f"{Fore.RED}Please check if the key exists in {dotenv_path}.")
        sys.exit(1)
    print(f"{Fore.GREEN}GROQ_API_KEY loaded successfully.")
    
    print(f"{Fore.CYAN}Testing Groq API connection...")
    try:
        client.models.list()
        print(f"{Fore.GREEN}Groq API connection test successful.")
    except Exception as e:
        print(f"{Fore.RED}Groq API test failed. Exact error: {e}")
        print(f"{Fore.RED}Exiting...")
        sys.exit(1)
        
    chat_loop()
