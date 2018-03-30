import os

files = {}
rules = []

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
    
    teste = []
    code = """
for a in range(len(obj['var'])):
    teste.append(obj['var'][a])
"""
    print(code)
    exec(code)

    print(teste)

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
    tabulation = ''

    for textline in text:
        rule = {}
        ctrl = 1

        if space == 0 and spaces(textline) > 0 and tabulation == '':
            for i in range(spaces(textline)):
                tabulation = tabulation + ' '

        if '<' in textline and instr(textline, '>') > instr(textline, '<'):
            ruletext = ruletxt(textline)
            ruleline = ruletext.split(' ')
            space = spaces(textline)

            if not ('end' in ruleline[0]):
                rule['id'] = ctrl
                rule['space'] = space
                rule['type'] = ruleline[0]
                rule['rule'] = ruletext
                rule['processing'] = True
                rule['text'] = []
                rules.append(rule)
                result.append('<' + str(ctrl) + '>')

                ctrl += 1
                continue
        
        # if len(block) > 0 and rowfor == False:

        opened = [elem for elem in rules if elem['space'] == space and elem['type'] == 'for' and elem['processing'] == True]

        if len(opened) > 0:
            if 'endfor' in textline:
                opened[0]['processing'] = False

            else:
                opened[0]['text'].append(textline)
            
            for a in range(len(rules)):
                if rules[a]['space'] == opened[0]['space'] and rules[a]['type'] == opened[0]['type'] and rules[a]['processing'] == True:
                    rules[a] = opened[0]
        else:
            result.append(textline)

    if len(rules) > 0:
        for textline in result:
            for a in range(len(rules)):
                if textline.strip() == '<' + str(rules[a]['id']) + '>':
                    if rules[a]['type'] == 'for':
                        rule = rules[a]['rule'].split(' ')
                        stxt = ''

                        ruletext = 'for ' + rule[1] + " in range(len(obj['" + rule[3] + "'])):\n"
                        
                        for x in range(len(rules[a]['text'])):
                            text = rules[a]['text'][x].replace('\n','')
                            text = text.replace('#' + rule[1], "' + str(obj['" + rule[3] + "'][" + rule[1] + "]) + '")
                            ruletext = ruletext + tabulation + "result.append('" + text + "')" + '\n'
                        
                        exec(ruletext)
                        
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