from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash
import sqlite3, os, io, math, statistics, smtplib, secrets, re
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from urllib.parse import quote_plus
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from email.message import EmailMessage
try:
    import psycopg2
    from psycopg2.extras import DictCursor
except ImportError:
    psycopg2 = None
    DictCursor = None

app=Flask(__name__)
app.secret_key=os.environ.get("SECRET_KEY", "dev-only-change-this-secret")
BASE=os.path.dirname(os.path.abspath(__file__))
DB=os.path.join(BASE,"student_performance.db")
ADMIN_EMAIL=os.environ.get("ADMIN_EMAIL", "")
ADMIN_PHONE=os.environ.get("ADMIN_PHONE", "")
NOTES_UPLOAD_DIR=os.path.join(BASE,"static","notes_uploads")
os.makedirs(NOTES_UPLOAD_DIR, exist_ok=True)
MAX_PDF_MB=20

APP_NAME="Victory Hub AI"
APP_TAGLINE="AI Student Performance System"
APP_SLOGAN="Learn • Grow • Achieve"
OTP_VALID_MINUTES=10
OTP_MAX_ATTEMPTS=5

@app.context_processor
def inject_brand():
    return {"app_name": APP_NAME, "app_tagline": APP_TAGLINE, "app_slogan": APP_SLOGAN, "is_admin": is_admin(), "is_faculty": is_faculty()}

CATALOG={'CSE': {'1': ['Engineering Mathematics I', 'Engineering Physics', 'Programming for Problem Solving', 'Engineering Graphics', 'English / Communication Skills'], '2': ['Engineering Mathematics II', 'Engineering Chemistry', 'Data Structures', 'Digital Logic Design', 'Object Oriented Programming'], '3': ['Discrete Mathematics', 'Database Management Systems', 'Operating Systems', 'Computer Networks', 'Computer Organization & Architecture'], '4': ['Design and Analysis of Algorithms', 'Software Engineering', 'Web Technologies', 'Theory of Computation', 'Artificial Intelligence'], '5': ['Machine Learning', 'Compiler Design', 'Computer Graphics', 'Distributed Systems', 'Professional Elective I'], '6': ['Cloud Computing', 'Data Mining', 'Cyber Security', 'Professional Elective II', 'Open Source Technologies'], '7': ['Internet of Things', 'Big Data Analytics', 'Professional Elective III', 'Project / Internship', 'Technical Seminar'], '8': ['Project Work', 'Professional Elective IV', 'Professional Elective V', 'Technical Seminar / Viva', 'Comprehensive Viva']}, 'AI & ML': {'1': ['Engineering Mathematics I', 'Engineering Physics', 'Programming for Problem Solving', 'Engineering Graphics', 'English / Communication Skills'], '2': ['Engineering Mathematics II', 'Engineering Chemistry', 'Data Structures', 'Object Oriented Programming', 'Digital Logic Design'], '3': ['Probability & Statistics', 'Database Management Systems', 'Operating Systems', 'Computer Networks', 'Artificial Intelligence'], '4': ['Machine Learning', 'Design and Analysis of Algorithms', 'Deep Learning', 'Theory of Computation', 'Web Technologies'], '5': ['Natural Language Processing', 'Computer Vision', 'Reinforcement Learning', 'Data Mining', 'Professional Elective I'], '6': ['Big Data Analytics', 'Generative AI', 'Cloud Computing', 'MLOps', 'Professional Elective II'], '7': ['Advanced Machine Learning', 'Deep Learning Applications', 'Professional Elective III', 'Project / Internship', 'Technical Seminar'], '8': ['Major Project', 'Professional Elective IV', 'Professional Elective V', 'Project Viva', 'Comprehensive Viva']}, 'AI & DS': {'1': ['Engineering Mathematics I', 'Engineering Physics', 'Programming for Problem Solving', 'Engineering Graphics', 'English / Communication Skills'], '2': ['Engineering Mathematics II', 'Engineering Chemistry', 'Data Structures', 'Object Oriented Programming', 'Digital Logic Design'], '3': ['Probability & Statistics', 'Database Management Systems', 'Data Visualization', 'Python for Data Science', 'Computer Networks'], '4': ['Machine Learning', 'Design and Analysis of Algorithms', 'Data Mining', 'Artificial Intelligence', 'Web Technologies'], '5': ['Big Data Analytics', 'Natural Language Processing', 'Deep Learning', 'Data Warehousing', 'Professional Elective I'], '6': ['Cloud Computing', 'Generative AI', 'MLOps', 'Business Intelligence', 'Professional Elective II'], '7': ['Advanced Data Analytics', 'Deep Learning Applications', 'Professional Elective III', 'Project / Internship', 'Technical Seminar'], '8': ['Major Project', 'Professional Elective IV', 'Professional Elective V', 'Project Viva', 'Comprehensive Viva']}, 'IT': {'1': ['Engineering Mathematics I', 'Engineering Physics', 'Programming for Problem Solving', 'Engineering Graphics', 'English / Communication Skills'], '2': ['Engineering Mathematics II', 'Engineering Chemistry', 'Data Structures', 'Object Oriented Programming', 'Digital Logic Design'], '3': ['Database Management Systems', 'Operating Systems', 'Computer Networks', 'Computer Organization', 'Software Engineering'], '4': ['Design and Analysis of Algorithms', 'Web Technologies', 'Theory of Computation', 'Artificial Intelligence', 'Professional Elective I'], '5': ['Machine Learning', 'Cloud Computing', 'Cyber Security', 'Data Mining', 'Professional Elective II'], '6': ['Big Data Analytics', 'Mobile Application Development', 'DevOps', 'Internet of Things', 'Professional Elective III'], '7': ['Advanced Web Technologies', 'Cloud Security', 'Professional Elective IV', 'Project / Internship', 'Technical Seminar'], '8': ['Major Project', 'Professional Elective V', 'Professional Elective VI', 'Project Viva', 'Comprehensive Viva']}, 'ECE': {'1': ['Engineering Mathematics I', 'Engineering Physics', 'Programming for Problem Solving', 'Engineering Graphics', 'English / Communication Skills'], '2': ['Engineering Mathematics II', 'Engineering Chemistry', 'Basic Electrical Engineering', 'Electronic Devices', 'Digital Logic Design'], '3': ['Signals and Systems', 'Network Analysis', 'Analog Circuits', 'Digital Electronics', 'Electromagnetic Waves'], '4': ['Control Systems', 'Microprocessors and Microcontrollers', 'Communication Systems', 'Linear IC Applications', 'Probability and Random Processes'], '5': ['Digital Signal Processing', 'VLSI Design', 'Embedded Systems', 'Antenna and Wave Propagation', 'Professional Elective I'], '6': ['Computer Architecture', 'IoT Systems', 'Wireless Communications', 'Optical Communications', 'Professional Elective II'], '7': ['Advanced VLSI', 'Embedded AI', 'RF and Microwave Engineering', 'Project / Internship', 'Technical Seminar'], '8': ['Major Project', 'Professional Elective III', 'Professional Elective IV', 'Project Viva', 'Comprehensive Viva']}, 'EEE': {'1': ['Engineering Mathematics I', 'Engineering Physics', 'Programming for Problem Solving', 'Engineering Graphics', 'English / Communication Skills'], '2': ['Engineering Mathematics II', 'Engineering Chemistry', 'Basic Electronics', 'Electrical Circuit Analysis', 'Electrical Machines I'], '3': ['Electrical Machines II', 'Power Systems I', 'Power Electronics', 'Control Systems', 'Measurements and Instrumentation'], '4': ['Power Systems II', 'Microprocessors and Microcontrollers', 'Electrical Drives', 'Signals and Systems', 'Power System Protection'], '5': ['High Voltage Engineering', 'Switchgear and Protection', 'Renewable Energy Sources', 'Digital Signal Processing', 'Professional Elective I'], '6': ['Power System Analysis', 'Smart Grid', 'Electric Vehicle Technology', 'Industrial Automation', 'Professional Elective II'], '7': ['Advanced Power Electronics', 'Power Quality', 'Energy Management', 'Project / Internship', 'Technical Seminar'], '8': ['Major Project', 'Professional Elective III', 'Professional Elective IV', 'Project Viva', 'Comprehensive Viva']}, 'MECH': {'1': ['Engineering Mathematics I', 'Engineering Physics', 'Programming for Problem Solving', 'Engineering Graphics', 'English / Communication Skills'], '2': ['Engineering Mathematics II', 'Engineering Chemistry', 'Engineering Mechanics', 'Basic Electrical Engineering', 'Manufacturing Processes'], '3': ['Thermodynamics', 'Fluid Mechanics', 'Strength of Materials', 'Machine Drawing', 'Material Science'], '4': ['Theory of Machines', 'Heat Transfer', 'Machine Design I', 'Manufacturing Technology', 'Metrology and Measurements'], '5': ['Machine Design II', 'Internal Combustion Engines', 'Refrigeration and Air Conditioning', 'CAD/CAM', 'Professional Elective I'], '6': ['Finite Element Methods', 'Robotics', 'Automobile Engineering', 'Industrial Engineering', 'Professional Elective II'], '7': ['Additive Manufacturing', 'Mechatronics', 'Advanced Manufacturing', 'Project / Internship', 'Technical Seminar'], '8': ['Major Project', 'Professional Elective III', 'Professional Elective IV', 'Project Viva', 'Comprehensive Viva']}, 'CIVIL': {'1': ['Engineering Mathematics I', 'Engineering Physics', 'Programming for Problem Solving', 'Engineering Graphics', 'English / Communication Skills'], '2': ['Engineering Mathematics II', 'Engineering Chemistry', 'Engineering Mechanics', 'Basic Electrical Engineering', 'Building Materials'], '3': ['Strength of Materials', 'Fluid Mechanics', 'Surveying', 'Structural Analysis I', 'Concrete Technology'], '4': ['Structural Analysis II', 'Geotechnical Engineering I', 'Hydrology and Water Resources', 'Transportation Engineering I', 'Environmental Engineering I'], '5': ['Design of Reinforced Concrete Structures', 'Geotechnical Engineering II', 'Transportation Engineering II', 'Environmental Engineering II', 'Professional Elective I'], '6': ['Design of Steel Structures', 'Estimation and Costing', 'Construction Management', 'Hydraulic Engineering', 'Professional Elective II'], '7': ['Advanced Structural Engineering', 'Remote Sensing and GIS', 'Earthquake Engineering', 'Project / Internship', 'Technical Seminar'], '8': ['Major Project', 'Professional Elective III', 'Professional Elective IV', 'Project Viva', 'Comprehensive Viva']}}

RESOURCE_MAP={
"c programming":("https://www.geeksforgeeks.org/c-programming-language/","https://www.youtube.com/results?search_query=C+Programming+Full+Course+freeCodeCamp"),
"python":("https://docs.python.org/3/tutorial/","https://www.youtube.com/results?search_query=Python+Full+Course+freeCodeCamp"),
"data structures":("https://www.geeksforgeeks.org/data-structures/","https://www.youtube.com/results?search_query=Data+Structures+Full+Course+freeCodeCamp"),
"database management systems":("https://www.geeksforgeeks.org/dbms/","https://www.youtube.com/results?search_query=DBMS+Full+Course+NPTEL"),
"operating systems":("https://www.geeksforgeeks.org/operating-systems/","https://www.youtube.com/results?search_query=Operating+Systems+Full+Course+NPTEL"),
"computer networks":("https://www.geeksforgeeks.org/computer-network-tutorials/","https://www.youtube.com/results?search_query=Computer+Networks+Full+Course+NPTEL"),
"machine learning":("https://www.geeksforgeeks.org/machine-learning/","https://www.youtube.com/results?search_query=Machine+Learning+Full+Course+NPTEL"),
"artificial intelligence":("https://www.geeksforgeeks.org/artificial-intelligence/","https://www.youtube.com/results?search_query=Artificial+Intelligence+Full+Course+NPTEL"),
"design and analysis of algorithms":("https://www.geeksforgeeks.org/fundamentals-of-algorithms/","https://www.youtube.com/results?search_query=Design+and+Analysis+of+Algorithms+Full+Course+NPTEL"),
"web technologies":("https://www.w3schools.com/","https://www.youtube.com/results?search_query=Web+Technologies+Full+Course"),
"java":("https://dev.java/learn/","https://www.youtube.com/results?search_query=Java+Full+Course+freeCodeCamp"),
"theory of computation":("https://www.geeksforgeeks.org/theory-of-computation-automata-tutorials/","https://www.youtube.com/results?search_query=Theory+of+Computation+Full+Course"),
"compiler design":("https://www.geeksforgeeks.org/compiler-design-tutorials/","https://www.youtube.com/results?search_query=Compiler+Design+Full+Course"),
"computer organization & architecture":("https://www.geeksforgeeks.org/computer-organization-and-architecture-tutorials/","https://www.youtube.com/results?search_query=Computer+Organization+Architecture+Full+Course"),
"software engineering":("https://www.geeksforgeeks.org/software-engineering/","https://www.youtube.com/results?search_query=Software+Engineering+Full+Course"),
"cloud computing":("https://www.geeksforgeeks.org/cloud-computing/","https://www.youtube.com/results?search_query=Cloud+Computing+Full+Course"),
"cyber security":("https://www.geeksforgeeks.org/cyber-security-tutorial/","https://www.youtube.com/results?search_query=Cyber+Security+Full+Course"),
"computer graphics":("https://www.geeksforgeeks.org/computer-graphics/","https://www.youtube.com/results?search_query=Computer+Graphics+Full+Course"),
"engineering mathematics i":("https://nptel.ac.in/courses/111105090","https://www.youtube.com/results?search_query=Engineering+Mathematics+1+Full+Course"),
"engineering mathematics ii":("https://nptel.ac.in/courses/111105035","https://www.youtube.com/results?search_query=Engineering+Mathematics+2+Full+Course"),
"engineering physics":("https://nptel.ac.in/courses/115105099","https://www.youtube.com/results?search_query=Engineering+Physics+Full+Course"),
"engineering chemistry":("https://nptel.ac.in/courses/104106096","https://www.youtube.com/results?search_query=Engineering+Chemistry+Full+Course")
}

class DBConnection:
    # Small compatibility layer: PostgreSQL on Render, SQLite locally.
    def __init__(self, conn, postgres=False):
        self.conn=conn
        self.postgres=postgres
        self.cur = conn.cursor()
    def _sql(self, sql):
        return sql.replace('?', '%s') if self.postgres else sql
    def execute(self, sql, params=()):
        self.cur.execute(self._sql(sql), params)
        return self.cur
    def commit(self): self.conn.commit()
    def rollback(self): self.conn.rollback()
    def close(self):
        try: self.cur.close()
        finally: self.conn.close()

def using_postgres():
    return bool(os.environ.get('DATABASE_URL'))

def get_db():
    url=os.environ.get('DATABASE_URL','').strip()
    if url:
        if psycopg2 is None:
            raise RuntimeError('PostgreSQL driver missing. Add psycopg2-binary to requirements.txt.')
        if url.startswith('postgres://'):
            url='postgresql://'+url[len('postgres://'):]
        conn=psycopg2.connect(url, connect_timeout=10, cursor_factory=DictCursor)
        return DBConnection(conn, postgres=True)
    conn=sqlite3.connect(DB)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA busy_timeout=30000')
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    return DBConnection(conn, postgres=False)

def init_db():
    c=get_db()
    if c.postgres:
        c.execute('''CREATE TABLE IF NOT EXISTS users(
            id BIGSERIAL PRIMARY KEY,name TEXT NOT NULL,email TEXT UNIQUE,phone TEXT UNIQUE,password TEXT NOT NULL,
            role TEXT DEFAULT 'student')''')
        c.execute('''CREATE TABLE IF NOT EXISTS semester_subjects(
            id BIGSERIAL PRIMARY KEY,user_id BIGINT NOT NULL,branch TEXT NOT NULL,year TEXT NOT NULL,
            semester TEXT NOT NULL,subject_names TEXT NOT NULL,
            UNIQUE(user_id,branch,year,semester))''')
        c.execute('''CREATE TABLE IF NOT EXISTS predictions(
            id BIGSERIAL PRIMARY KEY,user_id BIGINT,name TEXT,year TEXT,semester TEXT,branch TEXT,
            attendance DOUBLE PRECISION,subject_names TEXT,subject_marks TEXT,assignment_marks TEXT,
            internal_marks TEXT,study_hours DOUBLE PRECISION,prediction TEXT,score DOUBLE PRECISION,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS custom_subjects(
            id BIGSERIAL PRIMARY KEY,user_id BIGINT,branch TEXT,year TEXT,semester TEXT,
            subjects TEXT,UNIQUE(user_id,branch,year,semester))''')
        c.execute('''CREATE TABLE IF NOT EXISTS password_resets(
            id BIGSERIAL PRIMARY KEY,user_id BIGINT NOT NULL,email TEXT NOT NULL,otp_hash TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,attempts INTEGER DEFAULT 0,verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS notes_files(
            id BIGSERIAL PRIMARY KEY,branch TEXT NOT NULL,regulation TEXT NOT NULL,year TEXT NOT NULL,
            semester TEXT NOT NULL,subject TEXT NOT NULL,stored_name TEXT NOT NULL,original_name TEXT NOT NULL,
            uploaded_by TEXT,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(branch,regulation,year,semester,subject))''')
    else:
        c.execute('''CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT UNIQUE,phone TEXT UNIQUE,password TEXT NOT NULL,
            role TEXT DEFAULT 'student')''')
        c.execute('''CREATE TABLE IF NOT EXISTS semester_subjects(
            id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,branch TEXT NOT NULL,year TEXT NOT NULL,
            semester TEXT NOT NULL,subject_names TEXT NOT NULL,UNIQUE(user_id,branch,year,semester))''')
        c.execute('''CREATE TABLE IF NOT EXISTS predictions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,name TEXT,year TEXT,semester TEXT,branch TEXT,
            attendance REAL,subject_names TEXT,subject_marks TEXT,assignment_marks TEXT,internal_marks TEXT,
            study_hours REAL,prediction TEXT,score REAL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS custom_subjects(
            id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,branch TEXT,year TEXT,semester TEXT,
            subjects TEXT,UNIQUE(user_id,branch,year,semester))''')
        c.execute('''CREATE TABLE IF NOT EXISTS password_resets(
            id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,email TEXT NOT NULL,otp_hash TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,attempts INTEGER DEFAULT 0,verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS notes_files(
            id INTEGER PRIMARY KEY AUTOINCREMENT,branch TEXT NOT NULL,regulation TEXT NOT NULL,year TEXT NOT NULL,
            semester TEXT NOT NULL,subject TEXT NOT NULL,stored_name TEXT NOT NULL,original_name TEXT NOT NULL,
            uploaded_by TEXT,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(branch,regulation,year,semester,subject))''')
    try:
        c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'student'")
        c.commit()
    except Exception:
        c.rollback()
    c.commit(); c.close()

def resources(subject):
    k=subject.strip().lower()
    if k in RESOURCE_MAP: return RESOURCE_MAP[k]
    q=quote_plus(subject.strip())
    notes=f'https://www.google.com/search?q={q}+notes+filetype%3Apdf'
    video=f'https://www.youtube.com/results?search_query={q}+full+course+lecture'
    return (notes, video)

REGULATIONS=["R16","R20","R23"]
NOTES_SITES={
"R16":[("JNTUK Materials (jntukmaterials.com)","jntukmaterials.com"),
       ("JNTU Fast Updates","www.jntufastupdates.com"),
       ("JNTU Materials","www.jntumaterials.co.in")],
"R20":[("JNTUK Materials (jntukmaterials.com)","jntukmaterials.com"),
       ("JNTU Fast Updates","www.jntufastupdates.com"),
       ("JNTU Materials","www.jntumaterials.co.in")],
"R23":[("JNTUK Materials (jntukmaterials.com)","jntukmaterials.com"),
       ("JNTU Materials","www.jntumaterials.co.in"),
       ("JNTU Fast Updates","www.jntufastupdates.com")]
}

def regulation_resources(subject, regulation):
    # Builds live search links (site-scoped + general) instead of hardcoding PDF
    # URLs, since exact page links on third-party note sites change over time.
    q=quote_plus(f"JNTUK {regulation} {subject} notes")
    sites=NOTES_SITES.get(regulation, NOTES_SITES["R20"])
    site_links=[]
    for label, domain in sites:
        sq=quote_plus(f"site:{domain} {subject} {regulation}")
        site_links.append({"label":label,"url":f"https://www.google.com/search?q={sq}"})
    notes=f"https://www.google.com/search?q={q}+pdf"
    video=f"https://www.youtube.com/results?search_query={quote_plus(subject)}+{regulation}+JNTUK+lecture"
    return {"notes":notes,"video":video,"sites":site_links}

def send_prediction_email(to_email, result):
    host=os.environ.get("SMTP_HOST",""); user=os.environ.get("SMTP_USER",""); password=os.environ.get("SMTP_PASSWORD","")
    if not (host and user and password and to_email): return
    try:
        msg=EmailMessage(); msg["Subject"]="AI Student Performance Report"; msg["From"]=os.environ.get("FROM_EMAIL",user); msg["To"]=to_email
        msg.set_content(f"Hello {result['name']},\n\nYour latest predicted performance is {result['score']}% ({result['label']}).\nFocus subjects: {', '.join(x['name'] for x in result['weak'])}.\n\nOpen your dashboard to view the full study plan and PDF report.")
        with smtplib.SMTP(host,int(os.environ.get("SMTP_PORT","587")),timeout=10) as server:
            server.starttls(); server.login(user,password); server.send_message(msg)
    except Exception:
        pass

def smtp_configured():
    return bool(os.environ.get("SMTP_HOST") and os.environ.get("SMTP_USER") and os.environ.get("SMTP_PASSWORD"))

def send_otp_email(to_email, name, otp):
    host=os.environ.get("SMTP_HOST",""); user=os.environ.get("SMTP_USER",""); password=os.environ.get("SMTP_PASSWORD","")
    if not (host and user and password and to_email):
        print(f"[OTP EMAIL] Skipped — missing config. host={bool(host)} user={bool(user)} password={bool(password)} to_email={bool(to_email)}")
        return False
    try:
        msg=EmailMessage(); msg["Subject"]=f"{APP_NAME} - Your Password Reset OTP"
        msg["From"]=os.environ.get("FROM_EMAIL",user); msg["To"]=to_email
        msg.set_content(f"Hello {name},\n\nYour {APP_NAME} password reset OTP is: {otp}\n\nThis code is valid for {OTP_VALID_MINUTES} minutes. If you did not request this, you can ignore this email.")
        with smtplib.SMTP(host,int(os.environ.get("SMTP_PORT","587")),timeout=10) as server:
            server.starttls(); server.login(user,password); server.send_message(msg)
        print(f"[OTP EMAIL] Sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"[OTP EMAIL] FAILED to send to {to_email}: {type(e).__name__}: {e}")
        return False

def latest_prediction():
    if not session.get("user_id"):
        return None
    c=get_db()
    row=c.execute("SELECT * FROM predictions WHERE user_id=? ORDER BY id DESC LIMIT 1",(session["user_id"],)).fetchone()
    c.close()
    return row

def build_result(row):
    if not row: return None
    names=row["subject_names"].split("|") if row["subject_names"] else []
    marks=[float(x) for x in row["subject_marks"].split("|")] if row["subject_marks"] else []
    ext=[round(x/70*100,2) for x in marks]
    weak=sorted(zip(names,ext),key=lambda x:x[1])[:2]
    weak_names={n for n,_ in weak}
    all_subjects=[{"name":n,"mark":m,"notes":resources(n)[0],"video":resources(n)[1],"weak":n in weak_names} for n,m in zip(names,ext)]
    weak_data=[{"name":n,"mark":m,"notes":resources(n)[0],"video":resources(n)[1]} for n,m in weak]
    plan=[]
    if weak_data:
        first=weak_data[0]["name"]
        second=weak_data[1]["name"] if len(weak_data)>1 else first
        plan=[("Day 1",first,"Concepts + notes","60 min"),("Day 2",second,"Concepts + examples","60 min"),("Day 3",first,"Practice questions","75 min"),("Day 4",second,"Practice problems","75 min"),("Day 5",first,"Revision + previous questions","60 min"),("Day 6",second,"Revision + previous questions","60 min"),("Day 7","Weak subjects","Mock test + error review","90 min")]
    return {"score":row["score"],"label":row["prediction"],"message":"Keep following the study plan and focus on weak subjects.","weak":weak_data,"all_subjects":all_subjects,"plan":plan,"year":row["year"],"semester":row["semester"],"branch":row["branch"],"name":row["name"],"attendance":row["attendance"],"study_hours":row["study_hours"]}

@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"): return redirect(url_for("login"))
    c=get_db()
    rows=c.execute("SELECT * FROM predictions WHERE user_id=? ORDER BY id ASC",(session["user_id"],)).fetchall()
    c.close()
    scores=[float(r["score"]) for r in rows]
    latest=build_result(rows[-1]) if rows else None
    return render_template("dashboard.html",rows=rows,latest=latest,avg=round(statistics.mean(scores),2) if scores else 0,best=round(max(scores),2) if scores else 0,count=len(rows))

@app.route("/report/pdf")
def report_pdf():
    if not session.get("user_id"): return redirect(url_for("login"))
    row=latest_prediction()
    result=build_result(row)
    if not result: return redirect(url_for("details"))
    buf=io.BytesIO(); pdf=canvas.Canvas(buf,pagesize=A4); w,h=A4
    y=h-22*mm
    pdf.setTitle("AI Student Performance Report")
    pdf.setFont("Helvetica-Bold",18); pdf.drawString(20*mm,y,"AI Student Performance Report"); y-=10*mm
    pdf.setFont("Helvetica",10); pdf.drawString(20*mm,y,f"Student: {result['name']}"); y-=6*mm
    pdf.drawString(20*mm,y,f"Branch: {result['branch']} | Year: {result['year']} | Semester: {result['semester']}"); y-=10*mm
    pdf.setFont("Helvetica-Bold",14); pdf.drawString(20*mm,y,f"Performance: {result['label']} ({result['score']}%)"); y-=9*mm
    pdf.setFont("Helvetica",10); pdf.drawString(20*mm,y,f"Attendance: {result['attendance']}% | Study hours/day: {result['study_hours']}"); y-=12*mm
    pdf.setFont("Helvetica-Bold",11); pdf.drawString(20*mm,y,"Subject Performance"); y-=7*mm
    for s in result["all_subjects"]:
        pdf.setFont("Helvetica",10); pdf.drawString(25*mm,y,f"{s['name'][:55]}: {s['mark']}%" + ("  [FOCUS]" if s['weak'] else "")); y-=5.5*mm
        if y<25*mm: pdf.showPage(); y=h-20*mm
    y-=5*mm; pdf.setFont("Helvetica-Bold",11); pdf.drawString(20*mm,y,"Recommended Study Plan"); y-=7*mm
    pdf.setFont("Helvetica",9)
    for d,sub,focus,t in result["plan"]:
        pdf.drawString(25*mm,y,f"{d}: {sub} - {focus} ({t})"); y-=5.5*mm
        if y<20*mm: pdf.showPage(); y=h-20*mm
    pdf.showPage(); pdf.save(); buf.seek(0)
    return send_file(buf,as_attachment=True,download_name="AI_Student_Performance_Report.pdf",mimetype="application/pdf")

def is_admin():
    email_match=bool(ADMIN_EMAIL) and session.get("user_email")==ADMIN_EMAIL
    phone_match=bool(ADMIN_PHONE) and normalize_phone(session.get("user_phone",""))==normalize_phone(ADMIN_PHONE)
    return email_match or phone_match

def is_faculty():
    return session.get("user_role")=="faculty"

@app.route("/admin")
def admin():
    if not session.get("user_id"): return redirect(url_for("login"))
    c=get_db(); users=c.execute("SELECT id,name,email,phone FROM users ORDER BY id DESC").fetchall(); preds=c.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT 50").fetchall(); c.close()
    # For demo use, the configured ADMIN_EMAIL is the only account allowed. Set it on Render.
    if not is_admin():
        return render_template("message.html",title="Admin access",message="Admin access is restricted." if (ADMIN_EMAIL or ADMIN_PHONE) else "Admin access is disabled until ADMIN_EMAIL or ADMIN_PHONE is configured in your environment.")
    return render_template("admin.html",users=users,preds=preds)

@app.route("/api/catalog-subjects")
def api_catalog_subjects():
    if not session.get("user_id"): return jsonify({"subjects":[]})
    branch=request.args.get("branch","CSE")
    year=request.args.get("year","1")
    sem=request.args.get("semester","1")
    semester_no=(int(year)-1)*2+int(sem)
    subjects=CATALOG.get(branch,CATALOG["CSE"]).get(str(semester_no),[])
    return jsonify({"subjects":subjects})

def save_notes_pdf(branch, regulation, year, sem, subject, file, uploader_email):
    if not subject:
        return "Please choose a subject.", None
    if not file or file.filename=="":
        return "Please choose a PDF file.", None
    if not file.filename.lower().endswith(".pdf"):
        return "Only PDF files are allowed.", None
    file.seek(0,os.SEEK_END); size_mb=file.tell()/(1024*1024); file.seek(0)
    if size_mb>MAX_PDF_MB:
        return f"File too large. Max size is {MAX_PDF_MB} MB.", None
    safe_subject=secure_filename(subject.lower().replace(" ","-"))[:60]
    stored_name=f"{branch}_{regulation}_{year}_{sem}_{safe_subject}_{secrets.token_hex(4)}.pdf"
    stored_name=secure_filename(stored_name)
    file.save(os.path.join(NOTES_UPLOAD_DIR, stored_name))
    c=get_db()
    existing=c.execute("SELECT id,stored_name FROM notes_files WHERE branch=? AND regulation=? AND year=? AND semester=? AND subject=?",
                        (branch,regulation,year,sem,subject)).fetchone()
    if existing:
        old_path=os.path.join(NOTES_UPLOAD_DIR, existing["stored_name"])
        if os.path.exists(old_path):
            try: os.remove(old_path)
            except OSError: pass
        c.execute("UPDATE notes_files SET stored_name=?,original_name=?,uploaded_by=?,created_at=CURRENT_TIMESTAMP WHERE id=?",
                  (stored_name, secure_filename(file.filename), uploader_email, existing["id"]))
    else:
        c.execute("INSERT INTO notes_files(branch,regulation,year,semester,subject,stored_name,original_name,uploaded_by) VALUES(?,?,?,?,?,?,?,?)",
                  (branch,regulation,year,sem,subject,stored_name,secure_filename(file.filename),uploader_email))
    c.commit(); c.close()
    return None, f"Uploaded notes PDF for {subject} ({branch} {regulation} Y{year}S{sem})."

@app.route("/admin/notes",methods=["GET","POST"])
def admin_notes():
    if not session.get("user_id"): return redirect(url_for("login"))
    if not is_admin():
        return render_template("message.html",title="Admin access",message="Admin access is restricted." if (ADMIN_EMAIL or ADMIN_PHONE) else "Admin access is disabled until ADMIN_EMAIL or ADMIN_PHONE is configured in your environment.")
    error=""; success=""
    if request.method=="POST":
        branch=request.form.get("branch","CSE"); regulation=request.form.get("regulation","R20")
        year=request.form.get("year","1"); sem=request.form.get("semester","1")
        subject=request.form.get("subject","").strip()
        file=request.files.get("pdf_file")
        error, success = save_notes_pdf(branch, regulation, year, sem, subject, file, session.get("user_email",""))
    c=get_db(); files=c.execute("SELECT * FROM notes_files ORDER BY id DESC").fetchall(); c.close()
    return render_template("admin_notes.html",catalog=CATALOG,regulations=REGULATIONS,error=error,success=success,files=files)

@app.route("/admin/notes/delete/<int:file_id>",methods=["POST"])
def admin_notes_delete(file_id):
    if not session.get("user_id") or not is_admin():
        return redirect(url_for("login"))
    c=get_db()
    row=c.execute("SELECT * FROM notes_files WHERE id=?", (file_id,)).fetchone()
    if row:
        path=os.path.join(NOTES_UPLOAD_DIR, row["stored_name"])
        if os.path.exists(path):
            try: os.remove(path)
            except OSError: pass
        c.execute("DELETE FROM notes_files WHERE id=?", (file_id,))
        c.commit()
    c.close()
    return redirect(url_for("admin_notes"))

@app.route("/faculty-desk",methods=["GET","POST"])
def faculty_desk():
    if not session.get("user_id"): return redirect(url_for("login"))
    if not is_faculty():
        return render_template("message.html",title="Faculty Desk",message="Faculty Desk is available to accounts registered with the Faculty role.")
    error=""; success=""
    if request.method=="POST":
        branch=request.form.get("branch","CSE"); regulation=request.form.get("regulation","R20")
        year=request.form.get("year","1"); sem=request.form.get("semester","1")
        subject=request.form.get("subject","").strip()
        file=request.files.get("pdf_file")
        error, success = save_notes_pdf(branch, regulation, year, sem, subject, file, session.get("user_email",""))
    c=get_db(); files=c.execute("SELECT * FROM notes_files ORDER BY id DESC").fetchall(); c.close()
    return render_template("faculty_desk.html",catalog=CATALOG,regulations=REGULATIONS,error=error,success=success,
                            files=files,my_email=session.get("user_email",""))

@app.route("/faculty-desk/delete/<int:file_id>",methods=["POST"])
def faculty_desk_delete(file_id):
    if not session.get("user_id") or not is_faculty():
        return redirect(url_for("login"))
    c=get_db()
    row=c.execute("SELECT * FROM notes_files WHERE id=?", (file_id,)).fetchone()
    if row and row["uploaded_by"]==session.get("user_email",""):
        path=os.path.join(NOTES_UPLOAD_DIR, row["stored_name"])
        if os.path.exists(path):
            try: os.remove(path)
            except OSError: pass
        c.execute("DELETE FROM notes_files WHERE id=?", (file_id,))
        c.commit()
    c.close()
    return redirect(url_for("faculty_desk"))

@app.route("/notes/file/<int:file_id>")
def notes_file(file_id):
    if not session.get("user_id"): return redirect(url_for("login"))
    c=get_db()
    row=c.execute("SELECT * FROM notes_files WHERE id=?", (file_id,)).fetchone()
    c.close()
    if not row: return render_template("message.html",title="Not found",message="This notes PDF is not available anymore.")
    path=os.path.join(NOTES_UPLOAD_DIR, row["stored_name"])
    if not os.path.exists(path):
        return render_template("message.html",title="Not found",message="This notes PDF is not available anymore.")
    return send_file(path, mimetype="application/pdf", as_attachment=False, download_name=row["original_name"])

def find_subject_in_text(msg, subjects):
    msg_words = [w for w in msg.split() if len(w)>=3]
    for s in subjects:
        sname=s["name"].lower()
        if sname in msg: return s
        words=[w for w in re.split(r'[\s/&-]+', sname) if len(w)>2]
        for w in words:
            if w in msg: return s
            for mw in msg_words:
                if len(w)>=4 and len(mw)>=4 and (w.startswith(mw[:4]) or mw.startswith(w[:4])):
                    return s
    return None

@app.route("/api/chat",methods=["POST"])
def chat():
    if not session.get("user_id"): return jsonify({"reply":"Please login first."}),401
    raw=(request.get_json(silent=True) or {}).get("message","").strip()
    msg=re.sub(r'[^a-z0-9\s]', ' ', raw.lower())
    uname=session.get("user_name","there").split(" ")[0]
    result=build_result(latest_prediction())

    if not msg:
        return jsonify({"reply":"Ask me about your score, weak subjects, study plan, attendance, a specific subject's marks, CGPA, notes, or your PDF report."})

    # Greetings
    if re.search(r'\b(hi|hii|hey|hello|hai)\b', msg) and len(msg.split())<=3:
        return jsonify({"reply":f"Hi {uname}! I can tell you about your score, weak subjects, study plan, attendance, subject marks, CGPA, notes, or history. What would you like to know?"})
    if re.search(r'\b(thanks|thank you|thank u|thankyou)\b', msg):
        return jsonify({"reply":"You're welcome! Let me know if you need anything else. 🙂"})
    if re.search(r'\b(bye|goodbye|see you)\b', msg):
        return jsonify({"reply":f"Good luck with your studies, {uname}! Come back anytime."})
    if re.search(r'\b(help|what can you do|options|commands)\b', msg):
        return jsonify({"reply":"I can help with: your latest score, weak subjects, a specific subject's marks (e.g. \"marks in DBMS\"), the 7-day study plan, attendance, average/best score history, CGPA/SGPA calculator, notes for a subject, downloading your PDF report, and password reset."})

    # Specific subject mark lookup
    if result and result.get("all_subjects") and re.search(r'\b(mark|marks|score|grade)\b', msg) and ("in " in msg or "for " in msg):
        found=find_subject_in_text(msg, result["all_subjects"])
        if found:
            weak_note=" This is one of your weaker subjects — check the Notes page for extra material." if found["weak"] else ""
            return jsonify({"reply":f"Your marks in {found['name']} are {found['mark']}%.{weak_note}"})

    # Weak subjects
    if re.search(r'\bweak\b', msg) or ("subject" in msg and re.search(r'\b(priority|focus|improve|low)\b', msg)):
        if result and result["weak"]:
            items=", ".join(f"{x['name']} ({x['mark']}%)" for x in result["weak"])
            return jsonify({"reply":f"Your priority subjects are: {items}. Visit the Notes page for study material on these."})
        return jsonify({"reply":"Enter your performance details first on the Student Prediction page, and I'll tell you your weak subjects."})

    # Score / performance / pass-fail
    if re.search(r'\b(score|performance|passing|pass|fail|result)\b', msg):
        if result:
            return jsonify({"reply":f"Your latest predicted performance is {result['score']}% ({result['label']}). {result['message']}"})
        return jsonify({"reply":"No prediction is available yet — fill in your details on the Student Prediction page first."})

    # Attendance
    if "attendance" in msg:
        if result:
            note = " That's below the usual 75% requirement — try to attend more classes." if float(result['attendance'])<75 else " That's a healthy attendance level, keep it up!"
            return jsonify({"reply":f"Your latest attendance is {result['attendance']}%.{note}"})
        return jsonify({"reply":"Enter your attendance on the Student Prediction page first."})

    # Study plan
    if re.search(r'\b(plan|study|schedule|routine)\b', msg):
        if result and result["plan"]:
            lines=[f"{d}: {topic} — {task} ({dur})" for d,topic,task,dur in result["plan"]]
            return jsonify({"reply":"Here's your 7-day plan:\n" + "\n".join(lines)})
        return jsonify({"reply":"Complete a prediction first on the Student Prediction page — I'll build a personalized 7-day plan around your weak subjects."})

    # History / average / best / trend
    if re.search(r'\b(history|average|avg|best|trend|improving|progress)\b', msg):
        c=get_db()
        rows=c.execute("SELECT score FROM predictions WHERE user_id=? ORDER BY id ASC",(session["user_id"],)).fetchall()
        c.close()
        if rows:
            scores=[float(r["score"]) for r in rows]
            avg=round(statistics.mean(scores),2); best=round(max(scores),2)
            trend=""
            if len(scores)>=2:
                trend = " You're trending upward! 📈" if scores[-1]>scores[-2] else (" Your last score dipped a bit — review your weak subjects." if scores[-1]<scores[-2] else "")
            return jsonify({"reply":f"You have {len(scores)} prediction(s). Average score: {avg}%, Best score: {best}%.{trend} Check the History page for full details."})
        return jsonify({"reply":"No prediction history yet — complete a prediction to start tracking your progress."})

    # CGPA / SGPA
    if re.search(r'\b(cgpa|sgpa|gpa|grade point)\b', msg):
        return jsonify({"reply":"Use the CGPA page (top navigation) — enter Internal marks (/30) and your External Grade per subject to get your SGPA, or enter each semester's SGPA and credits to get your overall CGPA."})

    # Notes / video lectures
    if re.search(r'\b(notes|material|pdf notes|video|lecture)\b', msg) and "report" not in msg:
        subj_hint=""
        if result and result.get("all_subjects"):
            found=find_subject_in_text(msg, result["all_subjects"])
            if found:
                subj_hint=f" For {found['name']}, check the Notes page and search for it — you'll get a direct PDF or video link."
        return jsonify({"reply":"Visit the Notes page (top navigation) — pick your Branch, Regulation, Year and Semester, then use the search box to find any subject's notes and video lectures." + subj_hint})

    # Report / PDF
    if re.search(r'\b(report|download)\b', msg):
        return jsonify({"reply":"Go to your Dashboard and click \"Download PDF Report\" to get your full performance report as a PDF."})

    # Password / login
    if re.search(r'\b(password|login|forgot|otp)\b', msg):
        return jsonify({"reply":"To reset your password, log out and click \"Forgot Password?\" on the login page — you'll get an OTP to verify before setting a new password."})

    # Admin
    if is_admin() and re.search(r'\b(admin|upload notes|manage)\b', msg):
        return jsonify({"reply":"As admin, use the Admin tab to view students and predictions, and the \"Upload Notes PDFs\" option on the Notes page to add official subject notes."})

    return jsonify({"reply":"I'm not sure about that yet — try asking about your score, weak subjects, a subject's marks, study plan, attendance, CGPA, notes, history, or PDF report."})

@app.route("/")
def home():
    return redirect(url_for("details") if session.get("user_id") else url_for("login"))

@app.route("/api/subjects")
def api_subjects():
    branch=request.args.get("branch","CSE")
    year=request.args.get("year","1")
    sem=request.args.get("semester","1")
    semester_no=(int(year)-1)*2+int(sem)
    subjects=CATALOG.get(branch,CATALOG["CSE"]).get(str(semester_no),[])
    if session.get("user_id"):
        c=get_db()
        row=c.execute("SELECT subjects FROM custom_subjects WHERE user_id=? AND branch=? AND year=? AND semester=?",
                      (session["user_id"],branch,year,sem)).fetchone()
        c.close()
        if row and row[0]: subjects=row[0].split("|")
    return jsonify({"subjects":subjects,"semester_number":semester_no})

@app.route("/api/save-subjects",methods=["POST"])
def save_subjects():
    if not session.get("user_id"): return jsonify({"ok":False,"error":"Login required"}),401
    data=request.get_json(force=True)
    branch=str(data.get("branch","CSE")); year=str(data.get("year","1")); sem=str(data.get("semester","1"))
    subjects=[str(x).strip() for x in data.get("subjects",[]) if str(x).strip()]
    if not subjects: return jsonify({"ok":False,"error":"Enter at least one subject"}),400
    subjects=subjects[:10]
    c=get_db()
    c.execute("INSERT INTO custom_subjects(user_id,branch,year,semester,subjects) VALUES(?,?,?,?,?) ON CONFLICT(user_id,branch,year,semester) DO UPDATE SET subjects=excluded.subjects",
              (session["user_id"],branch,year,sem,"|".join(subjects)))
    c.commit(); c.close()
    return jsonify({"ok":True,"subjects":subjects})

@app.route("/cgpa")
def cgpa_calculator():
    if not session.get("user_id"): return redirect(url_for("login"))
    return render_template("cgpa.html")

@app.route("/notes")
def notes():
    if not session.get("user_id"): return redirect(url_for("login"))
    branch=request.args.get("branch","CSE")
    regulation=request.args.get("regulation","R20")
    year=request.args.get("year","1")
    sem=request.args.get("semester","1")
    if regulation not in REGULATIONS: regulation="R20"
    semester_no=(int(year)-1)*2+int(sem)
    subject_names=CATALOG.get(branch,CATALOG["CSE"]).get(str(semester_no),[])
    c=get_db()
    pdf_rows=c.execute("SELECT * FROM notes_files WHERE branch=? AND regulation=? AND year=? AND semester=?",
                        (branch,regulation,year,sem)).fetchall()
    c.close()
    pdf_by_subject={r["subject"]:r for r in pdf_rows}
    subjects=[]
    for n in subject_names:
        item={"name":n, **regulation_resources(n,regulation)}
        pdf=pdf_by_subject.get(n)
        item["pdf_id"]=pdf["id"] if pdf else None
        subjects.append(item)
    return render_template("notes.html",catalog=CATALOG,regulations=REGULATIONS,branch=branch,
                            regulation=regulation,year=year,semester=sem,subjects=subjects,is_admin=is_admin())

def normalize_phone(s):
    digits=re.sub(r'[^0-9]', '', s or '')
    return digits[-10:] if len(digits)>10 else digits

@app.route("/register",methods=["GET","POST"])
def register():
    error=""
    if request.method=="POST":
        try:
            c=get_db()
            phone_norm=normalize_phone(request.form["phone"])
            role="faculty" if request.form.get("role")=="faculty" else "student"
            c.execute("INSERT INTO users(name,email,phone,password,role) VALUES(?,?,?,?,?)",
                      (request.form["name"],request.form["email"],phone_norm,generate_password_hash(request.form["password"]),role))
            c.commit(); c.close(); return redirect(url_for("login"))
        except sqlite3.IntegrityError: error="Email or phone number is already registered."
        except Exception as e:
            if psycopg2 and isinstance(e, psycopg2.IntegrityError):
                error="Email or phone number is already registered."
            else:
                raise
    return render_template("register.html",error=error)

@app.route("/login",methods=["GET","POST"])
def login():
    error=""
    if request.method=="POST":
        x=request.form["identity"].strip()
        x_phone=normalize_phone(x)
        c=get_db()
        row=c.execute("SELECT id,name,email,phone,password,role FROM users WHERE email=? OR phone=? OR phone=?", (x,x,x_phone)).fetchone()
        password_ok=False
        if row:
            stored=row["password"]
            try:
                password_ok=check_password_hash(stored, request.form["password"])
            except (ValueError, TypeError):
                password_ok=(stored == request.form["password"])
                if password_ok:
                    c.execute("UPDATE users SET password=? WHERE id=?", (generate_password_hash(request.form["password"]), row["id"]))
                    c.commit()
        c.close()
        if row and password_ok:
            session["user_id"]=row["id"]
            session["user_name"]=row["name"]
            session["user_email"]=row["email"]
            session["user_phone"]=row["phone"]
            session["user_role"]=row["role"] or "student"
            return redirect(url_for("details"))
        error="Invalid email/phone or password."
    return render_template("login.html",error=error)

def _new_otp():
    return f"{secrets.randbelow(1000000):06d}"

@app.route("/forgot-password",methods=["GET","POST"])
def forgot_password():
    error=""; info=""; dev_otp=""
    if request.method=="POST":
        identity=request.form.get("identity","").strip()
        c=get_db()
        row=c.execute("SELECT id,name,email FROM users WHERE email=? OR phone=?", (identity,identity)).fetchone()
        if row and row["email"]:
            otp=_new_otp()
            expires=(datetime.utcnow()+timedelta(minutes=OTP_VALID_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO password_resets(user_id,email,otp_hash,expires_at,attempts,verified) VALUES(?,?,?,?,0,0)",
                      (row["id"], row["email"], generate_password_hash(otp), expires))
            c.commit()
            c.close()
            sent=send_otp_email(row["email"], row["name"], otp)
            session["reset_pending_id"]=row["id"]
            session["reset_pending_email"]=row["email"]
            if sent:
                info="An OTP has been sent to your registered email."
            else:
                # Dev fallback: SMTP not configured, show the OTP directly so the flow is still testable.
                info="Email delivery is not configured on this server. Your OTP for testing is shown below."
                dev_otp=otp
            return render_template("forgot_password.html",error=error,info=info,dev_otp=dev_otp,sent_step=True)
        else:
            c.close()
            error="No account found with that email or phone."
    return render_template("forgot_password.html",error=error,info=info,dev_otp=dev_otp,sent_step=False)

@app.route("/verify-otp",methods=["GET","POST"])
def verify_otp():
    if not session.get("reset_pending_id"):
        return redirect(url_for("forgot_password"))
    error=""
    if request.method=="POST":
        entered=request.form.get("otp","").strip()
        c=get_db()
        row=c.execute("SELECT * FROM password_resets WHERE user_id=? ORDER BY id DESC LIMIT 1",(session["reset_pending_id"],)).fetchone()
        if not row:
            error="No OTP request found. Please request a new one."
        elif row["attempts"]>=OTP_MAX_ATTEMPTS:
            error="Too many incorrect attempts. Please request a new OTP."
        elif datetime.utcnow()>datetime.strptime(str(row["expires_at"])[:19], "%Y-%m-%d %H:%M:%S"):
            error="This OTP has expired. Please request a new one."
        elif check_password_hash(row["otp_hash"], entered):
            c.execute("UPDATE password_resets SET verified=1 WHERE id=?", (row["id"],))
            c.commit()
            session["reset_verified_id"]=session["reset_pending_id"]
            c.close()
            return redirect(url_for("reset_password"))
        else:
            c.execute("UPDATE password_resets SET attempts=attempts+1 WHERE id=?", (row["id"],))
            c.commit()
            error="Incorrect OTP. Please try again."
        c.close()
    return render_template("verify_otp.html",error=error,email=session.get("reset_pending_email",""))

@app.route("/reset-password",methods=["GET","POST"])
def reset_password():
    if not session.get("reset_verified_id"):
        return redirect(url_for("forgot_password"))
    error=""
    if request.method=="POST":
        p1=request.form.get("password",""); p2=request.form.get("confirm_password","")
        if len(p1)<6:
            error="Password must be at least 6 characters."
        elif p1!=p2:
            error="Passwords do not match."
        else:
            c=get_db()
            c.execute("UPDATE users SET password=? WHERE id=?", (generate_password_hash(p1), session["reset_verified_id"]))
            c.commit(); c.close()
            session.pop("reset_pending_id",None); session.pop("reset_pending_email",None); session.pop("reset_verified_id",None)
            flash("Password reset successful. Please log in with your new password.")
            return redirect(url_for("login"))
    return render_template("reset_password.html",error=error)

@app.route("/api/saved-subjects")
def saved_subjects():
    if not session.get("user_id"):
        return jsonify({"subjects":[]})
    branch=request.args.get("branch","")
    year=request.args.get("year","")
    sem=request.args.get("semester","")
    c=get_db()
    row=c.execute("""SELECT subjects FROM custom_subjects
                     WHERE user_id=? AND branch=? AND year=? AND semester=?""",
                  (session["user_id"],branch,year,sem)).fetchone()
    c.close()
    return jsonify({"subjects": row[0].split("|") if row and row[0] else []})

@app.route("/details",methods=["GET","POST"])
def details():
    if not session.get("user_id"): return redirect(url_for("login"))
    error=""
    if request.method=="POST":
        try:
            year=request.form["year"]; sem=request.form["semester"]; branch=request.form["branch"]
            count=int(request.form.get("subject_count","5"))
            names=[request.form[f"subject{i}_name"].strip() for i in range(1,count+1)]
            marks=[float(request.form[f"subject{i}"]) for i in range(1,count+1)]
            assigns=[float(request.form[f"assignment{i}"]) for i in range(1,count+1)]
            internals=[float(request.form[f"internal{i}"]) for i in range(1,count+1)]
            attendance=float(request.form["attendance"]); study=float(request.form["study_hours"])
            if len(names)<2: raise ValueError("Please enter at least 2 subjects.")
            if not all(names): raise ValueError("Please enter a name for every subject.")
            if any(x<0 or x>100 for x in [attendance]): raise ValueError("Attendance must be between 0 and 100.")
            if any(x<0 or x>70 for x in marks): raise ValueError("External marks must be between 0 and 70.")
            if any(x<0 or x>30 for x in internals): raise ValueError("Internal marks must be between 0 and 30.")
            if any(x<0 or x>25 for x in assigns): raise ValueError("Assignment marks must be between 0 and 25.")
            # Convert each component to percentage before combining so the model is scale-independent.
            ext_pct=[m/70*100 for m in marks]
            int_pct=[m/30*100 for m in internals]
            ass_pct=[m/25*100 for m in assigns]
            avg=sum(ext_pct)/len(ext_pct)
            score=round(attendance*.25+avg*.35+sum(ass_pct)/len(ass_pct)*.10+sum(int_pct)/len(int_pct)*.20+min(study*10,100)*.10,2)
            label="Excellent" if score>=80 else "Good" if score>=65 else "Average" if score>=50 else "Needs Improvement"
            message={"Excellent":"Excellent performance. Keep your routine.",
                     "Good":"Good performance. Strengthen the weaker subjects.",
                     "Average":"Follow the study plan consistently and practice more.",
                     "Needs Improvement":"Focus on weak subjects and revise every day."}[label]
            weak=sorted(zip(names,ext_pct),key=lambda x:x[1])[:2]
            weak_names={n for n,_ in weak}
            all_subjects=[
                {"name":n,"mark":round(m,2),"notes":resources(n)[0],"video":resources(n)[1],
                 "weak":n in weak_names}
                for n,m in zip(names,ext_pct)
            ]
            weak_data=[{"name":n,"mark":m,"notes":resources(n)[0],"video":resources(n)[1]} for n,m in weak]
            plan=[
              ("Day 1",weak_data[0]["name"],"Concepts + notes","60 min"),
              ("Day 2",weak_data[1]["name"],"Concepts + examples","60 min"),
              ("Day 3",weak_data[0]["name"],"Practice questions","75 min"),
              ("Day 4",weak_data[1]["name"],"Practice problems","75 min"),
              ("Day 5",weak_data[0]["name"],"Revision + previous questions","60 min"),
              ("Day 6",weak_data[1]["name"],"Revision + previous questions","60 min"),
              ("Day 7","Both weak subjects","Mock test + error review","90 min")]
            c=get_db()
            c.execute("INSERT INTO custom_subjects(user_id,branch,year,semester,subjects) VALUES(?,?,?,?,?) ON CONFLICT(user_id,branch,year,semester) DO UPDATE SET subjects=excluded.subjects",
                      (session["user_id"],branch,year,sem,"|".join(names)))
            c.execute("""INSERT INTO predictions(user_id,name,year,semester,branch,attendance,subject_names,subject_marks,assignment_marks,internal_marks,study_hours,prediction,score)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",(session["user_id"],request.form["name"],year,sem,branch,attendance,
            "|".join(names),"|".join(map(str,marks)),"|".join(map(str,assigns)),"|".join(map(str,internals)),study,label,score))
            c.commit(); c.close()
            session["result"]={"score":score,"label":label,"message":message,"weak":weak_data,
                               "all_subjects":all_subjects,"plan":plan,
                               "year":year,"semester":sem,"branch":branch,"name":request.form["name"],
                               "attendance":attendance,"study_hours":study}
            send_prediction_email(session.get("user_email",""), session["result"])
            return redirect(url_for("prediction"))
        except ValueError as e: error=str(e)
    return render_template("details.html",catalog=CATALOG,user_name=session.get("user_name",""),error=error)

@app.route("/prediction")
def prediction():
    if not session.get("user_id"): return redirect(url_for("login"))
    return render_template("prediction.html",result=session.get("result"))

@app.route("/history")
def history():
    if not session.get("user_id"): return redirect(url_for("login"))
    c=get_db()
    rows=c.execute("SELECT * FROM predictions WHERE user_id=? ORDER BY id DESC",(session["user_id"],)).fetchall()
    c.close(); return render_template("history.html",rows=rows)

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("login"))

init_db()

@app.route("/db-status")
def db_status():
    if not session.get("user_id"): return jsonify({"error":"Login required"}),401
    return jsonify({"database":"PostgreSQL" if using_postgres() else "SQLite (local fallback)","persistent":using_postgres()})

@app.route("/health")
def health():
    try:
        c=get_db(); c.execute("SELECT 1").fetchone(); c.close()
        return jsonify({"status":"ok","service":"AI Student Performance System"})
    except Exception:
        return jsonify({"status":"error"}),500

@app.route("/robots.txt")
def robots():
    return "User-agent: *\nAllow: /\nDisallow: /admin\n", 200, {"Content-Type":"text/plain"}

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)
