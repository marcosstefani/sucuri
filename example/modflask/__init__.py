from flask import Flask, render_template_string
from sucuri import rendering

app = Flask(__name__)

@app.route("/")
def index():
    # template = rendering.template('template.suc')
    template = rendering.template('template_data.suc',{"a": 1, "b": "Hello!"})
    return render_template_string(template)