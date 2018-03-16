# Run a test server.
from app import app
app.run(host='localhost', port=8080, debug=True)