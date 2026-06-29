from typing import List, Dict, Optional
from difflib import get_close_matches
from hrms.schemas import EmployeeCreate
from hrms.db import get_connection

class ManagerMapDict:
    def get(self, emp_id: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT manager_id FROM employees WHERE emp_id = ?", (emp_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row['manager_id']
        return None

class EmployeeManager:
    def __init__(self):
        self.manager_map = ManagerMapDict()

    def get_next_emp_id(self) -> str:
        """
        Generate the next employee ID based on the existing IDs.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT emp_id FROM employees")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "E001"
        max_id = max(int(row['emp_id'][1:]) for row in rows)
        return f"E{max_id + 1:03}"

    def add_employee(self, emp: EmployeeCreate) -> None:
        """
        Add a new employee via Pydantic model.
        Raises ValueError if emp_id exists or manager_id is invalid.
        """
        name, manager_id = emp.name, emp.manager_id
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM employees WHERE emp_id = ?", (emp.emp_id,))
        if cursor.fetchone():
            conn.close()
            raise ValueError(f"Employee ID '{emp.emp_id}' already exists.")
            
        if manager_id:
            cursor.execute("SELECT 1 FROM employees WHERE emp_id = ?", (manager_id,))
            if not cursor.fetchone():
                conn.close()
                raise ValueError(f"Manager ID '{manager_id}' does not exist.")
                
        cursor.execute(
            "INSERT INTO employees (emp_id, name, manager_id, email) VALUES (?, ?, ?, ?)",
            (emp.emp_id, name, manager_id, emp.email)
        )
        
        cursor.execute(
            "INSERT INTO leave_balances (emp_id, balance) VALUES (?, ?)",
            (emp.emp_id, 10)
        )
        
        conn.commit()
        conn.close()

    def get_manager(self, emp_id: str) -> str:
        """
        Return manager's ID and name, or a message if none.
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT manager_id FROM employees WHERE emp_id = ?", (emp_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            raise ValueError(f"Employee ID '{emp_id}' not found.")
            
        mgr_id = row['manager_id']
        if not mgr_id:
            conn.close()
            return "No manager assigned."
            
        cursor.execute("SELECT name FROM employees WHERE emp_id = ?", (mgr_id,))
        mgr_row = cursor.fetchone()
        conn.close()
        
        return f"{mgr_id}: {mgr_row['name']}"

    def search_employee_by_name(self, name_query: str, n: int = 5, cutoff: float = 0.6) -> List[str]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT emp_id, name FROM employees")
        rows = cursor.fetchall()
        conn.close()
        
        matches = get_close_matches(name_query, [r["name"] for r in rows], n=n, cutoff=cutoff)
        return [r["emp_id"] for r in rows if r["name"] in matches]

    def get_employee_details(self, emp_id: str) -> Dict[str, str]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT emp_id, name, manager_id, email FROM employees WHERE emp_id = ?", (emp_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise ValueError(f"Employee ID '{emp_id}' not found.")
        return dict(row)

    def get_direct_reports(self, manager_id: str) -> List[str]:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM employees WHERE emp_id = ?", (manager_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Manager ID '{manager_id}' not found.")
            
        cursor.execute("SELECT emp_id FROM employees WHERE manager_id = ?", (manager_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [r["emp_id"] for r in rows]

if __name__ == "__main__":
    em = EmployeeManager()
    em.add_employee(EmployeeCreate(emp_id="E001", name="John Doe", manager_id=None, email="john@example.com"))
    print(em.get_next_emp_id())