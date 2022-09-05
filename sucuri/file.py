import os

class File:
    def __init__(self, file_name):
        self.file_name = file_name
    
    def load_lines(self):
        root = os.getcwd()
        readFile = open( root + '/' + self.file_name, 'r' , encoding='utf-8')
        lines = readFile.readlines()
        readFile.close()
        
        return lines
