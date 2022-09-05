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
            repeat = False
            for template in self.templates.values():
                if template.has_include():
                    for temp in template.presets.include.values():
                        temps.add(temp)
                    repeat = True
                    continue
            if temps:
                for temp in temps:
                    self._add_template(temp)
    
    def _add_template(self, file):
        template = Template(file)
        self.templates[template.import_name()] = template
        for temp in self.templates.values():
            temp.remove_include(template.import_name())
