from flask import Flask,g,render_template,send_file,request, redirect, url_for,session
import subprocess
import base64,os
from io import BytesIO
from datetime import datetime, timedelta
import matplotlib

import matplotlib.pyplot as plt
from db import *
app=Flask(__name__)

app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'static/UPLOAD_FOLDER/'
matplotlib.use('agg')

@app.route('/cmc')
def cmc():
    try:
        db= get_db()
        cur = db.cursor()
        cur.execute("SELECT 1")
        # cur.close()
        return "sqlite3 connection is established."
    except Exception as e:
        return f"Error connecting to Sqlite3: {e}"

if __name__=="__main__":
    app.run (debug=True)    
