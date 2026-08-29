UPDATED FEATURES
- Subject names are entered by the student, so subjects display correctly.
- Lowest 2 subjects are automatically identified.
- Each weak subject gets a Notes link and a Video link.
- Known C/Python/DSA/DBMS/CN/OS/ML/AI/COA/Java etc. have topic-specific resources.
- Unknown subjects get a Google Notes search + YouTube tutorial search.
- Personalized 7-day study plan is generated from the 2 weakest subjects.
- Result includes Excellent / Good / Average / Needs Improvement.

IMPORTANT FOR UPDATING AN OLD COPY
This version changes the SQLite database structure. If you run an older copy,
delete its old student_performance.db once before starting this updated version,
or simply use a fresh extracted folder.

RUN:
cd /d "%USERPROFILE%\Desktop\AI_Student_Performance_System"
py -m pip install -r requirements.txt
py app.py

OPEN:
http://127.0.0.1:5000
