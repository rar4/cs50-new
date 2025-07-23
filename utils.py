from functools import wraps
from flask import redirect, render_template, session
import sqlite3
from werkzeug.security import check_password_hash
from smtplib import SMTP 


ADDRESS = "botnoreply55@gmail.com"

PASSWORD = "SigmaGrind"


def send_confirmation_email(reciver_address: str, message):
    s = SMTP("smtp.gmail.com")
    s.starttls()
    s.login(ADDRESS, PASSWORD)
    s.sendmail(ADDRESS, reciver_address, message)
    s.quit()


def error(message):
    return render_template("error.html", message=message)


def login_required(f):
    

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def enter(name: str, passwd: str):
    res = db_exec("SELECT id, password_hash FROM User WHERE username = ?", (name, ))

    if res:
        if not check_password_hash(res[0][1], passwd):
            return None
        return res[0][0]
    else:
        return None

def db_exec(query: str, arguments: tuple) -> None:
    conn = sqlite3.connect("brainstorm.db")
    curr = conn.cursor()
    try:
        res = curr.execute(query, arguments).fetchall()
    except sqlite3.IntegrityError:
        return "Usernate is already taken"
    conn.commit()
    conn.close()
    return res