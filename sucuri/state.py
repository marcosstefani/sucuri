class State:
    """
    Observable state dict for the Sucuri live server.

    Top-level key assignments trigger an automatic re-render of the
    watch block that depends on that key and broadcast it to all
    connected browsers via SSE.

    For nested mutations, call state.notify(key) explicitly:

        state.data["products"][0]["price"] = 9.99
        state.notify("products")           # pushes the update

    For top-level reassignments, it is automatic:

        state["products"] = new_list       # pushes automatically
    """

    def __init__(self, initial_data=None):
        self._data = dict(initial_data or {})
        self._broadcast_fn = None

    @property
    def data(self):
        return self._data

    def _set_broadcast(self, fn):
        self._broadcast_fn = fn

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value
        self.notify(key)

    def notify(self, key):
        """Manually trigger a partial re-render for the given watch key."""
        if self._broadcast_fn:
            self._broadcast_fn(key)
