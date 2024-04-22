from flask import Flask


app= Flask(__name__)

@app.run('/')
def home():
    return "welcome"


if __name__ =="__main__":
    app.run(debug=True)