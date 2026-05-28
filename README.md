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

## 🏃 Running Your App (Serve vs Desktop)

Sucuri has two execution modes for applications:

| Mode | Best for | Command |
|---|---|---|
| `serve` | Web/browser access, local dev, deploy on server/container | `sucuri serve app.py` |
| `desktop` | Native desktop window (WebView) without opening a browser tab | `sucuri desktop app.py` |

`desktop` runs the same Sucuri server internally and opens a native window pointed to it. So both modes share the same app/routes/templates behavior; the main difference is how users access the UI.

### Quick Commands

```bash
# Browser/server mode
sucuri serve app.py

# Native desktop mode (requires sucuri[desktop])
sucuri desktop app.py

# Common custom options
sucuri serve app.py --host 0.0.0.0 --port 3000
sucuri desktop app.py --title "My App" --width 1280 --height 800 --port 8080
```

### Desktop dependency

```bash
# Required only for desktop mode
pip install 'sucuri[desktop]'
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

### Code Blocks (`code`)

Use `code` for literal code snippets. For multi-line snippets, prefer `pre` + `code` and pipe lines (`|`).

```pug
pre
    code
        | class User:
        |     def save(self):
        |
        |         pass
```

**Output:**
```html
<pre>
    <code>
class User:
    def save(self):

        pass
    </code>
</pre>
```

Behavior notes:
- Line breaks and left indentation are preserved for multi-line `code` blocks.
- Blank lines inside `code` blocks are preserved.
- HTML-sensitive characters are escaped for safety (`<`, `>`, `&`, etc.).
- Whitespace-preservation behavior above is specific to `code` blocks.

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

### CSS Shortcuts
Sucuri supports PugJS-style CSS shorthand for `class` and `id` attributes. Use `.class-name` and `#id-name` directly on any tag — or even without a tag name to implicitly create a `<div>`.

```pug
div.container
    p.card-text Text

#app.wrapper
    h1 Hello

section#main.content.active
    span Done
```
**Output:**
```html
<div class="container">
    <p class="card-text">Text</p>
</div>
<div id="app" class="wrapper">
    <h1>Hello</h1>
</div>
<section id="main" class="content active">
    <span>Done</span>
</section>
```

---

### Dynamic Variables (Context)
Variables passed by Python's `context` can be effortlessly embedded directly into your text with `{}`. Sucuri also resolves **deeply nested context**. 

**Python Context:** `{"user": {"name": "Alice", "id": 123}}`

**Sucuri:**
```pug
div(class="profile")
    h1 Hello {user.name}!
    span User ID is {user.id}
```

### Filters
Apply built-in transformations to any variable using the pipe `|` operator. Filters can be chained.

| Filter  | Description                                      |
|---------|--------------------------------------------------|
| `upper` | Converts text to UPPERCASE                       |
| `lower` | Converts text to lowercase                       |
| `title` | Capitalizes The First Letter Of Each Word        |
| `safe`  | Renders raw HTML without escaping *(bypass XSS protection — use carefully!)* |

```pug
h1 {title | upper}
p {subtitle | lower}
span {author | title}
div {raw_html | safe}
```

Filters also work inside `<for>` loops via the `#` syntax:

```pug
<for item in products>
    li #item.name | title
<endfor>
```

Filters can be chained in sequence:

```pug
span {label | lower | title}
```

---

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

#### Passing Parameters to Macros
You can pass inline parameters to any macro directly at the call site using the `()` syntax. Parameters override context variables only for that macro invocation.

*`inc/card.suc`:*
```pug
div.card
    h2 {title}
    p {type}
```

*`index.suc`:*
```pug
include inc/card

+card(title="Warning" type="danger")
+card(title="Success" type="info")
```
**Output:**
```html
<div class="card">
    <h2>Warning</h2>
    <p>danger</p>
</div>
<div class="card">
    <h2>Success</h2>
    <p>info</p>
</div>
```

---

### Template Inheritance (`extends` / `block`)
Sucuri supports full template inheritance. A **parent layout** defines named `block` regions, and **child templates** extend it with `extends`, overriding only the blocks they need.

*`layout.suc`:*
```pug
html
    head
        title {title}
    body
        div(id="content")
            block content
        div(id="footer")
            block footer
```

*`page.suc`:*
```pug
extends layout

block content
    h1 Welcome to the Home Page
    p Here comes the content.

block footer
    p Page Footer
```

**Python:**
```python
html = template("page.suc", {"title": "My Site"})
```

**Output:**
```html
<html>
    <head>
        <title>My Site</title>
    </head>
    <body>
        <div id="content">
            <h1>Welcome to the Home Page</h1>
            <p>Here comes the content.</p>
        </div>
        <div id="footer">
            <p>Page Footer</p>
        </div>
    </body>
</html>
```

> Blocks not overridden by the child template render their default content from the parent.

---

### Injecting CSS Styles and JS Scripts
Need global JS or CSS appended without manually crafting raw headers/footers everywhere? Merely use `style` and `script` top-level declarations, supplying their raw path! They will be automatically wrapped in `<style>` and `<script>` HTML tags and beautifully appended to the file.

```pug
style static/css/global.css
script static/js/app.js

html
    body
        h1 Wow!
```

---

## 🔒 Security

### XSS Protection
By default, **all variables are automatically HTML-escaped** before rendering. This prevents cross-site scripting (XSS) attacks from untrusted context values.

**Python Context:** `{"msg": "<script>alert(1)</script>"}`

```pug
h1 {msg}
```
**Output:**
```html
<h1>&lt;script&gt;alert(1)&lt;/script&gt;</h1>
```

To render **trusted raw HTML** intentionally, use the `safe` filter:

```pug
div {html_content | safe}
```

> **Warning:** Only use `safe` on content you fully control. Never apply it to user-supplied input.

---

## ⚙️ Advanced: Environment & Custom Filters

For greater control — custom filters, isolated environments, or multi-app setups — use the `Environment` class directly instead of the top-level `template()` function.

### Registering Custom Filters

```python
from sucuri import Environment

env = Environment()

@env.register_filter('exclaim')
def exclaim(val):
    return f"{val}!!!"

env.register_filter('reverse', lambda x: str(x)[::-1])

html = env.template("templates/index.suc", {"title": "Hello"})
```

Custom filters are used in templates exactly like built-in ones:

```pug
h1 {title | exclaim}
span {title | exclaim | reverse}
```

Custom filters also work inside loops:

```pug
<for item in items>
    li #item | exclaim
<endfor>
```

### Multiple Environments
Each `Environment` instance has its own filter registry and base directory, making it safe to run isolated configurations side by side (e.g., multiple apps in the same process).

```python
env_a = Environment(base_dir="templates/app_a")
env_b = Environment(base_dir="templates/app_b")

env_a.register_filter('shout', lambda v: v.upper() + "!")
# env_b has no 'shout' filter — fully isolated
```

---

## 🌐 Built-in Live Server (Serve Mode)

Sucuri ships with a zero-dependency reactive HTTP server. It watches your app's state and pushes HTML updates to every connected browser in real time — no page reload needed.

### Starting the server

```bash
# Basic usage
sucuri serve app.py

# Custom host / port
sucuri serve app.py --host 0.0.0.0 --port 3000

# Disable CSRF token protection (see Security below)
sucuri serve app.py --public
```

---

### SucuriApp

```python
from sucuri.server import SucuriApp

app = SucuriApp(template_dir="templates")   # template_dir defaults to "."
```

To start the server from Python, call `app.run()` at the bottom of your app file:

```python
app.run()                             # http://127.0.0.1:8080  (defaults)
app.run(port=3000)                    # http://127.0.0.1:3000
app.run(host="0.0.0.0", port=3000)   # bind to all interfaces
```

> `host` and `port` can also be overridden at launch time via `--host` / `--port` CLI flags or the `SUCURI_HOST` / `SUCURI_PORT` environment variables — no need to change the source file.

---

### Reactive State & Live Reload

`app.state()` creates a reactive dictionary. When any top-level key changes, all browsers connected via SSE receive the updated HTML fragment instantly — without a full page reload.

```python
state = app.state({
    "products": [
        {"name": "Widget A", "price": "9.99"},
    ],
    "cart": {"count": 0, "total": "0.00"},
})
```

In your template, wrap reactive sections in `watch` blocks using the state key as the identifier:

```pug
html
  body
    watch products
      <for p in products>
      div.card
        span.name {p.name}
        span.price $ {p.price}
      <endfor>

    watch cart
      p Items: {cart.count} — Total: $ {cart.total}
```

Each `watch` block renders as a `<div data-suc-watch="key">` wrapper. When the server detects a change to that key, only that wrapper is replaced in the DOM — no full page reload.

> **Using `watch` outside the live server?**  
> When rendering with `template()`, `Environment.template()`, or any framework integration (Flask, FastAPI, Django…), `watch` blocks are completely transparent. The content inside renders as normal HTML — no wrapper div, no markers. This means you can freely share the same `.suc` templates between the live server and a plain render without any changes.

**Triggering a re-render from a route handler:**

There are two mutation patterns, and they behave differently:

```python
# ✅ Top-level reassignment — triggers notify automatically
state["products"] = updated_list

# ⚠️  Nested mutation (append, pop, dict update…) — must notify manually
state.data["products"].append({"name": "New", "price": "1.00"})
state.notify("products")   # push the update to connected browsers
```

The rule is simple: **assigning directly to `state["key"]` is automatic; mutating the value inside `state.data["key"]` is manual.**

---

### Automatic Template Reload

The live server also watches every `.suc`, `.css`, `.js`, and `.html` file inside `template_dir`. Whenever you save any of those files during development, **all connected browsers automatically reload the full page** — no manual refresh needed.

This is completely separate from the reactive state updates:

| Trigger | Result |
|---|---|
| `state["key"]` assignment or `state.notify("key")` | Only the matching `watch` block is swapped in the DOM — no reload |
| Any template / CSS / JS file saved on disk | Full page reload in all connected browsers |

No configuration is required — the watcher starts automatically with `app.run()`.

---

### Routes

#### GET

```python
@app.get("/")
def index():
    return app.render("shop.suc", state.data)   # template → HTML string

@app.get("/ping")
def ping():
    return {"status": "ok"}   # dict → JSON response
```

#### POST / PUT / DELETE

Mutation handlers receive a `request` object as their first positional argument:

```python
@app.post("/api/price")
def update_price(request):
    new_price = request.json.get("price")
    state.data["products"][0]["price"] = new_price
    state.notify("products")
    return {"ok": True}

@app.put("/api/item")
def replace_item(request):
    ...

@app.delete("/api/item")
def remove_item(request):
    ...
```

#### Dynamic routes

Use `<param>` placeholders in the path. GET handlers receive params as keyword arguments; mutation handlers receive them after `request`:

```python
@app.get("/api/product/<index>")
def get_product(index):
    return state.data["products"][int(index)]

@app.post("/api/product/<index>/price")
def update_price_by_index(request, index):
    state.data["products"][int(index)]["price"] = request.json["price"]
    state.notify("products")
    return {"ok": True}

@app.delete("/api/product/<index>")
def delete_product(request, index):
    state.data["products"].pop(int(index))
    state.notify("products")
    return {"ok": True}
```

---

### Response Helpers

By default, routes return `str` (HTML 200) or `dict` (JSON 200). For any other status code, redirect, or raw bytes, import the helpers from `sucuri.server`:

```python
from sucuri.server import SucuriApp, Response, redirect
```

#### `Response(body, status=200, content_type=None)`

Wraps any return value with a custom HTTP status code or content type.

```python
@app.post("/api/login")
def login(request):
    if not valid_credentials(request.json):
        return Response({"error": "unauthorized"}, status=401)
    return {"ok": True}

@app.get("/api/item/<id>")
def get_item(id):
    item = find(id)
    if item is None:
        return Response("<h1>Not found</h1>", status=404)
    return item

@app.get("/report")
def report():
    pdf_bytes = generate_pdf()
    return Response(pdf_bytes, status=200, content_type="application/pdf")
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `body` | `str`, `dict`, or `bytes` | — | Response body |
| `status` | `int` | `200` | HTTP status code |
| `content_type` | `str \| None` | `None` | Forces a specific Content-Type; auto-detected when `None` |

#### `redirect(url, status=302)`

Returns an HTTP redirect. Works from any GET or mutation handler.

```python
@app.get("/old-path")
def old_path():
    return redirect("/new-path")          # 302 Found

@app.get("/permanent")
def permanent():
    return redirect("/new-path", status=301)  # 301 Moved Permanently

@app.post("/api/login")
def login(request):
    # authenticate…
    return redirect("/dashboard")
```

---

### Request Object

| Attribute | Type | Description |
|-----------|------|-------------|
| `request.body` | `bytes` | Raw request body |
| `request.json` | `dict` | Parsed JSON body (`{}` on failure) |
| `request.form` | `dict` | Parsed form data (see below) |

#### `request.form`

Populated for `application/x-www-form-urlencoded` and `multipart/form-data` requests.

| Scenario | Value type |
|----------|-----------|
| Single-value field | `str` |
| Repeated field name | `list[str]` |
| File upload field (`filename=`) | `bytes` |

```python
@app.post("/api/register")
def register(request):
    name  = request.form["name"]        # str
    tags  = request.form.get("tags")    # list[str] if sent multiple times
    photo = request.form.get("photo")   # bytes if it's a file field
    ...
```

To submit a form from JavaScript using the correct Content-Type:

```javascript
fetch("/api/register", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams(new FormData(formElement)).toString()
});
```

---

### Custom Error Handlers

Register handlers for any HTTP error code with `@app.error(code)`. The handler for `500` receives the exception as its first argument; all other codes are called with no arguments.

```python
@app.error(404)
def not_found():
    return """
    <html><body>
      <h1>404 — Not found</h1>
      <a href="/">Go back</a>
    </body></html>
    """

@app.error(500)
def server_error(exc):
    return {"error": str(exc), "type": type(exc).__name__}
```

Handlers follow the same return convention as routes: a `str` is sent as `text/html`, a `dict` as `application/json`, both with the appropriate error status code.

---

### Static Files

Any file placed inside `template_dir/static/` is served automatically at `/static/<path>`.

```
templates/
  static/
    css/
      style.css    →  GET /static/css/style.css
    js/
      app.js       →  GET /static/js/app.js
    logo.png       →  GET /static/logo.png
```

Path traversal outside `static/` is blocked with a `403`.

---

### CSRF Protection

By default, every non-GET request is protected by a CSRF token stored in an `HttpOnly; SameSite=Strict` cookie named `__sucuri_csrf`.

- **`HttpOnly`** — JavaScript on the page can never read the token, even under an XSS attack.
- **`SameSite=Strict`** — the browser never sends the cookie on cross-origin requests, blocking CSRF from other domains.
- The token is set automatically when the server serves any HTML page. The browser sends the cookie on same-origin `fetch` and `<form>` requests without any JavaScript involvement.

**No token management is needed in your JavaScript.** Just make `fetch` calls normally:

```javascript
// No X-Sucuri-Token header needed — the browser handles the cookie automatically
fetch("/api/update", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ price: "19.99" })
});
```

To disable protection (e.g. for fully public APIs):

```bash
sucuri serve app.py --public
# or
SUCURI_PUBLIC=1 sucuri serve app.py
```

> **Warning:** Never use `--public` in production if your endpoints mutate state.

---

### Default Favicon

When your app does not provide a favicon, the server automatically serves the Sucuri logo at `/favicon.ico`. To override it, place your own file in `template_dir/static/` with any of these names (checked in order):

- `static/favicon.ico`
- `static/favicon.svg`
- `static/favicon.png`

---

## 🖥️ Desktop Mode

Sucuri can open your application as a **native desktop window** instead of serving it in a browser tab. It uses the operating system's built-in WebView (WKWebView on macOS, WebView2 on Windows, WebKitGTK on Linux) via [pywebview](https://pywebview.flowrl.com/) - no Electron or Chromium bundle needed.

### Usage

```bash
sucuri desktop app.py
```

The Sucuri server starts in a background thread and a native window opens pointing to it. When the window is closed, the server stops automatically.

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--title` | `Sucuri App` | Window title bar text |
| `--port`, `-p` | `8080` | Port the server listens on |
| `--host` | `127.0.0.1` | Host to bind to |
| `--width` | `1024` | Window width in pixels |
| `--height` | `768` | Window height in pixels |

### Example

```bash
sucuri desktop main.py --title "Inventory" --width 1280 --height 800
```

### Packaging as a standalone executable

To distribute your app without requiring Python to be installed, use [PyInstaller](https://pyinstaller.org):

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name my-app \
    --add-data "templates:templates" \
    --icon sucuri/assets/favicon.png \
    main.py
```

The output binary in `dist/` runs your Sucuri app as a self-contained desktop application.

> **Note:** `--icon` sets the dock/taskbar icon on Windows and Linux. On macOS, the icon is embedded in the `.app` bundle via `--icon` as well, but requires an `.icns` file for best results.

---

## �🐳 Docker

A pre-built Docker image is available on Docker Hub, so you can containerise any Sucuri app without installing Python locally.

> Replace `latest` with any published version tag if you need a pinned release — e.g. `marcosstefani/sucuri:1.2.3`.

### Using the image as a base

Create a `Dockerfile` in your project root:

```dockerfile
FROM marcosstefani/sucuri:latest

# Copy your app files into the container
COPY . .

# Default port is 8080 — expose it
EXPOSE 8080
```

Your project structure should look like this:

```
my-app/
  Dockerfile
  app.py            ← SucuriApp entry point
  templates/
    index.suc
    static/
      style.css
```

Then build and run:

```bash
docker build -t my-sucuri-app .
docker run -p 8080:8080 my-sucuri-app
```

Your app is now available at `http://localhost:8080`.

### Overriding the entry point

The default `CMD` runs `sucuri serve app.py --host 0.0.0.0`. If your entry file has a different name, override it in your `Dockerfile`:

```dockerfile
FROM marcosstefani/sucuri:latest

COPY . .

CMD ["sucuri", "serve", "main.py", "--host", "0.0.0.0"]
```

### Using Docker Compose

```yaml
services:
  web:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./templates:/app/templates   # live-reload template edits without rebuilding
```
