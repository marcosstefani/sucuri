# Sucuri Live Server — Demo App

A minimal e-commerce demo that exercises the reactive `watch` feature of the Sucuri live server.

## Running

From the **root of the repository**:

```bash
sucuri serve tests/app/main.py
```

Then open [http://127.0.0.1:8080](http://127.0.0.1:8080) in your browser.

To use a different port:

```bash
sucuri serve tests/app/main.py --port 3000
```

## What to test

### Via the browser UI

The page has two forms in the sidebar:

| Form | What it does |
|---|---|
| **Update price** | Fill in the exact product name and a new price, then click **Apply** |
| **Add product** | Fill in a name and price, then click **Add** |

Changes are reflected **instantly** in the product grid — only the `watch products` block is replaced in the DOM, no full page reload.

### Via curl

**Update the price of an existing product:**
```bash
curl -X POST http://127.0.0.1:8080/api/product/price \
  -H "Content-Type: application/json" \
  -d '{"name": "Widget A", "price": "2.50"}'
```

**Add a new product:**
```bash
curl -X POST http://127.0.0.1:8080/api/product/add \
  -H "Content-Type: application/json" \
  -d '{"name": "Widget D", "price": "15.99"}'
```

Open the browser before running the curl commands to watch the DOM update live.

## How the reactivity works

```
Browser GET /           → server renders shop.suc with current state → full HTML
Browser GET /events     → SSE connection stays open (persistent stream)

curl POST /api/...      → handler mutates state
                        → state.notify("products") triggers partial re-render
                        → server sends: { "id": "products", "html": "<div ...>" }

Browser receives event  → JS replaces document.querySelector('[data-suc-watch="products"]').outerHTML
                        → only the product grid updates, nothing else
```

## File structure

```
tests/app/
├── main.py                  ← SucuriApp entry point (routes + state)
└── templates/
    ├── shop.suc             ← template with two watch blocks: products and cart
    └── static/
        ├── style.css
        └── app.js           ← updatePrice() and addProduct() JS helpers
```

## Key concepts shown

- `watch products` in the template marks a reactive region tied to the `products` key
- `state["products"] = new_list` triggers an automatic broadcast (top-level assignment)
- `state.data["products"][0]["price"] = x` + `state.notify("products")` for nested mutations
- Multiple independent `watch` blocks (`products` and `cart`) update separately
