import os

files = {}

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
    
    newtext = inject(text)

    for x in range(0, len(newtext)):
        textline = newtext[x]
        
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
    return result

def inject(text):
    local = os.getcwd()
    includes = []
    result = []
    for textline in text:
        if len(textline.strip()) == 0:
            continue

        aux = textline.strip().split(' ', 1)
        if aux[0].strip() == 'include' and len(aux) == 2:
            includes.append(aux[1])
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
                    lines = loadfile(includes[i] + '.suc')
                    for y in range(len(lines)):
                        result.append(space + lines[y] + '\n')
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