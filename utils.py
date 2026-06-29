from typing import Dict, List, Optional
from collections import defaultdict
from datetime import date, datetime, timedelta
import random
from hrms import *
from hrms.db import get_connection

def seed_services(employee_manager, leave_manager, meeting_manager, ticket_manager):
    """
    Seeds all service classes with coherent dummy data in SQLite database.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if we need to seed
    cursor.execute("SELECT COUNT(*) as count FROM employees")
    if cursor.fetchone()['count'] > 0:
        conn.close()
        return {"employees": 0, "leave_records": 0, "meetings": 0, "tickets": 0}

    employees_data = [
        {"emp_id": "E001", "name": "Sarah Johnson", "manager_id": None, "email": "sarah.johnson@atliq.com"},
        {"emp_id": "E002", "name": "Michael Chen", "manager_id": None, "email": "michael.chen@atliq.com"},
        {"emp_id": "E003", "name": "David Wilson", "manager_id": "E001", "email": "david.wilson@atliq.com"},
        {"emp_id": "E004", "name": "Tony Sharma", "manager_id": "E003", "email": "tony.sharma@atliq.com"},
        {"emp_id": "E005", "name": "James Rodriguez", "manager_id": "E003", "email": "james.rodriguez@atliq.com"},
        {"emp_id": "E006", "name": "Emily Kim", "manager_id": "E002", "email": "emily.kim@atliq.com"},
        {"emp_id": "E007", "name": "Carlos Mendez", "manager_id": "E006", "email": "carlos.mendez@atliq.com"},
        {"emp_id": "E008", "name": "Lisa Wong", "manager_id": "E006", "email": "lisa.wong@atliq.com"},
    ]

    for employee in employees_data:
        cursor.execute("INSERT INTO employees (emp_id, name, manager_id, email) VALUES (?, ?, ?, ?)",
                       (employee["emp_id"], employee["name"], employee["manager_id"], employee["email"]))

    current_date = date.today()
    request_id_counter = 1
    leave_records = 0

    for employee in employees_data:
        emp_id = employee["emp_id"]
        balance = random.randint(5, 20)
        cursor.execute("INSERT INTO leave_balances (emp_id, balance) VALUES (?, ?)", (emp_id, balance))

        num_leaves = random.randint(1, 5)
        for i in range(num_leaves):
            days_ago = random.randint(1, 90)
            leave_date = current_date - timedelta(days=days_ago)
            
            cursor.execute("INSERT INTO leave_history (emp_id, leave_date, request_id) VALUES (?, ?, ?)",
                           (emp_id, leave_date.isoformat(), request_id_counter))
            leave_records += 1

            if random.random() > 0.7:
                for j in range(1, random.randint(2, 5)):
                    consecutive_date = leave_date + timedelta(days=j)
                    cursor.execute("INSERT INTO leave_history (emp_id, leave_date, request_id) VALUES (?, ?, ?)",
                                   (emp_id, consecutive_date.isoformat(), request_id_counter))
                    leave_records += 1
            request_id_counter += 1

    meeting_types = ["Team Sync", "Project Review", "Client Meeting", "1:1", "Planning"]
    meeting_records = 0
    
    for employee in employees_data:
        emp_id = employee["emp_id"]
        num_meetings = random.randint(2, 6)

        for i in range(num_meetings):
            meeting_date = current_date + timedelta(days=random.randint(0, 10))
            meeting_hour = random.randint(9, 16)
            iso_dt = f"{meeting_date.strftime('%Y-%m-%d')}T{meeting_hour:02d}:00:00"
            topic = random.choice(meeting_types)
            
            cursor.execute("INSERT INTO meetings (emp_id, date, topic) VALUES (?, ?, ?)",
                           (emp_id, iso_dt, topic))
            meeting_records += 1

    ticket_items = ["Laptop", "Monitor", "Keyboard", "Mouse", "Headset", "Office Chair", "Software License"]
    ticket_reasons = ["New hire setup", "Replacement for broken item", "Upgrade request", "Project requirement", "Ergonomic needs"]
    
    num_tickets = random.randint(8, 15)
    for i in range(num_tickets):
        employee = random.choice(employees_data)
        ticket_id = f"T{i+1:04d}"
        item = random.choice(ticket_items)
        reason = random.choice(ticket_reasons)
        status = random.choice(["Open", "In Progress", "Closed"])
        dt_str = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO tickets (ticket_id, emp_id, item, reason, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (ticket_id, employee["emp_id"], item, reason, status, dt_str, dt_str))

    conn.commit()
    conn.close()

    return {
        "employees": len(employees_data),
        "leave_records": leave_records,
        "meetings": meeting_records,
        "tickets": num_tickets
    }

if __name__ == "__main__":
    employee_manager = EmployeeManager()
    leave_manager = LeaveManager()
    meeting_manager = MeetingManager()
    ticket_manager = TicketManager()

    result = seed_services(employee_manager, leave_manager, meeting_manager, ticket_manager)

    print(f"Seeded {result['employees']} employees")
    print(f"Seeded {result['leave_records']} leave records")
    print(f"Seeded {result['meetings']} meetings")
    print(f"Seeded {result['tickets']} tickets")
