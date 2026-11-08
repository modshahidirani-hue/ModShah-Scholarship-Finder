# ModShah Scholarship Finder — Setup

## Required software
Install Python 3.10+, MySQL Server, MySQL Workbench and VS Code.

## 1. Open the project
Extract the ZIP and open the `ModShah-Scholarship-Finder` folder in VS Code.

## 2. Install Python packages
Open **Terminal → New Terminal** in VS Code and run:
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

## 3. Set up MySQL
Open MySQL Workbench, connect to your local server, open `database.sql`, and click the lightning bolt Execute button. This creates the database and tables.

## 4. Configure database password
Copy `.env.example` to a new file named `.env`. Enter your MySQL password in `DB_PASSWORD`. Change `SECRET_KEY` to a long random value. Save.

## 5. Run the website
In VS Code terminal:
```powershell
python app.py
```
Open http://127.0.0.1:5000 in your browser. Register and log in.

## 6. Create an admin account (optional)
Register a normal account first. In MySQL Workbench run this SQL, replacing the email:
```sql
USE modshah_scholarship;
UPDATE users SET role='admin' WHERE email='your-email@example.com';
```
Log out and log in again, then visit `/admin` to add scholarships.

## Included
- Student registration/login with password hashing
- Student profile (education, marks, income, location, category)
- Scholarship search
- Application tracker and status updates
- PDF/JPG/PNG document upload
- Basic keyword-based assistant (not a live AI model)
- Admin dashboard and scholarship creation

## Important
The included scholarship entry is demo content, not a verified current scheme. Confirm eligibility and deadlines on official provider websites. Eligibility fields are stored but automatic eligibility matching is not implemented yet. This is a learning starter project, not production-ready. Uploaded files are stored locally; add stronger security and privacy controls before public deployment.
