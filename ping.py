

import Sources.CPFBuildscripts.python.miscosaccess as miscosaccess

if __name__ == '__main__':
    osa = miscosaccess.MiscOsAccess()
    system = osa.system()
    if system == 'Windows':
        osa.execute_command_output('ping -n 2 www.google.com')
    elif system == 'Linux':
        osa.execute_command_output('ping -c 2 www.google.com')
    else:
        raise Exception('Unknown OS')

