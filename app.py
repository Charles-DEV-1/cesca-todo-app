from flask import Flask, render_template, session, redirect, request, flash, url_for
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.secret_key = "wudwjcdjnfoqsnmefvxjienvj"
app.permanent_session_lifetime = timedelta(days=2)

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///cesca.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'Cesca1Mul@gmail.com'   # your app email
app.config['MAIL_PASSWORD'] = 'rpqg ctjg vdru zsli'
app.config["MAIL_DEBUG"] = True

mail = Mail(app)

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # make longer for hashing

    # Relationship
    tasks = db.relationship('Task', backref='user', lazy=True)

# Task Model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_title = db.Column(db.String(100), nullable=False)
    task_description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods= ["POST","GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, request.form["password"]):
            session["username"] = user.username
            session["user_id"] = user.id
            flash("Logged in succesfully!","success")
            return redirect(url_for("dashboard"))
        flash("Invalid credentials!","warning")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/register", methods=["POST","GET"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        hwz = generate_password_hash(password)
        username = request.form["username"]

        # ✅ Check for existing username or email
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            flash("Username or Email already exists!", "warning")
            return redirect(url_for("register"))

        # ✅ Create and save user first
        user = User(name=name, username=username, email=email, password=hwz)
        db.session.add(user)
        db.session.commit()

        flash("Account created!", "success")

        # ✅ Try sending mail (but don’t block login if it fails)
        try:
            msg = Message(
                subject="Welcome to Cesca Todo App",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email]
            )
            msg.body = (
                f"Hello {username},\n\n"
                "Thanks for joining Cesca Todo! 🎉\n"
                "We’re excited to help you stay organized. "
                "Start adding your first task and see how easy it is to track your goals!"
            )
            mail.send(msg)
        except Exception as e:
            print("⚠️ Email sending failed:", e)

        # ✅ Always redirect after successful registration
        return redirect(url_for("login"))

    else:
        if "user_id" in session:
            return redirect(url_for("dashboard"))
    return render_template("register.html")



@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please login!", "warning")
        return redirect(url_for("login"))

    tasks = Task.query.filter_by(user_id=session["user_id"]).all()
    return render_template("dashboard.html", tasks=tasks, username=session["username"])


@app.route("/add_task", methods=["POST"])
def add_task():
    if "user_id" in session:  # ✅ check correct session key
        title = request.form["title"]
        description = request.form["description"]

        task = Task(
            task_title=title,
            task_description=description,
            user_id=session["user_id"]  # ✅ link to logged-in user
        )
        db.session.add(task)
        db.session.commit()

        flash("Task added successfully!", "success")
        return redirect(url_for("dashboard"))
    else:
        flash("Please login to add tasks!", "warning")
        return redirect(url_for("login"))


@app.route("/edit_task/<int:id>", methods=["POST", "GET"])
def edit_task(id):
    if "user_id" not in session:
        flash("Please login!", "warning")
        return redirect(url_for("login"))

    task = Task.query.get_or_404(id)

    if request.method == "POST":
        task.task_title = request.form["title"]
        task.task_description = request.form["description"]

        db.session.commit()  # ✅ save changes
        flash("Task edited successfully!", "success")
        return redirect(url_for("dashboard"))

    # ✅ Pass the task object so the form can be pre-filled
    return render_template("edit_task.html", task=task)

@app.route("/delete_task/<int:id>", methods=["POST", "GET"])
def delete_task(id):
    if "user_id" not in session:
        flash("Please login!", "warning")
        return redirect(url_for("login"))

    task = Task.query.get_or_404(id)

    # Make sure the task belongs to the logged-in user
    if task.user_id != session["user_id"]:
        flash("You are not authorized to delete this task!", "danger")
        return redirect(url_for("dashboard"))

    db.session.delete(task)
    db.session.commit()
    flash("Task deleted successfully!", "success")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Logout successfull!","success")
    return redirect(url_for("home"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)



