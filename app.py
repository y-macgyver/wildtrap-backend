from flask import Flask, Response, request, jsonify, render_template
import psycopg2
import os
import time
from datetime import datetime

app = Flask(__name__)

latest_frame = None
latest_count = 0
last_save_time = time.time()

# PostgreSQL connection
conn = psycopg2.connect(os.environ["DATABASE_URL"])
cursor = conn.cursor()

# ----------------------------------
# RECEIVE FRAME FROM EDGE
# ----------------------------------
@app.route("/upload", methods=["POST"])
def upload():
    global latest_frame, latest_count, last_save_time

    latest_frame = request.files["frame"].read()
    latest_count = int(request.form["count"])

    # Save every 5 minutes
    if time.time() - last_save_time > 300:
        now = datetime.now()
        cursor.execute(
            """
            INSERT INTO records (date, day, time, location, count)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                now.date(),
                now.strftime("%A"),
                now.strftime("%H:%M:%S"),
                "Main Cage",
                latest_count
            )
        )
        conn.commit()
        last_save_time = time.time()

    return "OK"

# ----------------------------------
# VIDEO STREAM
# ----------------------------------
@app.route("/video_feed")
def video_feed():
    def gen():
        while True:
            if latest_frame:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + latest_frame
                    + b"\r\n"
                )
            time.sleep(0.05)

    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")

# ----------------------------------
# WEB PAGE
# ----------------------------------
@app.route("/")
def surveillance():
    return render_template("Surveillance.html")

# ----------------------------------
# API RECORDS
# ----------------------------------
@app.route("/api/records")
def records():
    cursor.execute("SELECT * FROM records ORDER BY id DESC")
    rows = cursor.fetchall()

    return jsonify([
        {
            "id": r[0],
            "date": str(r[1]),
            "day": r[2],
            "time": r[3],
            "location": r[4],
            "count": r[5]
        } for r in rows
    ])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
