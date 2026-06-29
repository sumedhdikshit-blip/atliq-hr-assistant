from typing import Dict
from datetime import datetime
from hrms.schemas import LeaveApplyRequest
from hrms.db import get_connection

class LeaveManager:
    def __init__(self):
        pass

    def get_leave_balance(self, employee_id: str) -> str:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM leave_balances WHERE emp_id = ?", (employee_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return f"{employee_id} has {row['balance']} leave days remaining."
        return "Employee ID not found."

    def apply_leave(self, req: LeaveApplyRequest) -> str:
        employee_id = req.emp_id
        leave_dates = [d.isoformat() for d in req.leave_dates]
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT balance FROM leave_balances WHERE emp_id = ?", (employee_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return "Employee ID not found."
            
        requested = len(leave_dates)
        available = row["balance"]
        
        if available < requested:
            conn.close()
            return f"Insufficient leave balance: requested {requested}, available {available}."
            
        new_balance = available - requested
        cursor.execute("UPDATE leave_balances SET balance = ? WHERE emp_id = ?", (new_balance, employee_id))
        
        cursor.execute("SELECT MAX(request_id) as max_req FROM leave_history WHERE emp_id = ?", (employee_id,))
        req_row = cursor.fetchone()
        next_req_id = (req_row['max_req'] or 0) + 1
        
        for d in leave_dates:
            cursor.execute("INSERT INTO leave_history (emp_id, leave_date, request_id) VALUES (?, ?, ?)",
                           (employee_id, d, next_req_id))
                           
        conn.commit()
        conn.close()
        
        return (f"Leave applied for {requested} day(s). Remaining balance: "
                f"{new_balance}")

    def get_leave_history(self, employee_id: str) -> str:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM leave_balances WHERE emp_id = ?", (employee_id,))
        if not cursor.fetchone():
            conn.close()
            return "Employee ID not found."
            
        cursor.execute("SELECT leave_date FROM leave_history WHERE emp_id = ? ORDER BY leave_date ASC", (employee_id,))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return f"Leave history for {employee_id}: No leave records found."
            
        dates = [datetime.fromisoformat(row['leave_date']).strftime("%B %d, %Y") for row in rows]
        return f"Leave history for {employee_id}: {', '.join(dates)}."