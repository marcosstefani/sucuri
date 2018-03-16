from flask import Flask, render_template_string, render_template
from app.sucuri.rendering import rendering

app = Flask(__name__)
app.config.from_object('config')

@app.route("/")
def index():
    html= rendering()
    return render_template_string(html)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

rendering()