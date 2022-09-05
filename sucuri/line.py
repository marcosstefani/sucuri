presets = ['include', 'style', 'script']

class Line:
    def __init__(self, line):
        self.line = line.replace('\n', '')
        self.preset = None
        values = self.line.strip().split(' ')
        if len(values) == 2 and values[0].strip() in presets:
            self.preset = [values[0].strip(), values[1].strip()]
    
    def is_empty(self):
        return len(self.line.strip()) == 0
