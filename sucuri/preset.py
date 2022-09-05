class Preset:
    def __init__(self):
        self.include = {}
        self.style = set()
        self.script = set()
    
    def add(self, preset):
        if preset and len(preset) == 2:
            if preset[0] == 'include':
                self.include["+" + preset[1].split("/")[-1]] = preset[1]
            
            if preset[0] == 'style':
                self.style.add(preset[1])
            
            if preset[0] == 'script':
                self.script.add(preset[1])
                
            return True
        return False
