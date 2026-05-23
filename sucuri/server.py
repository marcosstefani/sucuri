import json
import mimetypes
import os
import queue
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs

from sucuri.rendering import Environment, _AST_CACHE
from sucuri.parser import parse_sucuri
from sucuri.state import State


def _compile_route(path):
    """Convert '/api/<resource>/<id>' to (compiled_regex, [param_names])."""
    param_names = []
    parts = re.split(r'(<[^>]+>)', path)
    pattern = ''
    for part in parts:
        if part.startswith('<') and part.endswith('>'):
            param_names.append(part[1:-1])
            pattern += '([^/]+)'
        else:
            pattern += re.escape(part)
    return re.compile(f'^{pattern}$'), param_names


# ---------------------------------------------------------------------------
# JS snippet injected into every rendered page.
# Opens an SSE connection, replaces changed watch blocks, and keeps the
# rotating CSRF token in sync with the server.
# ---------------------------------------------------------------------------
def _make_sse_script(token=None):
    """Return the SSE <script> tag to inject. Pass token=None in public mode."""
    token_js = f'\n  window.__sucuri_token = "{token}";' if token is not None else ''
    return f"""\
<script>
(function () {{{token_js}
  var es = new EventSource('/__sucuri__/events');
  es.onmessage = function (e) {{
    var d = JSON.parse(e.data);
    var el = document.querySelector('[data-suc-watch="' + d.id + '"]');
    if (el) {{ el.outerHTML = d.html; }}
  }};
  es.addEventListener('token', function (e) {{
    window.__sucuri_token = e.data;
  }});
}}());
</script>"""


class _ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """HTTPServer that handles each request in its own thread."""
    daemon_threads = True

    def handle_error(self, request, client_address):
        """Suppress noisy-but-harmless connection errors (browser closed tab, etc)."""
        import sys
        if sys.exc_info()[0] in (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            return
        super().handle_error(request, client_address)


def _extract_watch_block(html, key):
    """Return the rendered HTML for a single watch block, including its wrapper div."""
    start_marker = f'<!--[suc:{key}:start]-->'
    end_marker   = f'<!--[suc:{key}:end]-->'
    start_idx = html.find(start_marker)
    end_idx   = html.find(end_marker)
    if start_idx == -1 or end_idx == -1:
        return None
    # Return the content between the markers (the <div data-suc-watch="...">)
    return html[start_idx + len(start_marker):end_idx].strip()


def _invalidate_cache_if_stale(path):
    """Remove the AST cache entry if the file has been modified since last parse."""
    if path not in _AST_CACHE:
        return
    cached_mtime = getattr(_invalidate_cache_if_stale, '_mtimes', {}).get(path)
    current_mtime = os.path.getmtime(path)
    if cached_mtime != current_mtime:
        del _AST_CACHE[path]

if not hasattr(_invalidate_cache_if_stale, '_mtimes'):
    _invalidate_cache_if_stale._mtimes = {}


class SucuriApp:
    """
    Built-in reactive web server for Sucuri templates.

    Usage::

        from sucuri.server import SucuriApp

        app = SucuriApp(template_dir=".")

        state = app.state({
            "title": "My Shop",
            "products": [{"name": "Widget", "price": 9.99}],
        })

        @app.get("/")
        def index():
            return app.render("shop.suc", state.data)

        @app.post("/api/price")
        def update_price(request):
            state["products"][0]["price"] = request.json["price"]
            state.notify("products")   # nested mutation: notify manually
            return {"ok": True}

        app.run(port=8080)

    Top-level key assignment notifies automatically::

        state["products"] = new_list   # <- broadcasts to all browsers instantly
    """

    def __init__(self, template_dir="."):
        self.template_dir = os.path.abspath(template_dir)
        self._env = Environment(base_dir=self.template_dir)
        self._routes = []           # list of (method, regex, param_names, callable)
        self._sse_clients = []      # list of queue.Queue
        self._sse_lock = threading.Lock()
        self._current_template = None   # absolute path of the last rendered template
        self._current_context  = None   # reference to the context dict (state.data)
        # Token protection — disabled when SUCURI_PUBLIC=1
        self._protected  = os.environ.get("SUCURI_PUBLIC") != "1"
        self._token      = secrets.token_hex(32)
        self._token_lock = threading.Lock()
        self._error_handlers = {}   # status_code -> callable

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def state(self, initial_data):
        """Create an observable State tied to this app."""
        s = State(initial_data)
        s._set_broadcast(self._on_state_change)
        return s

    def render(self, template_name, context):
        """
        Render a .suc template with the given context dict and return HTML.
        Call this from a route handler::

            return app.render("index.suc", state.data)
        """
        path = os.path.join(self.template_dir, template_name)
        _invalidate_cache_if_stale(path)
        _invalidate_cache_if_stale._mtimes[path] = os.path.getmtime(path)

        self._current_template = path
        self._current_context  = context

        html = self._env.template(path, context)

        # Inject SSE listener + current token before </body>
        sse = _make_sse_script(self._token if self._protected else None)
        if "</body>" in html:
            html = html.replace("</body>", sse + "\n</body>", 1)
        else:
            html += "\n" + sse

        return html

    def get(self, path):
        """Register a GET route handler. Supports '<param>' placeholders."""
        def decorator(fn):
            regex, params = _compile_route(path)
            self._routes.append(("GET", regex, params, fn))
            return fn
        return decorator

    def post(self, path):
        """Register a POST route handler. Supports '<param>' placeholders."""
        def decorator(fn):
            regex, params = _compile_route(path)
            self._routes.append(("POST", regex, params, fn))
            return fn
        return decorator

    def put(self, path):
        """Register a PUT route handler. Supports '<param>' placeholders."""
        def decorator(fn):
            regex, params = _compile_route(path)
            self._routes.append(("PUT", regex, params, fn))
            return fn
        return decorator

    def delete(self, path):
        """Register a DELETE route handler. Supports '<param>' placeholders."""
        def decorator(fn):
            regex, params = _compile_route(path)
            self._routes.append(("DELETE", regex, params, fn))
            return fn
        return decorator

    def error(self, code):
        """Register a custom error handler for an HTTP status code.

        The 500 handler receives the exception as its first argument.
        All other handlers receive no arguments.

        Example::

            @app.error(404)
            def not_found():
                return "<h1>404 — Page not found</h1>"

            @app.error(500)
            def server_error(exc):
                return {"error": str(exc)}
        """
        def decorator(fn):
            self._error_handlers[code] = fn
            return fn
        return decorator

    def _match_route(self, method, path):
        """Return (handler, params_dict) for the first matching route, or (None, {})."""
        for (m, regex, param_names, fn) in self._routes:
            if m != method:
                continue
            match = regex.match(path)
            if match:
                return fn, dict(zip(param_names, match.groups()))
        return None, {}

    def run(self, port=None, host=None):
        """Start the live server. Blocks until Ctrl-C."""
        port = port or int(os.environ.get("SUCURI_PORT", 8080))
        host = host or os.environ.get("SUCURI_HOST", "127.0.0.1")

        app = self  # closure reference for the inner Handler class

        class _Handler(BaseHTTPRequestHandler):

            def log_message(self, fmt, *args):  # noqa: D401
                print(f"  [{self.address_string()}] {fmt % args}")

            # --- GET ---------------------------------------------------
            def do_GET(self):
                path = urlparse(self.path).path
                if path == "/__sucuri__/events":
                    self._handle_sse()
                    return
                if path == "/favicon.ico":
                    self.send_response(204)
                    self.end_headers()
                    return
                if path.startswith("/static/"):
                    self._serve_static(path)
                    return
                handler, params = app._match_route("GET", path)
                if handler is None:
                    self._respond_error(404)
                    return
                try:
                    self._respond(handler(**params))
                except Exception as exc:
                    self._respond_error(500, exc)

            # --- POST / PUT / DELETE -----------------------------------
            def _handle_mutation(self, method):
                path = urlparse(self.path).path
                handler, params = app._match_route(method, path)
                if handler is None:
                    self._respond_error(404)
                    return
                if app._protected:
                    provided = self.headers.get("X-Sucuri-Token", "")
                    with app._token_lock:
                        valid = secrets.compare_digest(provided, app._token)
                    if not valid:
                        body = json.dumps({"error": "invalid or expired token"}).encode()
                        self.send_response(403)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(body)))
                        self.end_headers()
                        self.wfile.write(body)
                        return
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length else b""
                content_type = self.headers.get("Content-Type", "")
                try:
                    result = handler(_Request(raw, content_type), **params)
                except Exception as exc:
                    self._respond_error(500, exc)
                    return
                if app._protected:
                    with app._token_lock:
                        app._token = secrets.token_hex(32)
                        new_token = app._token
                    app._broadcast_token(new_token)
                self._respond(result)

            def do_POST(self):   self._handle_mutation("POST")
            def do_PUT(self):    self._handle_mutation("PUT")
            def do_DELETE(self): self._handle_mutation("DELETE")

            # --- helpers -----------------------------------------------
            def _respond(self, result, status=200):
                if isinstance(result, str):
                    body = result.encode("utf-8")
                    self.send_response(status)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif isinstance(result, dict):
                    body = json.dumps(result).encode("utf-8")
                    self.send_response(status)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

            def _respond_error(self, code, exc=None):
                """Call custom error handler if registered, else fall back to default."""
                handler = app._error_handlers.get(code)
                if handler is not None:
                    try:
                        result = handler(exc) if exc is not None else handler()
                        self._respond(result, status=code)
                        return
                    except Exception:
                        pass
                self.send_error(code)

            def _serve_static(self, url_path):
                rel = url_path[len("/static/"):]
                static_root = os.path.realpath(os.path.join(app.template_dir, "static"))
                abs_path = os.path.realpath(os.path.join(static_root, rel))
                # Prevent path traversal outside static_root
                if not abs_path.startswith(static_root + os.sep):
                    self.send_error(403, "Forbidden")
                    return
                if not os.path.isfile(abs_path):
                    self.send_error(404, "Not found")
                    return
                mime, _ = mimetypes.guess_type(abs_path)
                mime = mime or "application/octet-stream"
                with open(abs_path, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _handle_sse(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                q = queue.Queue(maxsize=64)
                with app._sse_lock:
                    app._sse_clients.append(q)

                try:
                    while True:
                        try:
                            msg = q.get(timeout=25)
                            self.wfile.write(msg)
                            self.wfile.flush()
                        except queue.Empty:
                            # Keep-alive ping so the connection stays open
                            self.wfile.write(b": ping\n\n")
                            self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    pass
                finally:
                    with app._sse_lock:
                        if q in app._sse_clients:
                            app._sse_clients.remove(q)

        server = _ThreadingHTTPServer((host, port), _Handler)
        print(f"Sucuri live server → http://{host}:{port}  (Ctrl-C to stop)")
        if self._protected:
            print( "  Protected  → token rotates after each request. Use --public to disable.")
        else:
            print( "  Public mode → non-GET endpoints have no token protection.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            server.shutdown()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_state_change(self, key):
        if self._current_template is None or self._current_context is None:
            return
        html_fragment = self._render_partial(key)
        if html_fragment is not None:
            self._broadcast(key, html_fragment)

    def _render_partial(self, watch_key):
        """Re-render the full template and extract only the changed watch block."""
        path = self._current_template
        _invalidate_cache_if_stale(path)
        # Full re-render with current (already updated) context
        full_html = self._env.template(path, self._current_context)
        return _extract_watch_block(full_html, watch_key)

    def _broadcast(self, key, html):
        data = json.dumps({"id": key, "html": html})
        msg  = f"data: {data}\n\n".encode("utf-8")
        with self._sse_lock:
            dead = []
            for q in self._sse_clients:
                try:
                    q.put_nowait(msg)
                except queue.Full:
                    dead.append(q)
            for q in dead:
                self._sse_clients.remove(q)

    def _broadcast_token(self, token):
        """Push the new rotating token to all connected SSE clients."""
        msg = f"event: token\ndata: {token}\n\n".encode("utf-8")
        with self._sse_lock:
            dead = []
            for q in self._sse_clients:
                try:
                    q.put_nowait(msg)
                except queue.Full:
                    dead.append(q)
            for q in dead:
                self._sse_clients.remove(q)


def _parse_urlencoded(body_bytes):
    """Parse application/x-www-form-urlencoded body → dict."""
    text = body_bytes.decode("utf-8", errors="replace")
    parsed = parse_qs(text, keep_blank_values=True)
    return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}


def _parse_multipart(body_bytes, content_type):
    """Parse multipart/form-data body → dict of {name: str | bytes}."""
    m = re.search(r'boundary=(?:"([^"]+)"|([^\s;]+))', content_type, re.IGNORECASE)
    if not m:
        return {}
    boundary = (m.group(1) or m.group(2)).encode("latin-1")
    result = {}
    for part in body_bytes.split(b"--" + boundary)[1:]:
        if part.lstrip(b"\r\n").startswith(b"--"):
            break
        sep = b"\r\n\r\n" if b"\r\n\r\n" in part else b"\n\n"
        if sep not in part:
            continue
        headers_raw, body = part.split(sep, 1)
        body = body.rstrip(b"\r\n")
        cd = re.search(rb';\s*name="([^"]+)"', headers_raw, re.IGNORECASE)
        if not cd:
            continue
        name = cd.group(1).decode("utf-8", errors="replace")
        fn = re.search(rb'filename="([^"]*)"', headers_raw, re.IGNORECASE)
        result[name] = body if fn else body.decode("utf-8", errors="replace")
    return result


class _Request:
    """Minimal request object passed to mutation handlers."""
    __slots__ = ("body", "json", "form")

    def __init__(self, body_bytes, content_type=""):
        self.body = body_bytes
        ct = content_type.lower()
        try:
            self.json = json.loads(body_bytes)
        except Exception:
            self.json = {}
        if "application/x-www-form-urlencoded" in ct:
            self.form = _parse_urlencoded(body_bytes)
        elif "multipart/form-data" in ct:
            self.form = _parse_multipart(body_bytes, content_type)
        else:
            self.form = {}
