from flask import Flask, request, redirect, session
import os

app = Flask(__name__)
app.secret_key = "secret"

# ---------------------------
# UI TEMPLATE
# ---------------------------
def render_page(content):
    return f"""
    <html>
    <head>
        <title>Co-op System</title>
        <style>
            body {{
                margin: 0;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                background: radial-gradient(circle at top, #1f1f1f, #0a0a0a);
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                color: white;
            }}

            .card {{
                background: #1f1f1f;
                padding: 30px;
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                width: 90%;
                max-width: 420px;
                text-align: center;
                backdrop-filter: blur(10px);
            }}

            input, textarea {{
                width: 100%;
                padding: 10px;
                margin: 8px 0;
                border-radius: 8px;
                border: none;
                background: #2a2a2a;
                color: white;
            }}

            button {{
                width: 100%;
                padding: 10px;
                border: none;
                border-radius: 8px;
                background: #4CAF50;
                color: white;
                cursor: pointer;
                font-weight: bold;
            }}

            button:hover {{
                background: #45a049;
            }}

            a {{
                color: #4da6ff;
                text-decoration: none;
            }}

            a:hover {{
                text-decoration: underline;
            }}

            .box {{
                border: 1px solid #444;
                padding: 10px;
                margin: 10px 0;
                border-radius: 10px;
                text-align: left;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            {content}
        </div>
    </body>
    </html>
    """

# ---------------------------
# STORAGE
# ---------------------------
applications = []

users = {
    "student@test.com": {"password": "123", "role": "student"},
    "coord@test.com": {"password": "123", "role": "coordinator"},
    "sup@test.com": {"password": "123", "role": "supervisor"}
}

UPLOAD_FOLDER = "uploads"
MAX_SIZE = 5 * 1024 * 1024

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------------------------
# HOME
# ---------------------------
@app.route("/")
def home():
    return render_page("""
        <h1>Co-op Application System</h1>
        <a href="/login">Login</a>
    """)

# ---------------------------
# LOGIN
# ---------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = users.get(email)

        if user and user["password"] == password:
            session["role"] = user["role"]

            if user["role"] == "student":
                return redirect("/student")
            elif user["role"] == "coordinator":
                return redirect("/coordinator")
            else:
                return redirect("/supervisor")

        return render_page("<p>Invalid login</p><a href='/login'>Try again</a>")

    return render_page("""
        <h2>Login</h2>
        <form method="post">
            <input name="email" placeholder="Email">
            <input name="password" type="password" placeholder="Password">
            <button type="submit">Login</button>
        </form>
    """)

# ---------------------------
# STUDENT
# ---------------------------
@app.route("/student", methods=["GET", "POST"])
def student():
    if session.get("role") != "student":
        return "Access denied"

    if request.method == "POST":
        name = request.form.get("name")
        sid = request.form.get("id")
        email = request.form.get("email")
        file = request.files.get("report")

        if not name or not sid or not email:
            return render_page("<p>Error: Fill all fields</p>")

        report_filename = None

        if file and file.filename:
            if not file.filename.lower().endswith(".pdf"):
                return render_page("<p>Error: Only PDF files allowed</p>")

            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)

            if size > MAX_SIZE:
                return render_page("<p>Error: File too large</p>")

            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            report_filename = filepath

        applications.append({
            "name": name,
            "id": sid,
            "email": email,
            "status": "Pending",
            "final": "N/A",
            "report": report_filename,
            "evaluation": None
        })

        return render_page("<p>Application Submitted!</p><a href='/student'>Back</a>")

    return render_page("""
        <h2>Student Portal</h2>

        <form method="post" enctype="multipart/form-data">
            <input name="name" placeholder="Name">
            <input name="id" placeholder="Student ID">
            <input name="email" placeholder="Email">
            <input type="file" name="report">
            <button type="submit">Apply</button>
        </form>

        <h3>Check Status</h3>
        <form action="/status" method="post">
            <input name="id" placeholder="Student ID">
            <button type="submit">View Status</button>
        </form>

        <br><a href="/">Home</a>
    """)

# ---------------------------
# STATUS
# ---------------------------
@app.route("/status", methods=["POST"])
def status():
    sid = request.form.get("id")

    for app_data in applications:
        if app_data["id"] == sid:
            return render_page(f"""
                <p>Provisional: {app_data['status']}</p>
                <p>Final: {app_data['final']}</p>
                <p>Report Uploaded: {"Yes" if app_data["report"] else "No"}</p>
                <p>Evaluation Submitted: {"Yes" if app_data["evaluation"] else "No"}</p>
                <a href="/">Home</a>
            """)

    return render_page("<p>Student not found</p>")

# ---------------------------
# COORDINATOR
# ---------------------------
@app.route("/coordinator")
def coordinator():
    if session.get("role") != "coordinator":
        return "Access denied"

    filter_type = request.args.get("filter")

    if filter_type == "accepted":
        apps = [a for a in applications if a["status"] == "Accepted"]
    elif filter_type == "missing_reports":
        apps = [a for a in applications if not a["report"]]
    elif filter_type == "missing_evaluations":
        apps = [a for a in applications if not a["evaluation"]]
    else:
        apps = applications

    html = """
        <h2>Coordinator Dashboard</h2>
        <a href="/coordinator?filter=accepted">Accepted</a> |
        <a href="/coordinator?filter=missing_reports">Missing Reports</a> |
        <a href="/coordinator?filter=missing_evaluations">Missing Evaluations</a> |
        <a href="/coordinator">All</a><br><br>
    """

    for i, app_data in enumerate(apps):
        html += f"""
        <div class="box">
            <p>{app_data['name']} ({app_data['id']})</p>
            <p>Status: {app_data['status']}</p>
            <p>Final: {app_data['final']}</p>

            <a href='/update/{i}/accept'>Accept</a> |
            <a href='/update/{i}/reject'>Reject</a> |
            <a href='/update/{i}/final_accept'>Final Accept</a> |
            <a href='/update/{i}/final_reject'>Final Reject</a>
        </div>
        """

    html += "<br><a href='/'>Home</a>"
    return render_page(html)

# ---------------------------
# UPDATE
# ---------------------------
@app.route("/update/<int:index>/<action>")
def update(index, action):
    if session.get("role") != "coordinator":
        return "Access denied"

    if 0 <= index < len(applications):
        if action == "accept":
            applications[index]["status"] = "Accepted"
        elif action == "reject":
            applications[index]["status"] = "Rejected"
        elif action == "final_accept":
            applications[index]["final"] = "Final Accepted"
        elif action == "final_reject":
            applications[index]["final"] = "Final Rejected"

    return redirect("/coordinator")

# ---------------------------
# SUPERVISOR
# ---------------------------
@app.route("/supervisor", methods=["GET", "POST"])
def supervisor():
    if session.get("role") != "supervisor":
        return "Access denied"

    if request.method == "POST":
        sid = request.form.get("id")
        feedback = request.form.get("feedback")

        for app_data in applications:
            if app_data["id"] == sid:
                app_data["evaluation"] = feedback
                return render_page("<p>Evaluation Submitted</p>")

        return render_page("<p>Student not found</p>")

    return render_page("""
        <h2>Supervisor Portal</h2>
        <form method="post">
            <input name="id" placeholder="Student ID">
            <textarea name="feedback" placeholder="Feedback"></textarea>
            <button type="submit">Submit</button>
        </form>
        <br><a href="/">Home</a>
    """)

# ---------------------------
# RUN
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)