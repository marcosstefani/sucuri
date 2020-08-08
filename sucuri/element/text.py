class Text(object):
    def __init__(self, value, variables):
        self.value = value
        self.variables = variables

    def render(self):
        value = self.value
        for key in self.variables:
            old = '{' + key + '}'
            new = self.variables[key]
            value = value.replace(old, new)
        return value