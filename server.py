from emails import EmailSender
from hrms import *
from typing import List, Dict, Optional
from mcp.server.fastmcp import FastMCP

import os
# load the env
from dotenv import load_dotenv
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '.env')))
from datetime import datetime, timedelta
from utils import seed_services

employee_manager = EmployeeManager()
meeting_manager = MeetingManager()
leave_manager = LeaveManager()
ticket_manager = TicketManager()

seed_services(employee_manager, leave_manager, meeting_manager, ticket_manager)

emailer = EmailSender(
    smtp_server="smtp.gmail.com",
    port=587,
    username=os.getenv("CB_EMAIL"),
    password=os.getenv("CB_EMAIL_PWD"),
    use_tls=True
)

mcp = FastMCP("hr-assist")

@mcp.tool()
def add_employee(emp_name:str, manager_id:str, email:str) -> str:
    """
    Add a new employee to the HRMS system.
    :param emp_name: Employee name
    :param manager_id: Manager ID (optional)
    :return: Confirmation message
    """
    emp = EmployeeCreate(
        emp_id=employee_manager.get_next_emp_id(),
        name=emp_name,
        manager_id=manager_id,
        email=email
    )
    employee_manager.add_employee(emp)
    return f"Employee {emp_name} added successfully."

@mcp.tool()
def get_employee_details(name: str) -> Dict[str, str]:
    """
    Get employee details by name.
    :param name: Name of the employee
    :return: Employee ID and manager ID
    """
    matches = employee_manager.search_employee_by_name(name)

    if len(matches) == 0:
        raise ValueError(f"No employees found with name {name}.")

    emp_id = matches[0]
    emp_details = employee_manager.get_employee_details(emp_id)
    return emp_details

@mcp.tool()
def send_email(to_emails: List[str], subject: str, body: str, html: bool = False) -> None:
    emailer.send_email(subject, body, to_emails, from_email=emailer.username, html=html)
    return "Email sent successfully."


@mcp.tool()
def create_ticket(emp_id: str, item: str, reason:str) -> str:
    """
    Create a ticket for buying required items for an employee.
    :param emp_id: Employee ID
    :param item: Item requested (Laptop, ID Card, etc.)
    :param reason: Reason for the request
    :return: Confirmation message
    """
    ticket_req = TicketCreate(emp_id=emp_id, item=item, reason=reason)
    return ticket_manager.create_ticket(ticket_req)

@mcp.tool()
def update_ticket_status(ticket_id: str, status: str) -> str:
    """
    Update the status of a ticket.
    :param ticket_id: Ticket ID
    :param status: New status of the ticket
    :return: Confirmation message
    """
    ticket_status_update = TicketStatusUpdate(status=status)
    return ticket_manager.update_ticket_status(ticket_status_update, ticket_id)

@mcp.tool()
def list_tickets(employee_id: str, status: str) -> str:
    """
    List tickets for an employee with optional status filter.
    :param employee_id: Employee ID
    :param status: Ticket status (optional)
    :return: List of tickets
    """
    return ticket_manager.list_tickets(employee_id=employee_id, status=status)


@mcp.tool()
def schedule_meeting(employee_id: str, meeting_datetime: datetime, topic: str) -> str:
    """
    Schedule a meeting for an employee.
    :param employee_id: Employee ID
    :param meeting_datetime: Date and time of the meeting in python datetime format
    :param topic: Topic of the meeting
    :return: Confirmation message
    """
    meeting_req = MeetingCreate(
        emp_id=employee_id,
        meeting_dt=meeting_datetime,
        topic=topic
    )
    return meeting_manager.schedule_meeting(meeting_req)


@mcp.tool()
def get_meetings(employee_id: str) -> str:
    """
    Get the list of meetings scheduled for an employee.
    :param employee_id: Employee ID
    :return: List of meetings
    """
    return meeting_manager.get_meetings(employee_id)


@mcp.tool()
def cancel_meeting(employee_id: str, meeting_datetime: datetime, topic: str) -> str:
    """
    Cancel a scheduled meeting for an employee.
    :param employee_id: Employee ID
    :param meeting_datetime: Date and time of the meeting in python datetime format
    :param topic: Topic of the meeting (optional)
    :return: Confirmation message
    """
    meeting_req = MeetingCancelRequest(
        emp_id=employee_id,
        meeting_dt=meeting_datetime,
        topic=topic
    )
    return meeting_manager.cancel_meeting(meeting_req)


@mcp.tool()
def get_employee_leave_balance(emp_id: str) -> str:
    """
    Get the leave balance of an employee.
    :param emp_id: Employee ID
    :return: Leave balance message
    """
    return leave_manager.get_leave_balance(emp_id)

@mcp.tool()
def apply_leave(emp_id: str, leave_dates: list) -> str:
    """
    Apply for leave for an employee.
    :param emp_id: Employee ID
    :param leave_dates: List of leave dates
    :return: Leave application status message
    """
    req = LeaveApplyRequest(emp_id=emp_id, leave_dates=leave_dates)
    return leave_manager.apply_leave(req)


@mcp.tool()
def get_leave_history(emp_id: str) -> str:
    """
    Get the leave history of an employee.
    :param emp_id: Employee ID
    :return: Leave history message
    """
    return leave_manager.get_leave_history(emp_id)


@mcp.tool()
def send_welcome_email(emp_id: str) -> str:
    emp = employee_manager.get_employee_details(emp_id)
    manager_str = employee_manager.get_manager(emp_id)
    html_body = f"<h1>Welcome to AtliQ, {emp['name']}!</h1><p>Your Employee ID is <b>{emp_id}</b>.</p><p>Your Manager is <b>{manager_str}</b>.</p><p>Company email format is first.last@atliq.com.</p>"
    emailer.send_email(f"Welcome to AtliQ, {emp['name']}!", html_body, [emp['email']], html=True)
    return f"Welcome email sent to {emp['name']}."

@mcp.tool()
def send_manager_notification(emp_id: str) -> str:
    emp = employee_manager.get_employee_details(emp_id)
    mgr_id = employee_manager.manager_map.get(emp_id)
    if not mgr_id:
        return "No manager to notify."
    mgr = employee_manager.get_employee_details(mgr_id)
    body = f"Hi {mgr['name']},\n\nNew team member {emp['name']} (ID: {emp_id}) has joined today.\n\nThanks,\nHR Team"
    emailer.send_email("New Team Member Joined", body, [mgr['email']])
    return f"Manager notification sent to {mgr['name']}."

@mcp.tool()
def send_ticket_update_email(ticket_id: str) -> str:
    t_details = next((t for t in ticket_manager.tickets if t["ticket_id"] == ticket_id), None)
    if not t_details:
        raise ValueError(f"Ticket {ticket_id} not found.")
    emp = employee_manager.get_employee_details(t_details["emp_id"])
    body = f"Your ticket {ticket_id} for '{t_details['item']}' is now {t_details['status']}."
    emailer.send_email(f"Ticket {ticket_id} Update", body, [emp['email']])
    return f"Ticket update email sent to {emp['name']}."

@mcp.tool()
def onboard_employee(emp_name: str, manager_id: str, email: str) -> str:
    summary = []
    try:
        emp_id = employee_manager.get_next_emp_id()
        add_employee(emp_name, manager_id, email)
        summary.append(f"Step 1: Added employee {emp_name} ({emp_id}) - SUCCESS")
    except Exception as e:
        summary.append(f"Step 1: Add employee - FAILED: {str(e)}")
        return "\n".join(summary)
        
    try:
        send_welcome_email(emp_id)
        summary.append("Step 2: Welcome email - SUCCESS")
    except Exception as e:
        summary.append(f"Step 2: Welcome email - FAILED: {str(e)}")
        
    try:
        send_manager_notification(emp_id)
        summary.append("Step 3: Manager notification - SUCCESS")
    except Exception as e:
        summary.append(f"Step 3: Manager notification - FAILED: {str(e)}")
        
    try:
        create_ticket(emp_id, "Laptop", "New hire onboarding")
        create_ticket(emp_id, "ID Card", "New hire onboarding")
        create_ticket(emp_id, "Access Card", "New hire onboarding")
        summary.append("Step 4: Created tickets - SUCCESS")
    except Exception as e:
        summary.append(f"Step 4: Created tickets - FAILED: {str(e)}")
        
    try:
        now = datetime.now()
        days_ahead = 1 if now.weekday() < 4 else (3 if now.weekday() == 4 else (2 if now.weekday() == 5 else 1))
        next_day = now + timedelta(days=days_ahead)
        meeting_dt = datetime(next_day.year, next_day.month, next_day.day, 10, 0)
        schedule_meeting(emp_id, meeting_dt, "Introductory Meeting")
        summary.append("Step 5: Scheduled intro meeting - SUCCESS")
    except Exception as e:
        summary.append(f"Step 5: Scheduled intro meeting - FAILED: {str(e)}")
        
    return "\n".join(summary)

@mcp.tool()
def get_ticket_details(ticket_id: str) -> dict:
    t_details = next((t for t in ticket_manager.tickets if t["ticket_id"] == ticket_id), None)
    if not t_details:
        raise ValueError(f"Ticket {ticket_id} not found.")
    return t_details

@mcp.tool()
def list_all_tickets(status: str = None) -> str:
    tickets = ticket_manager.list_tickets(status=status)
    if not tickets:
        return "No tickets found."
    from collections import defaultdict
    grouped = defaultdict(list)
    for t in tickets:
        grouped[t["emp_id"]].append(t)
    out = []
    for emp_id, emp_tickets in grouped.items():
        out.append(f"Employee {emp_id}:")
        for t in emp_tickets:
            out.append(f"  - {t['ticket_id']}: {t['item']} ({t['status']})")
    return "\n".join(out)

@mcp.tool()
def close_resolved_tickets(emp_id: str) -> str:
    tickets = ticket_manager.list_tickets(employee_id=emp_id, status="In Progress")
    closed = []
    for t in tickets:
        update_ticket_status(t["ticket_id"], "Closed")
        try:
            send_ticket_update_email(t["ticket_id"])
        except Exception:
            pass
        closed.append(t["ticket_id"])
    if not closed:
        return "No In Progress tickets found to close."
    return f"Closed {len(closed)} tickets for {emp_id}: {', '.join(closed)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
