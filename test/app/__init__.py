from flask import Flask, render_template

app = Flask(__name__)
app.config.from_object('config')

@app.route("/")
def index():
    return render_template("home.html")

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

from app.sucuri.rendering import rendering

rendering()