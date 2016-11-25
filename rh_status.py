"""
Plugin which provides a command to change nickname on RH IRC server but not on the others.

HexChat Python Interface: http://hexchat.readthedocs.io/en/latest/script_python.html
IRC String Formatting: https://github.com/myano/jenni/wiki/IRC-String-Formatting
"""

import hexchat

__module_name__ = 'rh_status'
__module_description__ = 'Change nick only on RH server'
__module_version__ = '1.0'


def on_rh_nick(word, word_eol, userdata):
    """
    Callback function which changes nickname, but only on server/network 'RedHat'.

    Command usage:
        /rh-nick new_nick
    """
    new_nick = word[1]
    rh = hexchat.find_context(server='RedHat')
    rh.command('nick {}'.format(new_nick))
    return hexchat.EAT_HEXCHAT


hexchat.prnt('{}, version {}'.format(__module_name__, __module_version__))
hexchat.hook_command('rh-nick', on_rh_nick)
