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

function getProduct() {
  var index = document.getElementById('getIndex').value;
  fetch('/api/product/' + index)
    .then(function(r) { return r.json(); })
    .then(function(d) {
      document.getElementById('getResult').textContent =
        d.ok ? JSON.stringify(d.product, null, 2) : d.error;
    });
}

function updateByIndex() {
  var index = document.getElementById('putIndex').value;
  var price = parseFloat(document.getElementById('putPrice').value);
  if (isNaN(price)) return;
  fetch('/api/product/' + index + '/price', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Sucuri-Token': window.__sucuri_token || '' },
    body: JSON.stringify({ price: price.toFixed(2) })
  });
}

function replaceProduct() {
  var index = document.getElementById('repIndex').value;
  var name  = document.getElementById('repName').value.trim();
  var price = parseFloat(document.getElementById('repPrice').value);
  if (!name || isNaN(price)) return;
  fetch('/api/product/' + index, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', 'X-Sucuri-Token': window.__sucuri_token || '' },
    body: JSON.stringify({ name: name, price: price.toFixed(2) })
  });
}

function deleteProduct() {
  var index = document.getElementById('delIndex').value;
  fetch('/api/product/' + index, {
    method: 'DELETE',
    headers: { 'X-Sucuri-Token': window.__sucuri_token || '' }
  });
}

function triggerError() {
  fetch('/api/error-demo')
    .then(function(r) { return r.json(); })
    .then(function(d) {
      document.getElementById('errorResult').textContent = JSON.stringify(d, null, 2);
    });
}

/* ---- response helpers demo ---- */
function addValidated() {
  var name  = document.getElementById('valName').value;
  var price = parseFloat(document.getElementById('valPrice').value) || 0;
  fetch('/api/product/add-validated', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Sucuri-Token': window.__sucuri_token || '' },
    body: JSON.stringify({ name: name, price: price.toFixed(2) })
  })
  .then(function(r) {
    return r.json().then(function(d) { return { status: r.status, data: d }; });
  })
  .then(function(res) {
    document.getElementById('validatedResult').textContent =
      'HTTP ' + res.status + '\n' + JSON.stringify(res.data, null, 2);
  });
}

/* ---- modal de cadastro (form data demo) ---- */
function openModal() {
  document.getElementById('modalOverlay').classList.add('open');
  document.getElementById('modalName').focus();
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
  document.getElementById('productForm').reset();
}

function overlayClick(e) {
  if (e.target === e.currentTarget) { closeModal(); }
}

function submitProductForm(e) {
  e.preventDefault();
  var body = new URLSearchParams(new FormData(e.target));
  fetch('/api/product/add-form', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'X-Sucuri-Token': window.__sucuri_token || ''
    },
    body: body.toString()
  })
  .then(function(r) { return r.json(); })
  .then(function(d) { if (d.ok) { closeModal(); } });
}
