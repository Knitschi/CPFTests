

import Sources.CPFBuildscripts.python.miscosaccess as miscosaccess

if __name__ == '__main__':
    mso = miscosaccess.MiscOsAccess()
    mso.execute_command_output('ping -n 2 datenbunker')