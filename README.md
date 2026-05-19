<a href="#"><img src="https://user-images.githubusercontent.com/16294901/37826760-892cd0de-2e73-11e8-8ea1-2afc390c2ac0.png" height="300" align="right"></a>

# Sucuri

Simple and efficient template engine for Python projects, inspired by [PugJS](https://pugjs.org).

Sucuri is designed to bring an elegant, indentation-based syntax to Python. By stripping away repetitive HTML tags and taking advantage of natural code structure, Sucuri gives developers a pristine, highly readable HTML rendering experience. 

Powered natively by the [Lark](https://github.com/lark-parser/lark) parser, Sucuri supports deep variable nesting, loops, conditionals, seamless macro injections, and is **completely framework-independent**. It plays just as well with modern frameworks like **FastAPI**, **Django**, and **Flask** as it does in native Python scripts.

---

## 📦 Installation

Install and update using [pip](https://pip.pypa.io/en/stable/quickstart/):

```bash
pip install sucuri
```

---

## 🚀 Quick Start & Integration

Sucuri returns raw HTML strings that can be seamlessly injected into any existing web framework format. All you need is the `template` function from `sucuri.rendering`.

### Vanilla Python
```python
from sucuri.rendering import template

context = {"name": "World"}
html_output = template("my_template.suc", context)
print(html_output)
```

### ⚡ FastAPI Integration
Returns a raw `HTMLResponse` instantly!
```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sucuri.rendering import template

app = FastAPI()

@app.get("/")
def index():
    context = {"name": "FastAPI User"}
    html = template('templates/index.suc', context)
    return HTMLResponse(content=html, status_code=200)
```

### 🌶️ Flask Integration
Use Flask's `render_template_string` to wrap Sucuri's output.
```python
from flask import Flask, render_template_string
from sucuri.rendering import template

app = Flask(__name__)

@app.route("/")
def index():
    context = {"name": "Flask User"}
    html = template('templates/index.suc', context)
    return render_template_string(html)
```

### 🎸 Django Integration
Return the compiled string through `HttpResponse`.
```python
from django.http import HttpResponse
from sucuri.rendering import template

def index(request):
    context = {"name": "Django User"}
    html = template('templates/index.suc', context)
    return HttpResponse(html)
```

---

## 💻 Command Line Interface (CLI)

Sucuri provides a CLI to directly process `.suc` templates from your terminal—perfect for shell scripts and static site generation!

```bash
# Basic compilation (outputs to stdout)
sucuri build index.suc

# Compilation with output file
sucuri build index.suc -o index.html

# Compilation passing JSON context variables directly inline
sucuri build index.suc --context '{"title": "My Page"}' -o index.html

# Compilation using JSON data loaded from another file
sucuri build index.suc --context context.json -o index.html
```

---

## 📖 Syntax & Features

### Basics & Indentation 
A standard `HTML` file doesn't need brackets `< >`. Instead, Sucuri relies on **tabs or spaces** (kept strictly uniform) to determine tag hierarchies.

```pug
html
    body
        h1 Title
        a(href='#') This is my link
```
**Output:**
```html
<html>
    <body>
        <h1>Title</h1>
        <a href="#">This is my link</a>
    </body>
</html>
```

### Text

Texts can be described in two ways. Inline together with the tag declaration, or spanning multiple lines starting with the `|` pipe character.

```pug
h3 Hello!
    | Text
    | with
    | more than
    | one line
```
**Output:**
```html
<h3>Hello!
    Text
    with
    more than
    one line
</h3>
```

### Attributes
HTML attributes in Sucuri must be separated by space and enclosed strictly within parentheses `()`. Unlike standard Pug, they are on a single line and separated by spaces (not commas).

```pug
a(href='google.com') Google
a(class='button' href='google.com') Google
div(class='div-class')
input(type="checkbox" checked)
```
**Output:**
```html
<a href="google.com">Google</a>
<a class="button" href="google.com">Google</a>
<div class="div-class"></div>
<input type="checkbox" checked>
```

### Dynamic Variables (Context)
Variables passed by Python's `context` can be effortlessly embedded directly into your text with `{}`. Sucuri also resolves **deeply nested context**. 

**Python Context:** `{"user": {"name": "Alice", "id": 123}}`

**Sucuri:**
```pug
div(class="profile")
    h1 Hello {user.name}!
    span User ID is {user.id}
```

### Control Flow
You can handle logic natively in `.suc` files.

#### If Conditions
Wrap standard comparisons using `<if condition>` and `<endif>`.
```pug
<if user.status != "banned">
  h1 User is active!
<endif>
```

#### For Loops
Iterate elegantly using `<for item in list>`. Access your iterated items dynamically using the hash `#` symbol (which also supports nested resolution like `#item.id`!).

**Python Context:** `{"invoices": [{"id": 1}, {"id": 2}]}`
```pug
ul
    <for inv in invoices>
        li Invoice Number: #inv.id
    <endfor>
```

---

## 📦 Preloaded Templates (Built-in Magic)

Instead of manually crafting standard HTML configurations like `ul/li` and `table` setups, Sucuri comes packed with pre-compiled macros for lists and tables to drastically speed up repetitive boilerplate code! 

### 1. Lists & Checkboxes
Pass ANY variable containing an Array, and use the `list()` built-in to render an entire list matrix automatically.

**Python Context:** `{"my_array": ["Apple", "Orange"], "opts": ["Apple"]}`

**Unordered List:**
```pug
list(my_array class="ul-squares")
```
**Result:**
```html
<ul class="ul-squares">
    <li> Apple </li>
    <li> Orange </li>
</ul>
```

**Checkboxes:** (Just provide the secondary array containing the checked values!)
```pug
list(my_array opts class="survey")
```
**Result:**
```html
<input type="checkbox" id="ck-Apple" checked="checked">Apple
<input type="checkbox" id="ck-Orange">Orange
```

### 2. Tables
Need a comprehensive HTML table constructed in one go? The `table()` syntax takes header arrays, rows matrices, and footer arrays automatically!

**Python Context:**
```python
context = {
    "heads": ["Name", "Age"],
    "rows": [["Alice", 21], ["Bob", 45]],
    "footers": ["End", "End"]
}
```

**Sucuri:**
```pug
table(heads rows footers class="table" id="tb-authors")
```
**Result:**
```html
<table class="table" id="tb-authors">
    <thead>
        <tr>
            <th>Name</th>
            <th>Age</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Alice</td>
            <td>21</td>
        </tr>
        <tr>
            <td>Bob</td>
            <td>45</td>
        </tr>
    </tbody>
    <tfoot>
        <tr>
            <td>End</td>
            <td>End</td>
        </tr>
    </tfoot>
</table>
```
*(Positional order: Headers array, Data Matrix array, Footer array.)*

---

## 🧩 Modularity: Includes, Styles & Scripts
Sucuri acts efficiently as an asset distributor through macro tagging and external inclusions. The engine caches everything natively during execution. 

### Including Other `.suc` files
Declare your macro inclusions at the top using `include`, and instantiate them using the `+` sign.

*`modules/button.suc`:*
```pug
button(class='btn-primary') {text}
```

*`index.suc`:*
```pug
include modules/button

html
    body
        h1 Welcome
        +button
```

### Injecting CSS Styles and JS Scripts
Need global JS or CSS appended without manually crafting raw headers/footers everywhere? Merely use `style` and `script` top-level declarations, supplying their raw path! They will be automatically wrapped in `<style>` and `<script>` HTML tags and beautifully appended to the file.

```pug
style static/css/global.css
script static/js/app.js

html
    body
        h1 Wow!
```
