# Run a test server.
from modflask import app
app.run(host='localhost', port=8080, debug=True)