import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret")
UPLOADS = os.path.join(app.root_path, "uploads")
os.makedirs(UPLOADS, exist_ok=True)

def db():
    return mysql.connector.connect(host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"), password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "modshah_scholarship"))

def login_required(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return inner

def admin_required(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required.", "warning")
            return redirect(url_for("dashboard"))
        return fn(*args, **kwargs)
    return inner

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name, email, password = request.form["name"].strip(), request.form["email"].strip().lower(), request.form["password"]
        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "danger")
        else:
            try:
                c=db(); q=c.cursor()
                q.execute("INSERT INTO users(name,email,password_hash) VALUES(%s,%s,%s)",
                          (name,email,generate_password_hash(password)))
                c.commit(); q.close(); c.close()
                flash("Account created. Please log in.", "success")
                return redirect(url_for("login"))
            except Error:
                flash("Could not register. Check database settings or whether the email already exists.", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            c=db(); q=c.cursor(dictionary=True)
            q.execute("SELECT * FROM users WHERE email=%s", (request.form["email"].lower(),))
            u=q.fetchone(); q.close(); c.close()
            if u and check_password_hash(u["password_hash"], request.form["password"]):
                session.update(user_id=u["id"], name=u["name"], role=u["role"])
                return redirect(url_for("dashboard"))
            flash("Incorrect email or password.", "danger")
        except Error:
            flash("Database connection failed. Follow SETUP.md.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    c=db(); q=c.cursor(dictionary=True)
    q.execute("SELECT * FROM students WHERE user_id=%s", (session["user_id"],))
    profile=q.fetchone()
    q.execute("""SELECT s.*, a.status AS application_status FROM scholarships s
        LEFT JOIN applications a ON a.scholarship_id=s.id AND a.user_id=%s
        ORDER BY s.deadline IS NULL, s.deadline LIMIT 6""", (session["user_id"],))
    items=q.fetchall(); q.close(); c.close()
    return render_template("dashboard.html", profile=profile, scholarships=items)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        values=(request.form.get("education"), request.form.get("marks") or None,
          request.form.get("annual_income") or None, request.form.get("location"),
          request.form.get("category"), session["user_id"])
        c=db(); q=c.cursor()
        q.execute("""INSERT INTO students(education,marks,annual_income,location,category,user_id)
          VALUES(%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE education=VALUES(education),
          marks=VALUES(marks),annual_income=VALUES(annual_income),location=VALUES(location),category=VALUES(category)""", values)
        c.commit(); q.close(); c.close()
        flash("Profile saved.", "success")
        return redirect(url_for("dashboard"))
    c=db(); q=c.cursor(dictionary=True)
    q.execute("SELECT * FROM students WHERE user_id=%s", (session["user_id"],))
    student=q.fetchone(); q.close(); c.close()
    return render_template("profile.html", student=student)
@app.route("/scholarships")
@login_required
def scholarships():

    term = request.args.get("q", "").strip()
    selected_category = request.args.get("category", "").strip()
    selected_type = request.args.get("scheme_type", "").strip()
    selected_education = request.args.get("education_level", "").strip()

    conditions = []
    params = []

    # Search across all scholarship information
    if term:
        conditions.append("""
            (
                title LIKE %s OR
                provider LIKE %s OR
                description LIKE %s OR
                category LIKE %s OR
                scheme_type LIKE %s OR
                education_level LIKE %s
            )
        """)

        search = f"%{term}%"
        params.extend([search] * 6)

    # Category filter
    if selected_category:
        conditions.append("category = %s")
        params.append(selected_category)

    # Scholarship type filter
    if selected_type:
        conditions.append("scheme_type = %s")
        params.append(selected_type)

    # Education filter
    if selected_education:
        conditions.append("education_level = %s")
        params.append(selected_education)

    where_sql = " AND ".join(conditions) if conditions else "1=1"

    c = db()
    q = c.cursor(dictionary=True)

    # Retrieve all matching scholarships
    q.execute(f"""
        SELECT *
        FROM scholarships
        WHERE {where_sql}
        ORDER BY
            deadline IS NULL,
            deadline ASC,
            title ASC
    """, tuple(params))

    items = q.fetchall()

    # Total matching scholarships
    q.execute(f"""
        SELECT COUNT(*) AS total
        FROM scholarships
        WHERE {where_sql}
    """, tuple(params))

    total = q.fetchone()["total"]

    # Category-wise scholarship counts
    q.execute("""
        SELECT category, COUNT(*) AS total
        FROM scholarships
        GROUP BY category
        ORDER BY category
    """)

    category_counts = q.fetchall()

    # Available scholarship types
    q.execute("""
        SELECT DISTINCT scheme_type
        FROM scholarships
        WHERE scheme_type IS NOT NULL
        AND scheme_type != ''
        ORDER BY scheme_type
    """)

    scheme_types = q.fetchall()

    # Available education levels
    q.execute("""
        SELECT DISTINCT education_level
        FROM scholarships
        WHERE education_level IS NOT NULL
        AND education_level != ''
        ORDER BY education_level
    """)

    education_levels = q.fetchall()

    q.close()
    c.close()

    return render_template(
        "scholarships.html",
        scholarships=items,
        keyword=term,
        total=total,
        category_counts=category_counts,
        selected_category=selected_category,
        selected_type=selected_type,
        selected_education=selected_education,
        scheme_types=scheme_types,
        education_levels=education_levels
    )
@app.route("/apply/<int:sid>", methods=["POST"])
@login_required
def apply(sid):
    c=db(); q=c.cursor()
    q.execute("INSERT IGNORE INTO applications(user_id,scholarship_id) VALUES(%s,%s)", (session["user_id"],sid))
    c.commit(); q.close(); c.close()
    flash("Added to your tracker.", "success")
    return redirect(url_for("tracker"))

@app.route("/tracker")
@login_required
def tracker():
    c=db(); q=c.cursor(dictionary=True)
    q.execute("""SELECT a.id,a.status,a.applied_at,s.title,s.provider,s.deadline
      FROM applications a JOIN scholarships s ON s.id=a.scholarship_id
      WHERE a.user_id=%s ORDER BY a.applied_at DESC""", (session["user_id"],))
    items=q.fetchall(); q.close(); c.close()
    return render_template("tracker.html", applications=items)

@app.route("/tracker/update/<int:aid>", methods=["POST"])
@login_required
def update_tracker(aid):
    status=request.form.get("status")
    if status in {"Interested","Preparing","Submitted","Approved","Rejected"}:
        c=db(); q=c.cursor()
        q.execute("UPDATE applications SET status=%s WHERE id=%s AND user_id=%s", (status,aid,session["user_id"]))
        c.commit(); q.close(); c.close()
    return redirect(url_for("tracker"))

@app.route("/documents", methods=["GET","POST"])
@login_required
def documents():
    allowed={"pdf","png","jpg","jpeg"}
    if request.method=="POST":
        f=request.files.get("document")
        if f and f.filename and "." in f.filename and f.filename.rsplit(".",1)[1].lower() in allowed:
            safe=secure_filename(f.filename)
            stored=f"{session['user_id']}_{int(datetime.now().timestamp())}_{safe}"
            f.save(os.path.join(UPLOADS,stored))
            c=db(); q=c.cursor()
            q.execute("INSERT INTO documents(user_id,original_name,stored_name) VALUES(%s,%s,%s)",(session["user_id"],safe,stored))
            c.commit(); q.close(); c.close()
            flash("Document uploaded.", "success")
        else:
            flash("Choose a PDF, PNG or JPG file.", "warning")
        return redirect(url_for("documents"))
    c=db(); q=c.cursor(dictionary=True)
    q.execute("SELECT * FROM documents WHERE user_id=%s ORDER BY uploaded_at DESC",(session["user_id"],))
    docs=q.fetchall(); q.close(); c.close()
    return render_template("documents.html", documents=docs)

@app.route("/assistant", methods=["GET","POST"])
@login_required
def assistant():
    answer=None
    if request.method=="POST":
        question=request.form.get("question","").lower()
        if "income" in question:
            answer="Check the official scholarship income limit and compare it with your annual family income."
        elif "mark" in question or "percentage" in question:
            answer="Check the minimum marks requirement in the official eligibility notice."
        elif "document" in question:
            answer="Common documents include marks cards, income certificate, ID proof, bank details and bonafide certificate. Requirements vary."
        elif "deadline" in question or "last date" in question:
            answer="Check the deadline in the listing and verify it on the provider's official website."
        else:
            answer="I can answer basic questions about marks, income, documents and deadlines. Verify important details with the official provider."
    return render_template("assistant.html", answer=answer)

@app.route("/admin")
@login_required
@admin_required
def admin():
    c=db(); q=c.cursor(dictionary=True)
    q.execute("SELECT COUNT(*) total FROM users"); users=q.fetchone()["total"]
    q.execute("SELECT COUNT(*) total FROM scholarships"); scholarship_count=q.fetchone()["total"]
    q.execute("SELECT COUNT(*) total FROM applications"); apps=q.fetchone()["total"]
    q.close(); c.close()
    return render_template("admin.html", users=users, scholarship_count=scholarship_count, apps=apps)

@app.route("/admin/add", methods=["POST"])
@login_required
@admin_required
def add_scholarship():
    c=db(); q=c.cursor()
    q.execute("""INSERT INTO scholarships(title,provider,description,amount,deadline,official_url,minimum_marks,income_limit)
      VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",
      (request.form["title"],request.form["provider"],request.form.get("description"),
       request.form.get("amount") or None,request.form.get("deadline") or None,
       request.form.get("official_url") or None,request.form.get("minimum_marks") or None,
       request.form.get("income_limit") or None))
    c.commit(); q.close(); c.close()
    flash("Scholarship added.", "success")
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True)
