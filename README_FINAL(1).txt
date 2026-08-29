AI STUDENT PERFORMANCE SYSTEM - FINAL VERSION

Features included:
- Register/Login with email and phone
- AI STUDENT PERFORMANCE SYSTEM branding
- 4 Years / 8 Semesters
- Branches: CSE, AI & ML, AI & DS, IT, ECE, EEE, MECH, CIVIL
- Year + Semester subject auto-display
- College-specific subject editing
- Add / Remove subjects (up to 10)
- Save My Semester Subjects for the logged-in student
- External marks: OUT OF 70
- Internal marks: OUT OF 30
- Assignment marks: OUT OF 25
- Attendance and Study Hours
- Performance prediction: Excellent / Good / Average / Needs Improvement
- Weak-subject detection
- Subject resource links for mapped subjects
- Personalized 7-day study plan
- Prediction history

IMPORTANT:
1. Extract this ZIP into a fresh folder.
2. If an old student_performance.db exists, delete it once before first run because this version adds a custom-subjects table.
3. Open CMD in the project folder.

RUN:
py -m pip install -r requirements.txt
py app.py

OPEN IN BROWSER:
http://127.0.0.1:5000

For each selected semester, edit the subject names if your college syllabus is different.
Click "Save My Semester Subjects" to remember the subjects for that Branch + Year + Semester.
