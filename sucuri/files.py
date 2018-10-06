import os

class Files:
    def __init__( self ):
        self.cashed = {}
        self.styles = []
        self.scripts = []

    def add( self, fileName ):
        if not ( fileName in self.cashed ):
            root = os.getcwd()
            readFile = open( root + '/' + fileName, 'r' )
            self.cashed[fileName] = readFile.readlines()
            readFile.close()

    def get( self, fileName ):
        return self.cashed.get( fileName )

    def update( self, fileName, value ):
        self.cashed[ fileName ] = value

    def template( self, fileName, obj=None ):
        space = 0
        tabulation = 0
        result = ''
        tags = []

        text = self._inject(fileName, obj)

        if obj:
            text = _addrules(text, obj)

        for x in range(0, len(text)):
            textline = text[x]

            if len(textline) == 0:
                continue

            ctrl = _transform( textline, obj )

            textline = text[ x ]

            if len( textline ) == 0:
                continue

            ctrl = _transform( textline, obj )

            if ctrl[1] != '|':
                tags.append( ctrl[ 1 ] )

                if space == 0 and _spaces( textline ) > 0:
                    tabulation = _spaces( textline ) - space

                if tabulation > 0 and space >= _spaces(textline):
                    quantity = ( ( space - _spaces( textline ) ) / tabulation ) + 1

                    if quantity == 0 and len( tags ) > 0 and space > 0:
                        lastreg = len( tags ) -2
                        result += '</' + tags[ lastreg ] + '>'
                        tags.pop( lastreg )

                    for i in reversed(range(0, int(quantity))):
                        lastreg = len( tags ) -2
                        result += '</' + tags[ lastreg ] + '>'
                        tags.pop( lastreg )

            else:
                msg = textline.strip()
                ctrl[0] = msg.replace('|','\n')

            result += ctrl[0]

            space = _spaces(textline)

        for i in reversed( range( len( tags ) ) ):
            result += '</' + str( tags[ i ] ) + '>'

        if len(self.styles) > 0:
            result += '<style>'
            for s in range(len(self.styles)):
                lines = self.cashed.get( self.styles[s] )

                for y in range(len(lines)):
                    result += lines[y]
            result += '</style>\n'
        
        if len(self.scripts) > 0:
            result += '<script>'
            for s in range(len(self.scripts)):
                lines = self.cashed.get( self.scripts[s] )
                for y in range(len(lines)):
                    result += lines[y]
            result += '</script>\n'

        return result

    def _inject( self, fileName, obj=None ):
        includes = []
        result = []
        for text in self.cashed.get( fileName ):
            if len( text.strip() ) == 0:
                continue

            aux = text.strip().split( ' ', 1 )
            if aux[0].strip() == 'include' and len( aux ) == 2:
                self.add( aux[ 1 ] + '.suc' )
                includes.append( aux[1] )
                continue

            if aux[ 0 ].strip() == 'style' and len( aux ) == 2:
                name = aux[ 1 ] + '.css'
                self.add( name )
                self.styles.append( name )
                continue

            if aux[ 0 ].strip() == 'script' and len( aux ) == 2:
                name = aux[ 1 ] + '.js'
                self.add( name )
                self.scripts.append( name )
                continue

            if _substring( text.strip(), 0, 1 ) == '+':
                indicative = _substring( text.strip() , 1, len( text.strip() ) ).strip()
                space = ''

                for i in range(_spaces( text )):
                    space += ' '

                for i in range(0, len(includes)):
                    line = includes[i].split('/')

                    if line[-1] == indicative:
                        inj = includes[i] + '.suc'
                        self.add(inj)
                        lines = _replace(self._inject(inj), obj)
                        for y in range(0, len(lines)):
                            result.append(space + lines[y])

            else:
                result.append(_replace(text, obj))

        return result

def _transform( text, obj=None ):
    msg = text.strip()
    properties = ''
    txt = ''

    if msg.split('(')[0] == "list":
        params = msg.split('(')[1].split(')')
        n = "\n"
        result = "<ul>" + n
        newresult = []
        textblock = "for value in obj['" + params[0] + "']:\n"
        textblock += "    newresult.append('<li> ' + str(value) + ' </li>' + n)\n"

        exec(textblock)
        for line in newresult:
            result += line
        return [result, "ul"]

    if obj:
        while _instr( msg, '{' ) > 0:
            data = _substring( msg, _instr( msg, '{' ), _instr( msg, '}' ) + 1 )
            elem = _substring( data, 1, len( data ) - 1 ).strip()
            if elem in obj:
                msg = msg.replace( data, str( obj[ elem ] ) )
            else:
                msg = msg.replace(data, '')

    tag = msg

    if '(' in msg:
        tag = _substring( msg, 0, _instr( msg, '(' ) )
        properties = ' ' + _substring( msg, _instr( msg, '(' ) + 1, _instr( msg, ')' ) )
        if _instr( msg, ')') +1 != len( msg ):
            txt = _substring( msg, _instr( msg, ')' ) +2, len( msg ) )

    elif ' ' in msg:
        tag = _substring( msg, 0, _instr( msg, ' ' ) )
        if _instr( msg, ' ' ) +1 != len( msg ):
            txt = _substring( msg, _instr( msg, ' ' ) +1, len( msg ) )

    result = '<' + tag + properties + '>\n' + txt

    return [result, tag]

def _addrules( text, obj ):
    result = []
    space = 0
    line = 0
    blocking = False
    spaceBlock = 0

    for textline in text:
        rule = {}
        line += 1

        if _isRule(textline):
            ruletext = _ruletxt(textline)
            ruleline = ruletext.split(' ')
            space = _spaces(textline)

            if not ('end' in ruleline[0]) and not blocking:
                rule['space'] = space
                rule['type'] = ruleline[0]
                rule['rule'] = ruletext
                blocking = True
                spaceBlock = space
                block = _ruleblock(text, line - 1, rule, obj)

                if len(block) > 0:
                    for blocktext in block:
                        result.append(blocktext)


            elif 'end' in ruleline[0] and space == spaceBlock:
                blocking = False

            continue

        if blocking and not _isRule(textline):
            continue

        result.append(textline)

    return result

def _ruleblock( text, line, rule, obj ):
    result = []
    newline = 0
    space = 0
    for textline in text:
        newline += 1

        if newline -1 < line:
            continue

        if not _isRule(textline) and space == _spaces(textline):
            result.append(textline)
        else:
            if newline -1 == line:
                space = _spaces(textline)
                continue

            ruletext = _ruletxt(textline)
            newrule = {}

            if _isRule(textline) and space < _spaces(textline) and not'end' in textline:
                newrule['space'] = space
                newrule['type'] = ruletext.split(' ')[0]
                newrule['rule'] = ruletext
                newblock = _ruleblock(text, newline - 1, newrule, obj)
                for newtext in newblock:
                    result.append(newtext)

            if space == _spaces(textline) and 'end' + rule['type'] in textline:
                splited = rule['rule'].split(' ')
                if splited[0] == 'for':
                    textblock = 'for ' + splited[1] + " in range(len(obj['" + splited[3] + "'])):\n"
                    newresult = []

                    for x in range(len(result)):
                        text = result[x].replace('\n','')
                        text = text.replace('#' + splited[1], '''" + str(obj["''' + splited[3] + '''"][''' + splited[1] + ''']) + "''')
                        textblock = textblock + '''    newresult.append("''' + text + '''")''' + '\n'

                    exec(textblock)
                    if len(newresult) > 0:
                        result = newresult

                elif splited[0] == 'if':
                    newresult = []
                    textblock = "if obj['" + splited[1] + "'] " + splited[2] + " obj['" + splited[3] + "']:\n"
                    for instruct in result:
                        textblock += '''    newresult.append("''' + instruct.replace('\n', '') + '''")''' + '\n'
                    exec(textblock)
                    result = newresult



                return result
    return result

def _spaces(text):
    result = 0
    for i in range(len(text)):
        if text[i] != ' ':
            result = i
            break
    return result

def _instr(text, char):
    result = 0
    if char in text:
        for i in range(len(text)):
            if text[i] == char:
                result = i
                break
    return result

def _substring(text, ini, end):
    size = len(text)
    result = ''
    if ini >= 0 and end > 0 and size > 0 and end > ini:
        end = end - size
        if end != 0:
            result = text[ini:end]
        else:
            result = text[ini:]
    return result

def _replace(text, obj=None):
    if obj:
        while _instr(text, '{') > 0:
            data = _substring(text, _instr(text, '{'), _instr(text, '}') +1)
            elem = _substring(data, 1, len(data) -1).strip()
            idx = ""
            if (_instr(elem, '[') > 0 and _instr(elem, ']') > 0):
                idx = _substring(elem, _instr(elem, '[') +1, _instr(elem, ']'))
                elem = _substring(elem, 0, _instr(elem, '['))
            if elem in obj:
                vlr = ""
                if ( idx == "" ):
                    vlr = str(obj[elem])
                else:
                    l = obj[elem]
                    vlr = str(l[int(idx)])
                text = text.replace(data, vlr)
            else:
                text = text.replace(data, '')
    return text

def _ruletxt(textline):
    result = _substring(textline, _instr(textline, '<') +1, _instr(textline, '>')).strip()
    while '  ' in result:
        result = result.replace('  ', ' ')
    return result.strip()

def _isRule(textline):
    return '<' in textline and _instr(textline, '>') > _instr(textline, '<')
