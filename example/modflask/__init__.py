from flask import Flask, render_template_string
from sucuri import rendering

app = Flask(__name__)

@app.route("/")
def index():
    template = rendering.template('template_include.suc',{"text": "Hello! I'm here!"})
    return render_template_string(template)