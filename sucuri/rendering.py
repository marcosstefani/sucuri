from .files import Files

def template(fileName, obj=None):
    files = Files()

    files.add( fileName )
    return files.template( fileName, obj )
