import os
from sucuri.server import SucuriApp, Response, redirect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = SucuriApp(template_dir=os.path.join(BASE_DIR, "templates"))

state = app.state({
    "title": "Sucuri Live Shop",
    "products": [
        {"name": "Widget A", "price": "9.99"},
        {"name": "Widget B", "price": "19.99"},
        {"name": "Widget C", "price": "4.50"},
    ],
    "cart": {"count": 0, "total": "0.00"},
})


@app.get("/")
def index():
    return app.render("shop.suc", state.data)


@app.post("/api/product/price")
def update_price(request):
    name      = request.json.get("name", "")
    new_price = request.json.get("price", "0")

    for product in state.data["products"]:
        if product["name"] == name:
            product["price"] = new_price
            break

    # Nested mutation: notify manually so the watch block re-renders
    state.notify("products")
    return {"ok": True}


@app.post("/api/product/add")
def add_product(request):
    name  = request.json.get("name", "").strip()
    price = request.json.get("price", "0")

    if name:
        state.data["products"].append({"name": name, "price": price})
        state.notify("products")

    return {"ok": True}


@app.post("/api/product/add-form")
def add_product_form(request):
    name  = request.form.get("name", "").strip()
    price = request.form.get("price", "0")

    if name:
        state.data["products"].append({"name": name, "price": price})
        state.notify("products")
        return {"ok": True}

    return {"ok": False, "error": "name required"}


@app.get("/api/product/<index>")
def get_product(index):
    """Dynamic GET — return a single product by index."""
    try:
        product = state.data["products"][int(index)]
        return {"ok": True, "product": product}
    except (IndexError, ValueError):
        return {"ok": False, "error": "product not found"}


@app.post("/api/product/<index>/price")
def update_price_by_index(request, index):
    """Dynamic POST — update a product's price by index."""
    try:
        new_price = request.json.get("price", "0")
        state.data["products"][int(index)]["price"] = new_price
        state.notify("products")
        return {"ok": True}
    except (IndexError, ValueError):
        return {"ok": False, "error": "product not found"}


@app.put("/api/product/<index>")
def replace_product(request, index):
    """Dynamic PUT — replace a product entirely by index."""
    try:
        name  = request.json.get("name", "").strip()
        price = request.json.get("price", "0")
        if not name:
            return {"ok": False, "error": "name required"}
        state.data["products"][int(index)] = {"name": name, "price": price}
        state.notify("products")
        return {"ok": True}
    except (IndexError, ValueError):
        return {"ok": False, "error": "product not found"}


@app.delete("/api/product/<index>")
def delete_product(request, index):
    """Dynamic DELETE — remove a product by index."""
    try:
        state.data["products"].pop(int(index))
        state.notify("products")
        return {"ok": True}
    except (IndexError, ValueError):
        return {"ok": False, "error": "product not found"}


@app.get("/api/error-demo")
def error_demo():
    """Intentionally raises to demonstrate the 500 handler."""
    raise RuntimeError("This is a demo error!")


# --- Response helpers demo ---------------------------------------------------

@app.get("/demo/redirect")
def demo_redirect():
    """Redirects back to home, demonstrating redirect()."""
    return redirect("/")


@app.post("/api/product/add-validated")
def add_validated(request):
    """Returns 201 on success, 422 when name is missing."""
    name  = request.json.get("name", "").strip()
    price = request.json.get("price", "0")
    if not name:
        return Response({"error": "name is required"}, status=422)
    state.data["products"].append({"name": name, "price": price})
    state.notify("products")
    return Response({"ok": True, "total": len(state.data["products"])}, status=201)


@app.error(404)
def not_found():
    return """
    <html><head><title>404</title></head>
    <body style="font-family:system-ui;text-align:center;padding:4rem">
      <h1 style="font-size:4rem;color:#1a1a2e">404</h1>
      <p>Page not found.</p>
      <a href="/">Go back</a>
    </body></html>
    """


@app.error(500)
def server_error(exc):
    return {"error": str(exc), "type": type(exc).__name__}


if __name__ == "__main__":
    app.run(port=8080)
