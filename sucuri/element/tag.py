class Tag(object):
    def __init__(self, name, value=None, properties=None):
        self.name = name
        self.value = value
        self.properties = properties

    def html(self):
        if self.value:
            return '<{}{}>{}</{}>'.format(self.name, self._properties(), self.value, self.name)
        if not self.properties:
            return '<{}>'.format(self.name)
        return '<{}{} />'.format(self.name, self._properties())

    def _properties(self):
        if self.properties:
            return ' {}'.format(self.properties)
        return ''