import streamlit as st
import sqlite3
import time
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'hr_database.db'))

st.set_page_config(page_title="HR Dashboard", layout="wide")

def get_connection():
    return sqlite3.connect(DB_PATH)

def fetch_data(query):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    if rows:
        columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]
    else:
        data = []
    conn.close()
    return data

st.title("HR Assistant Dashboard")

st.sidebar.info("Dashboard auto-refreshes every 30 seconds.")

tab1, tab2, tab3, tab4 = st.tabs(["Employees", "Leave Balances", "Tickets", "Meetings"])

with tab1:
    st.header("Employees")
    col1, col2 = st.columns([0.8, 0.2])
    with col2:
        if st.button("Refresh Employees"):
            pass
            
    emp_data = fetch_data("SELECT * FROM employees")
    if emp_data:
        st.dataframe(emp_data, use_container_width=True)
    else:
        st.write("No employees found.")
    
    st.subheader("Add Leave Balance Manually")
    with st.form("add_leave_balance_form"):
        emp_id = st.text_input("Employee ID (e.g. E011)")
        days = st.number_input("Leave Days", min_value=0, value=10, step=1)
        submitted = st.form_submit_button("Add Balance")
        if submitted:
            if emp_id:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO leave_balances (emp_id, balance) VALUES (?, ?)", (emp_id, days))
                    conn.commit()
                    conn.close()
                    st.success(f"Added {days} days for {emp_id}")
                except sqlite3.IntegrityError:
                    st.error(f"Balance for {emp_id} already exists!")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Please enter an Employee ID.")

with tab2:
    st.header("Leave Balances")
    col1, col2 = st.columns([0.8, 0.2])
    with col2:
        if st.button("Refresh Balances"):
            pass
            
    leave_data = fetch_data("SELECT * FROM leave_balances")
    if leave_data:
        st.dataframe(leave_data, use_container_width=True)
    else:
        st.write("No leave balances found.")

with tab3:
    st.header("Tickets")
    col1, col2 = st.columns([0.8, 0.2])
    with col2:
        if st.button("Refresh Tickets"):
            pass
            
    tickets_data = fetch_data("SELECT * FROM tickets")
    if tickets_data:
        st.dataframe(tickets_data, use_container_width=True)
    else:
        st.write("No tickets found.")

with tab4:
    st.header("Meetings")
    col1, col2 = st.columns([0.8, 0.2])
    with col2:
        if st.button("Refresh Meetings"):
            pass
            
    meetings_data = fetch_data("SELECT * FROM meetings")
    if meetings_data:
        st.dataframe(meetings_data, use_container_width=True)
    else:
        st.write("No meetings found.")

time.sleep(30)
st.rerun()
