import os

files = {}
styles = []
scripts = []

def loadfile(filename):
    if not (filename in files):
        local = os.getcwd()
        arq = open(local + '/' + filename, 'r')
        files[filename] = arq.readlines()
        arq.close()
    return files.get(filename)

def template(filename, obj=None):
    text = loadfile(filename)
    space = 0
    tabulation = 0
    tags = []
    result = ''

    text = inject(text)
    if obj:
        text = addrules(text, obj)

    for x in range(0, len(text)):
        textline = text[x]
        
        if len(textline) == 0:
            continue

        ctrl = transform(textline, obj)
        
        if ctrl[1] != '|':
            tags.append(ctrl[1])

            if space == 0 and spaces(textline) > 0:
                tabulation = spaces(textline) - space
            
            if tabulation > 0 and space >= spaces(textline):
                quantity = ((space - spaces(textline)) / tabulation) + 1

                if quantity == 0 and len(tags) > 0 and space > 0:
                    lastreg = len(tags) -2
                    result += '</' + tags[lastreg] + '>'
                    tags.pop(lastreg)

                for i in reversed(range(0, int(quantity))):
                    lastreg = len(tags) -2
                    result += '</' + tags[lastreg] + '>'
                    tags.pop(lastreg)
        
        else:
            msg = textline.strip()
            ctrl[0] = msg.replace('|','\n')

        result += ctrl[0]

        space = spaces(textline)

    for i in reversed(range(len(tags))):
        result += '</' + str(tags[i]) + '>'

    
    if len(styles) > 0:
        result += '<style>'
        for s in range(len(styles)):
            lines = loadfile(styles[s])
            for y in range(len(lines)):
                result += lines[y]
        result += '</style>'
    
    if len(scripts) > 0:
        result += '<script>'
        for s in range(len(scripts)):
            lines = loadfile(scripts[s])
            for y in range(len(lines)):
                result += lines[y]
        result += '</script>'

    return result

def inject(text):
    includes = []
    result = []
    for textline in text:
        if len(textline.strip()) == 0:
            continue

        aux = textline.strip().split(' ', 1)
        if aux[0].strip() == 'include' and len(aux) == 2:
            includes.append(aux[1])
            continue
        
        if aux[0].strip() == 'style' and len(aux) == 2:
            filename = aux[1] + '.css'
            styles.append(filename)
            continue
        
        if aux[0].strip() == 'script' and len(aux) == 2:
            filename = aux[1] + '.js'
            scripts.append(filename)
            continue

        if substring(textline.strip(),0,1) == '+':
            if len(includes) == 0:
                break

            indicative = substring(textline.strip(),1,len(textline.strip())).strip()
            space = ''
            for i in range(spaces(textline)):
                space = space + ' '

            for i in range(0, len(includes)):
                line = includes[i].split('/')
                if line[-1] == indicative:
                    lines = inject(loadfile(includes[i] + '.suc'))
                    
                    for y in range(len(lines)):
                        result.append(space + lines[y])
        else:
            result.append(textline)
    return result

def transform(text, obj=None):
    msg = text.strip()
    properties = ''
    txt = ''

    if obj:
        while instr(msg, '{') > 0:
            data = substring(msg, instr(msg, '{'), instr(msg, '}') +1)
            elem = substring(data, 1, len(data)-1).strip()
            if elem in obj:
                msg = msg.replace(data, str(obj[elem]))
            else:
                msg = msg.replace(data, '')

    tag = msg

    if '(' in msg:
        tag = substring(msg, 0, instr(msg, '('))
        properties = ' ' + substring(msg, instr(msg, '(') +1, instr(msg, ')'))
        if instr(msg, ')') +1 != len(msg):
            txt = substring(msg, instr(msg, ')') +2, len(msg) )
            
    elif ' ' in msg:
        tag = substring(msg, 0, instr(msg, ' '))
        if instr(msg, ' ') +1 != len(msg):
            txt = substring(msg, instr(msg, ' ') +1, len(msg) )

    result = '<' + tag + properties + '>' + txt

    return [result, tag]

def addrules(text, obj):
    result = []
    space = 0
    line = 0
    blocking = False
    spaceBlock = 0

    for textline in text:
        rule = {}
        line += 1

        if isRule(textline):
            ruletext = ruletxt(textline)
            ruleline = ruletext.split(' ')
            space = spaces(textline)

            if not ('end' in ruleline[0]) and not blocking:
                rule['space'] = space
                rule['type'] = ruleline[0]
                rule['rule'] = ruletext
                blocking = True
                spaceBlock = space
                block = ruleblock(text, line - 1, rule, obj)
                
                if len(block) > 0:
                    for blocktext in block:
                        result.append(blocktext)
                
            
            elif 'end' in ruleline[0] and space == spaceBlock:
                blocking = False
        
            continue

        if blocking and not isRule(textline):
            continue

        result.append(textline)
    
    return result

def ruleblock(text, line, rule, obj):
    result = []
    newline = 0
    space = 0
    for textline in text:
        newline += 1
        
        if newline -1 < line:
            continue

        if not isRule(textline) and space == spaces(textline):
            result.append(textline)
        else:
            if newline -1 == line:
                space = spaces(textline)
                continue
            
            ruletext = ruletxt(textline)
            newrule = {}

            if isRule(textline) and space < spaces(textline) and not'end' in textline:
                newrule['space'] = space
                newrule['type'] = ruletext.split(' ')[0]
                newrule['rule'] = ruletext
                newblock = ruleblock(text, newline - 1, newrule, obj)
                for newtext in newblock:
                    result.append(newtext)

            if space == spaces(textline) and 'end' + rule['type'] in textline:
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

                return result
    return result
        
def spaces(text):
    result = 0
    for i in range(len(text)):
        if text[i] != ' ':
            result = i
            break
    return result

def instr(text, char):
    result = 0
    if char in text:
        for i in range(len(text)):
            if text[i] == char:
                result = i
                break
    return result

def substring(text, ini, end):
    size = len(text)
    result = ''
    if ini >= 0 and end > 0 and size > 0 and end > ini:
        end = end - size
        if end != 0:
            result = text[ini:end]
        else:
            result = text[ini:]
    return result

def ruletxt(textline):
    result = substring(textline, instr(textline, '<') +1, instr(textline, '>')).strip()
    while '  ' in result:
        result = result.replace('  ', ' ')
    return result.strip()

def isRule(textline):
    return '<' in textline and instr(textline, '>') > instr(textline, '<')