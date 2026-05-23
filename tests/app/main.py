import os
from sucuri.server import SucuriApp

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


if __name__ == "__main__":
    app.run(port=8080)
