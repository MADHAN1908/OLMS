from flask import Flask, g
from db import get_db
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/cmc')
def cmc():
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT 1")
        cur.close()
        return "sqlite3 connection is established."
    except Exception as e:
        return f"Error connecting to Sqlite3: {e}"

if __name__ == "__main__":
    app.run(debug=True)
