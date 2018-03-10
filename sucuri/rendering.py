import json
from globals import _app_stack

def read():
    ctx = _app_stack.top
    print('teste')
    print(ctx)