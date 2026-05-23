import json
import os
import queue
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlparse

from sucuri.rendering import Environment, _AST_CACHE
from sucuri.parser import parse_sucuri
from sucuri.state import State


# ---------------------------------------------------------------------------
# Tiny JS snippet injected automatically into every rendered page.
# Opens an SSE connection and replaces only the changed watch block in the DOM.
# ---------------------------------------------------------------------------
_SSE_SCRIPT = """\
<script>
(function () {
  var es = new EventSource('/__sucuri__/events');
  es.onmessage = function (e) {
    var d = JSON.parse(e.data);
    var el = document.querySelector('[data-suc-watch="' + d.id + '"]');
    if (el) { el.outerHTML = d.html; }
  };
}());
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
        self._routes = {}           # (method, path) -> callable
        self._sse_clients = []      # list of queue.Queue
        self._sse_lock = threading.Lock()
        self._current_template = None   # absolute path of the last rendered template
        self._current_context  = None   # reference to the context dict (state.data)

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

        # Inject SSE listener before </body>; append if tag is missing
        if "</body>" in html:
            html = html.replace("</body>", _SSE_SCRIPT + "\n</body>", 1)
        else:
            html += "\n" + _SSE_SCRIPT

        return html

    def get(self, path):
        """Register a GET route handler."""
        def decorator(fn):
            self._routes[("GET", path)] = fn
            return fn
        return decorator

    def post(self, path):
        """Register a POST route handler."""
        def decorator(fn):
            self._routes[("POST", path)] = fn
            return fn
        return decorator

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
                handler = app._routes.get(("GET", path))
                if handler is None:
                    self.send_error(404, "Not found")
                    return
                self._respond(handler())

            # --- POST --------------------------------------------------
            def do_POST(self):
                path = urlparse(self.path).path
                handler = app._routes.get(("POST", path))
                if handler is None:
                    self.send_error(404, "Not found")
                    return
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length else b""
                self._respond(handler(_Request(raw)))

            # --- helpers -----------------------------------------------
            def _respond(self, result):
                if isinstance(result, str):
                    body = result.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif isinstance(result, dict):
                    body = json.dumps(result).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

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


class _Request:
    """Minimal request object passed to POST handlers."""
    __slots__ = ("body", "json")

    def __init__(self, body_bytes):
        self.body = body_bytes
        try:
            self.json = json.loads(body_bytes)
        except Exception:
            self.json = {}
