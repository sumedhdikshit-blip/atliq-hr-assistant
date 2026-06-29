# AtliQ HR Hub - AI-Powered HR Assistant

AtliQ HR Hub is an **AI-powered HR Assistant** with a natural language interface that streamlines day-to-day human resource operations. It enables managers and HR professionals to execute database operations, send system emails, manage ticketing, and arrange meetings using natural language instructions via a CLI or directly from a web dashboard interface.

---

## Features

- **Natural Language Chat Client**: Query, command, and manage the system with plain English text directly from the terminal or using the web-integrated floating chat widget.
- **Web Dashboard**: Modern single-page app displaying real-time statistics and sqlite databases.
- **Full Onboarding Workflow**: Multi-step onboarding command that registers new hires in the database, distributes welcome emails, alerts reporting managers, issues equipment purchase tickets (Laptop, ID Card, Access Card), and arranges introductory meetings.
- **Leave Management System**: Track leave balances, log historical data, and apply for leaves.
- **Support Tickets**: File asset requisitions and track progress with interactive status badges (Open, In Progress, Closed).
- **Meeting Scheduling**: Manage introductory sessions, syncs, or check-ins with employees.
- **Gmail SMTP Email Service**: Automated, real-time emails sent via secure App Password configurations.
- **Responsive Dark/Light Theme**: A theme toggle button saved via `localStorage` with smooth transition animations.
- **Instant CSV Export**: Pure client-side JS CSV exports for all directory tables.
- **Persistent SQLite Database**: Built on a solid local database backend with structured relational tables.

---

## Tech Stack

- **Backend**: Python, FastMCP (Model Context Protocol) Server, FastAPI, SQLite
- **AI Engine**: Groq API (`llama-3.1-8b-instant` LLM)
- **Frontend**: HTML5, Vanilla CSS3 (Custom Variables, Smooth Transitions), Vanilla JavaScript
- **Emailer**: Gmail SMTP Client

---

## Project Structure

```text
atliq-hr-assistant/
├── .env                  # Configuration keys (GROQ API key, SMTP credentials)
├── .gitignore            # Git ignore list
├── .python-version       # Python target version
├── README.md             # Project documentation (this file)
├── chat.py               # Natural language terminal chat client
├── dashboard.html        # Web dashboard front-end interface
├── dashboard.py          # Dashboard launcher
├── dashboard_api.py      # FastAPI server backend & Chat Endpoint
├── emails.py             # Email Sender helper (Gmail SMTP integration)
├── hr_database.db        # Structured SQLite database file
├── pyproject.toml        # Dependency manifest managed by uv
├── server.py             # Model Context Protocol (FastMCP) server tools definitions
├── utils.py              # Seeding script and utilities
└── hrms/                 # Core modular managers
    ├── __init__.py       # Initializes HRMS managers
    ├── db.py             # Database creation schema and connectivity
    ├── employee_manager.py # Employee registry CRUD controller
    ├── leave_manager.py  # Leave balances & history CRUD controller
    ├── meeting_manager.py # Schedules and cancels meetings
    ├── schemas.py        # Pydantic typing and validation layer
    └── ticket_manager.py  # Procurement ticketing controller
```

---

## Setup Instructions

### Prerequisites
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (Extremely fast Python package installer and resolver)

### Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/sumedhdikshit-blip/atliq-hr-assistant.git
   cd atliq-hr-assistant
   ```

2. **Install Dependencies**:
   Install all project packages into a virtual environment automatically managed by `uv`:
   ```bash
   uv sync
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY="your-groq-api-key-here"
   CB_EMAIL="your-system-sender-email@gmail.com"
   CB_EMAIL_PWD="your-gmail-app-password"
   ```

---

## Running the Application

### 1. Natural Language CLI
Interact with the HR assistant directly from your terminal:
```bash
uv run chat.py
```

### 2. Interactive Web Dashboard
Run the FastAPI web server to launch the frontend dashboard:
```bash
uv run uvicorn dashboard_api:app --reload --port 8001
```
Open [http://127.0.0.1:8001](http://127.0.0.1:8001) in your browser.

---

## Usage Examples

Here are typical chat prompts and their expected outcomes in the system:

### Example 1: Multi-Step Employee Onboarding
**Prompt**:
> Onboard Sumedh Dikshit with email sumedhdikshit@gmail.com. His manager is E006.

**Response**:
```text
Step 1: Added employee Sumedh Dikshit (E015) - SUCCESS
Step 2: Welcome email - SUCCESS
Step 3: Manager notification - SUCCESS
Step 4: Created tickets - SUCCESS
Step 5: Scheduled intro meeting - SUCCESS
```

### Example 2: Checking Leave Balances
**Prompt**:
> What is the leave balance for E001?

**Response**:
```text
Leave balance for E001: 13 days
```

### Example 3: Submitting Support / Procurement Tickets
**Prompt**:
> Create a ticket for E004 requesting a new monitor because their old one broke.

**Response**:
```text
Ticket T0024 created successfully for employee E004 (Item: Monitor).
```

### Example 4: Scheduling a Meeting
**Prompt**:
> Schedule a meeting for employee E003 tomorrow at 2 PM about project planning.

**Response**:
```text
Introductory meeting scheduled for E003 on 2026-06-30 at 14:00. Topic: Project Planning.
```

---

## Screenshots

*(add screenshots here)*

---

## License

This project is licensed under the terms of the [MIT License](LICENSE).
