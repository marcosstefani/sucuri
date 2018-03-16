import json, os

def rendering():
    local = os.getcwd()
    arq = open(local + '/app/templates/teste.suc', 'r')
    text = arq.readlines()
    space = 0
    tagclose = []
    result = ''
    for textline in text :
        ctrl = transform(textline)
        result += ctrl[0]
        if space < spaces(textline):
            tagclose.append(ctrl[1])
        elif space >= spaces(textline) and not(space == 0 and spaces(textline) == 0):
            result += '</' + ctrl[1] + '>'
        
        space = spaces(textline)
    arq.close()
    for i in reversed(range(len(tagclose))):
        result += '</' + str(tagclose[i]) + '>'
    # print(result)
    return result

def spaces(text):
    result = 0
    for i in range(len(text)):
        if text[i] != ' ':
            result = i
            break
    return result

def transform(text):
    msg = text.strip()
    tag = text.strip()
    properties = ''
    txt = ''

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