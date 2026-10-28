# DevOps Task Tracking System Using Agile Methodology

A beginner-friendly Flask + SQLite college mini-project. It demonstrates task management, Agile sprint tracking, bug tracking, and a dashboard. Agile is the software development methodology; this app does not require Jenkins, Docker, or Kubernetes.

## Features
- Login with role-based access (admin/member)
- Dashboard summary
- Create and assign tasks
- Update task status
- Create and track sprints
- Report and update bugs
- Add team members (admin only)
- SQLite database created automatically

## Requirements
- Python 3.10 or newer
- A browser
- Internet only for installing Flask the first time

## Run on Windows
1. Extract this ZIP to a folder, for example `C:\Users\YourName\Desktop\devops_agile_task_tracker`.
2. Open that folder in VS Code.
3. Open Terminal > New Terminal.
4. Create a virtual environment:
   ```powershell
   py -m venv .venv
   ```
5. Activate it:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt and run:
   ```bat
   .venv\Scripts\activate.bat
   ```
6. Install dependencies:
   ```powershell
   py -m pip install -r requirements.txt
   ```
7. Start the app:
   ```powershell
   py app.py
   ```
8. Open `http://127.0.0.1:5000` in your browser.

## Demo accounts
- Admin: `admin@example.com` / `Admin123!`
- Member: `member@example.com` / `Member123!`

Change these credentials for any real use. This is an educational demo; before public deployment, set a strong random `SECRET_KEY`, disable debug mode, add CSRF protection, and review security settings.

## Suggested demo
1. Log in as admin.
2. Add a team member from Team.
3. Create a sprint from Sprints.
4. Create and assign a task.
5. Log out and sign in as the assigned member.
6. Update the task status.
7. Report a bug and update its status.
8. Show the dashboard and explain how each feature could be delivered in Agile sprints.

## Agile sprint plan
- Sprint 1: requirements, UI/database design, login
- Sprint 2: task creation and assignment
- Sprint 3: sprint and bug management
- Sprint 4: dashboard, testing, feedback, documentation

## Project structure
```
devops_agile_task_tracker/
├── app.py
├── requirements.txt
├── README.md
├── templates/
└── static/
```
