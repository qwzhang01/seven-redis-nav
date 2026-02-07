
def log(func):
    def wrapper(*args, **kw):
       print('call %s():' % func.__name__)
       return func(*args, **kw)
    return wrapper

@log
def test(w):
    return "111" + w
    
    
print(test("0000"))

