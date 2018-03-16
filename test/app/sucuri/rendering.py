import json, os
# from .globals import _app_stack

def rendering():
    local = os.getcwd()
    arq = open(local + '/app/templates/teste.suc', 'r')
    text = arq.readlines()
    for line in text :
        # print(line)
        # print(spaces(line))
        print(tag(line))
    arq.close()

def spaces(text):
    result = 0
    for i in range(len(text)):
        if text[i] != ' ':
            result = i
            break
    return result

def tag(text):
    result = text.strip()

    if '(' in result:
        result = substring(result, 0, instr(result, '('))
    elif ' ' in result:
        result = substring(result, 0, instr(result, ' '))

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
    result = ''
    size = len(text)
    if ini >= 0 and end > 0 and size > 0 and end > ini:
        end = end - size
        result = text[ini:end]
    return result