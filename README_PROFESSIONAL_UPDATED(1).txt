AI Student Performance System - Professional Update

Added:
- Modern analytics dashboard with performance trend bars and KPIs
- Responsive mobile-friendly layout
- Dark/light mode toggle
- Approximate 10-point CGPA estimate from latest score
- PDF performance report download
- Built-in study assistant chatbot for score/weak-subject/study-plan questions
- Optional admin dashboard controlled by ADMIN_EMAIL environment variable
- Optional email notification controlled by SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, FROM_EMAIL
- SQLite WAL/busy-timeout improvements for deployment stability
- Gunicorn + ReportLab dependencies for Render deployment

Render Start Command:
gunicorn app:app
Build Command:
pip install -r requirements.txt

Admin setup on Render:
Set ADMIN_EMAIL to the exact email used by the admin account.
Optional email setup requires SMTP environment variables.
