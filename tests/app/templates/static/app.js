function updatePrice() {
  var name  = document.getElementById('name').value.trim();
  var price = parseFloat(document.getElementById('price').value);
  if (!name || isNaN(price)) return;

  fetch('/api/product/price', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Sucuri-Token': window.__sucuri_token || '' },
    body: JSON.stringify({ name: name, price: price.toFixed(2) })
  });
}

function addProduct() {
  var name  = document.getElementById('newName').value.trim();
  var price = parseFloat(document.getElementById('newPrice').value);
  if (!name || isNaN(price)) return;

  fetch('/api/product/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Sucuri-Token': window.__sucuri_token || '' },
    body: JSON.stringify({ name: name, price: price.toFixed(2) })
  });

  document.getElementById('newName').value  = '';
  document.getElementById('newPrice').value = '';
}
