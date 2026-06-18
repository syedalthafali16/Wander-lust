from flask import Flask, render_template, request, redirect, flash, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = "my_super_secret_key_123"

import requests
import os

API_KEY = os.environ.get("WEATHER_API_KEY")


# =========================
# MYSQL DATABASE CONNECTION (RAILWAY)
# =========================
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT"))
    )


# =========================
# GLOBAL LOGIN RULE
# =========================
@app.before_request
def require_login():
    allowed_routes = ["home", "login", "signup", "static", "contact"]

    if request.endpoint not in allowed_routes and "user_id" not in session:
        return redirect(url_for("login"))


# =========================
# HOME
# =========================
@app.route("/")
def home():

    if "user_id" not in session:
        return render_template("pages/index.html")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Total trips
    cursor.execute(
        "SELECT COUNT(*) FROM trips WHERE user_id=%s",
        (session["user_id"],)
    )
    total_trips = cursor.fetchone()[0]

    # Total budget
    cursor.execute(
        "SELECT SUM(budget) FROM trips WHERE user_id=%s",
        (session["user_id"],)
    )
    total_budget = cursor.fetchone()[0] or 0

    # Upcoming trips
    cursor.execute(
        "SELECT COUNT(*) FROM trips WHERE user_id=%s AND date >= CURDATE()",
        (session["user_id"],)
    )
    upcoming_trips = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "pages/index.html",
        total_trips=total_trips,
        total_budget=total_budget,
        upcoming_trips=upcoming_trips
    )


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]   # ✅ ADD THIS LINE

            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password!", "error")

    return render_template("auth/login.html")


# =========================
# SIGNUP
# =========================
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Username already exists!", "error")
        else:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, password)
            )

            conn.commit()
            flash("Account created successfully! Please login.", "success")
            conn.close()
            return redirect(url_for("login"))

        conn.close()

    return render_template("auth/signup.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))

# =========================
# MAP 
# =========================
@app.route("/explore-map")
def explore_map():
    return render_template("explore_map.html")

# =========================
# WEATHER
# =========================
@app.route("/weather")
def weather():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"

    return requests.get(url).json()


# =========================
# DESTINATIONS
# =========================
@app.route("/destinations")
def destinations():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM destinations")
    destinations = cursor.fetchall()

    conn.close()

    return render_template("pages/destinations.html", destinations=destinations)


# =========================
# PLANNER
# =========================
@app.route("/planner", methods=["GET", "POST"])
def planner():

    if request.method == "POST":
        destination = request.form["destination"]
        date = request.form["date"]
        budget = request.form["budget"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO trips (destination, date, budget, user_id)
            VALUES (%s, %s, %s, %s)
        """, (destination, date, budget, session["user_id"]))

        conn.commit()
        conn.close()

        flash("Trip added successfully!", "success")
        return redirect(url_for("bookings"))

    return render_template("trips/planner.html")


# =========================
# BOOKINGS
# =========================
@app.route("/bookings")
def bookings():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM trips WHERE user_id=%s",
        (session["user_id"],)
    )

    trips = cursor.fetchall()

    conn.close()

    return render_template("trips/bookings.html", trips=trips)


# =========================
# EDIT
# =========================
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        destination = request.form["destination"]
        date = request.form["date"]
        budget = request.form["budget"]

        cursor.execute("""
            UPDATE trips
            SET destination=%s, date=%s, budget=%s
            WHERE id=%s AND user_id=%s
        """, (destination, date, budget, id, session["user_id"]))

        conn.commit()
        conn.close()

        flash("Trip updated successfully!", "success")
        return redirect(url_for("bookings"))

    cursor.execute(
        "SELECT * FROM trips WHERE id=%s AND user_id=%s",
        (id, session["user_id"])
    )

    trip = cursor.fetchone()
    conn.close()

    return render_template("trips/edit.html", trip=trip)


# =========================
# DELETE
# =========================
@app.route("/delete/<int:id>")
def delete(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM trips WHERE id=%s AND user_id=%s",
        (id, session["user_id"])
    )

    conn.commit()
    conn.close()

    flash("Trip deleted successfully!", "success")
    return redirect(url_for("bookings"))


# =========================
# CONTACT
# =========================
@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO contact_messages (name, email, message)
            VALUES (%s, %s, %s)
        """, (name, email, message))

        conn.commit()
        conn.close()

        flash("Message sent successfully! We will contact you soon.", "success")
        return redirect(url_for("contact"))

    return render_template("pages/contact.html")


# =========================
# Admin View Destination
# =========================
@app.route("/admin/destinations")
def admin_destinations():

    if session.get("role") != "admin":
        return "Access Denied"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM destinations")
    destinations = cursor.fetchall()

    conn.close()

    return render_template("admin/destinations.html", destinations=destinations)

# =========================
# Admin add destination
# =========================
@app.route("/admin/add_destination", methods=["GET","POST"])
def add_destination():

    if session.get("role") != "admin":
        return "Access denied"

    if request.method == "POST":

        city = request.form["city"]
        country = request.form["country"]
        description = request.form["description"]
        image = request.form["image"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
        "INSERT INTO destinations (city,country,description,image) VALUES (%s,%s,%s,%s)",
        (city,country,description,image)
        )

        conn.commit()
        conn.close()

        flash("Destination added successfully","success")

        return redirect(url_for("admin_destinations"))

    return render_template("admin/add_destination.html")

# =========================
# Admin edit destination
# =========================
@app.route("/admin/edit_destination/<int:id>", methods=["GET","POST"])
def edit_destination(id):

    if session.get("role") != "admin":
        return "Access denied"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        city = request.form["city"]
        country = request.form["country"]
        description = request.form["description"]
        image = request.form["image"]

        cursor.execute("""
        UPDATE destinations
        SET city=%s, country=%s, description=%s, image=%s
        WHERE id=%s
        """, (city, country, description, image, id))

        conn.commit()
        conn.close()

        flash("Destination updated successfully","success")

        return redirect(url_for("admin_destinations"))

    cursor.execute("SELECT * FROM destinations WHERE id=%s", (id,))
    destination = cursor.fetchone()

    conn.close()

    return render_template("admin/edit_destination.html", destination=destination)

# =========================
# Admin Delete Destination
# =========================
@app.route("/admin/delete_destination/<int:id>")
def delete_destination(id):

    if session.get("role") != "admin":
        return "Access denied"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM destinations WHERE id=%s", (id,))

    conn.commit()
    conn.close()

    flash("Destination deleted successfully","success")

    return redirect(url_for("admin_destinations"))

# =========================
# Admin Messages
# =========================
@app.route("/admin/messages")
def admin_messages():

    if session.get("role") != "admin":
        return "Access Denied"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM contact_messages ORDER BY created_at DESC")
    messages = cursor.fetchall()

    conn.close()

    return render_template("admin/messages.html", messages=messages)


if __name__ == "__main__":
    app.run(debug=True)