from typing import List, Dict
from datetime import datetime
from hrms.schemas import MeetingCreate, MeetingCancelRequest
from hrms.db import get_connection

class MeetingManager:
    def __init__(self):
        pass

    def schedule_meeting(self, req: MeetingCreate) -> str:
        dt_str = req.meeting_dt.isoformat()
        try:
            datetime.fromisoformat(dt_str)
        except ValueError:
            raise ValueError("Invalid datetime format; use ISO format.")
        emp_id = req.emp_id
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM meetings WHERE emp_id = ? AND date = ?", (emp_id, dt_str))
        if cursor.fetchone():
            conn.close()
            raise ValueError(f"Conflict: {emp_id} already has a meeting at {dt_str}.")
            
        cursor.execute("INSERT INTO meetings (emp_id, date, topic) VALUES (?, ?, ?)", 
                      (emp_id, dt_str, req.topic))
        conn.commit()
        conn.close()
        
        return f"Meeting scheduled for {emp_id} on {dt_str} about '{req.topic}'."

    def get_meetings(self, employee_id: str) -> List[Dict[str, str]]:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT date, topic FROM meetings WHERE emp_id = ? ORDER BY date ASC", (employee_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [{"date": r["date"], "topic": r["topic"]} for r in rows]

    def cancel_meeting(self, req: MeetingCancelRequest) -> str:
        emp_id = req.emp_id
        dt_str = req.meeting_dt.isoformat()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        query = "DELETE FROM meetings WHERE emp_id = ? AND date = ?"
        params = [emp_id, dt_str]
        
        if req.topic:
            query += " AND topic = ?"
            params.append(req.topic)
            
        cursor.execute(query, params)
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted == 0:
            raise ValueError("No matching meeting to cancel.")
            
        return f"Canceled meeting for {emp_id} on {dt_str}{f' about {req.topic}' if req.topic else ''}."