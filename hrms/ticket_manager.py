from typing import List, Dict, Optional
from datetime import datetime
from hrms.schemas import TicketCreate, TicketStatusUpdate
from hrms.db import get_connection

class TicketManager:
    def __init__(self):
        pass
        
    @property
    def tickets(self) -> List[Dict[str, str]]:
        return self.list_tickets()

    def create_ticket(self, req: TicketCreate) -> str:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM tickets")
        row = cursor.fetchone()
        next_id = row['count'] + 1
        ticket_id = f"T{next_id:04d}"
        
        created_at = datetime.utcnow().isoformat()
        
        cursor.execute('''
            INSERT INTO tickets (ticket_id, emp_id, item, reason, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (ticket_id, req.emp_id, req.item, req.reason, "Open", created_at, created_at))
        
        conn.commit()
        conn.close()
        return f"Ticket {ticket_id} created for {req.emp_id}."

    def update_ticket_status(self, req: TicketStatusUpdate, ticket_id: str) -> str:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM tickets WHERE ticket_id = ?", (ticket_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Ticket '{ticket_id}' not found.")
            
        updated_at = datetime.utcnow().isoformat()
        cursor.execute("UPDATE tickets SET status = ?, updated_at = ? WHERE ticket_id = ?", 
                      (req.status, updated_at, ticket_id))
                      
        conn.commit()
        conn.close()
        return f"Ticket {ticket_id} status updated to {req.status}."

    def list_tickets(
            self,
            employee_id: Optional[str] = None,
            status: Optional[str] = None
    ) -> List[Dict[str, str]]:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM tickets WHERE 1=1"
        params = []
        
        if employee_id:
            query += " AND emp_id = ?"
            params.append(employee_id)
        if status and status.lower() != 'all':
            query += " AND LOWER(status) = ?"
            params.append(status.lower())
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(r) for r in rows]
