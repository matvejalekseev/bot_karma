from messages import MESSAGES

def is_str(s):
    if s is None or s == 'None' or s == '':
        return False
    else:
        return True


def prettyUsername(n,un):
    try:
        if is_str(un):
            user = '<a href="https://t.me/' + un +'">' + n + '</a>'
        else:
            user = n
        return user
    except:
        return MESSAGES['error']