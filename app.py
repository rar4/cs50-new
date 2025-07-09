from flask import Flask, render_template, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash


from markdown import markdown
from datetime import datetime

from generation import generate_idea
from utils import login_required, enter, db_exec, error
from fetch_image import fetch_image

app = Flask(__name__)

app.secret_key = "FooBarBaz"


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:

        f = request.form

        name = f["username"]
        passwd = f["password"]
        confirmation = f["confirmation"]

        if not name or not passwd or not confirmation:
            return error("Fill all the form")

        if passwd != confirmation:
            return error("Passwords do not match")

        pass_hash = generate_password_hash(passwd)

        if error_message := db_exec("INSERT INTO User (username, password_hash) VALUES (?, ?)", (name, pass_hash)):
            return error(error_message)

        if id := enter(name, passwd):
            session["user_id"] = id
            return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()
    if request.method == "GET":
        return render_template("login.html")
    else:

        if not (name := request.form.get("username")) or not (passwd := request.form.get("password")):
            return error("Fill all the form")

        if (id := enter(name, passwd)):
            print(id)
            session["user_id"] = id
            return redirect("/")
        else:
            return error("Wrong username or password")


@app.route("/", methods=["GET"])
@login_required
def index():
    session["prev_responces"] = []
    return render_template("index.html")


@app.route("/brainstorm")
@login_required
def brainstorm():

    if "topic" in request.args.keys():
        if request.args.get("topic"):

            responces = session.get("prev_responces")

            topic = request.args.get(
                "topic") + "which is not in " + ("" if responces == None else str(responces))

            text = generate_idea(topic)
            img = fetch_image(text)

            text = markdown(text)
            session["prev_responces"] = session.get("prev_responces") + [text,]
            print(session.get("prev_responces"))
            session["topic"] = request.args.get("topic")
            return render_template("brainstorm.html", text=text, img=img)
        
        return error("Write a topic")
    else:
        return redirect("/")


@app.route("/idea")
@login_required
def idea():
    if "title" in request.args.keys() and "img" in request.args.keys():
        if idea := request.args.get("title"):

            session.pop("prev_responces")

            img = request.args.get("img")
            desctiption = markdown(generate_idea(idea, False))

            arguments = (session.get("user_id"), session.get("topic"),
                         idea, img, str(datetime.now()), desctiption)


            db_exec("INSERT INTO BrainstormSession (user_id, topic, idea, image_url, timestamp, idea_description) VALUES (?, ?, ?, ?, ?, ?)", arguments)

            session.pop("topic")
            return render_template("idea.html", title=idea, img=img, desc=desctiption)
    else:
        return error("Enter a topic")


@app.route("/history")
@login_required
def history():
    if request.args.get("session_id"):
        rows = db_exec(
            "SELECT idea, description, id FROM BrainstormSession WHERE user_id = ? ORDER BY timestamp DESC", (session["user_id"],))
    else:
        rows = db_exec(
            "SELECT topic, idea, id FROM BrainstormSession WHERE user_id = ? ORDER BY timestamp DESC", (session["user_id"],))

        return render_template("history.html", rows=rows)


@app.route("/show-idea")
@login_required
def show_idea():
    if request.args.get("session_id"):
        row = db_exec("SELECT idea, idea_description, image_url FROM BrainstormSession WHERE id=?",
                      (request.args.get("session_id"), ))[0]

        return render_template("idea.html", img=row[2], desc=row[1], title=row[0])


@app.route("/logout", methods=["GET", "POST",])
@login_required
def logout():
    session.clear()
    return redirect("/login")
