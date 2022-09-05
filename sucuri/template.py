from .file import File
from .line import Line
from .preset import Preset

class Template:
    def __init__(self, file_name):
        self.file_name = file_name if file_name.endswith('.suc') else file_name + '.suc'
        self.body = []
        self.presets = Preset()
        self._load()
        
    def _load(self):
        file = File(file_name=self.file_name)
        lines = file.load_lines()
        for index in range(0, len(lines)):
            line = Line(lines[index])
            if line.is_empty():
                continue
            
            if not self.presets.add(line.preset):
                self.body.append(line.line)
    
    def has_include(self):
        return len(self.presets.include) > 0
        
    def remove_include(self, file):
        del self.presets.include[file]
