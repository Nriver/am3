alias_dict = {
    # 命令的alias设置
    'delete': ('del', 'dele', 'delete'),
    'help': ('h', 'help', '-h', '--help'),
    'list': ('l', 'ls', 'lis', 'list'),
    'load': ('ld', 'load',),
    'log': ('log', 'logs'),
    'restart': ('re', 'res', 'restart',),
    'save': ('sav', 'save'),
    'start': ('st', 'star', 'start',),
    'startup': ('startup',),
    'stop': ('sto', 'stop'),
    # api 命令
    'api': ('api',),
    'init': ('init',),
}

def get_aliases(action):
    return alias_dict.get(action, [])

if __name__ == '__main__':
    print(get_aliases('list'))