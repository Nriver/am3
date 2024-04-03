import shutil


def detect_init_system():
    # 参考 https://github.com/Unitech/pm2/blob/master/lib/API/Startup.js
    init_system_dict = {
        'systemctl': 'systemd',
        'update-rc.d': 'upstart',
        'chkconfig': 'systemv',
        'rc-update': 'openrc',
        'launchctl': 'launchd',
        'sysrc': 'rcd',
        'rcctl': 'rcd-openbsd',
        'svcadm': 'smf'
    }
    for x in init_system_dict:
        res = shutil.which(x)
        if res:
            return init_system_dict[x]


if __name__ == '__main__':
    print(detect_init_system())
