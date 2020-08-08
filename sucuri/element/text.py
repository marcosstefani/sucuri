class Text(object):
    def __init__(self, value, variables={}):
        self.value = value
        self.variables = variables

    def render(self):
        self._replace_variables()
        self._clean()
        return self.value

    def _replace_variables(self):
        value = self.value
        for key in self.variables:
            old = '{' + key + '}'
            new = self.variables[key]
            value = value.replace(old, new)
        self.value = value
    
    def _clean(self):
        one_line = self.value.replace("\n", " ")
        split = one_line.split("|")
        self.value = "\n".join(map(str.strip, split))
