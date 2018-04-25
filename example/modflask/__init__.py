from flask import Flask, render_template_string
from sucuri import rendering

app = Flask(__name__)

@app.route("/")
def index():
    template = rendering.template('template.suc',{"text": "Hello! I'm here!", "var":[1, 2, 3, 4]})
    return render_template_string(template)