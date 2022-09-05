from .template import Template

class Sucuri:
    def __init__(self, file):
        self.file = file
        self.templates = {}
    
    def render(self):
        self._add_template(self.file)
        
        repeat = True
        while repeat:
            temps = set()
            for template in self.templates.values():
                if template.has_include():
                    temps.add(template.presets.include.values())
                    continue
            for temp in temps:
                self._add_template(temp)
            repeat = False
    
    def _add_template(self, file):
        template = Template(file)
        self.templates[template.file_name] = template
