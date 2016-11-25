"""
Copies all highlighted messages to a virtual server, so they can be easily found and logged.

HexChat Python Interface: http://hexchat.readthedocs.io/en/latest/script_python.html
IRC String Formatting: https://github.com/myano/jenni/wiki/IRC-String-Formatting
"""

import hexchat

__module_name__ = 'highlights_log'
__module_description__ = 'Copies all highlighted phrases to a new server called Highlights'
__module_version__ = '1.0'

HIGHLIGHTS_TAB = 'Highlights'
LOG_FORMAT = '{} - {} | {}: \x034<\x033\x02{}\x0F\x032{}\x034>\x0F {}'


def highlights_tab():
    """
    Function which will return context of tab for logging highlights. If the tab does not exist, it
    is created.
    """
    context = hexchat.find_context(channel=HIGHLIGHTS_TAB)
    if context is None:
        newtofront = hexchat.get_prefs('gui_tab_newtofront')
        hexchat.command('set -quiet gui_tab_newtofront 0')
        hexchat.command('newserver -noconnect {}'.format(HIGHLIGHTS_TAB))
        hexchat.command('set -quiet gui_tab_newtofront {}'.format(newtofront))
        context = hexchat.find_context(channel=HIGHLIGHTS_TAB)
    return context


def on_log_highlight(word, word_eol, userdata):
    """
    Callback function which writes the highlighted message to logging tab.
    """
    context = highlights_tab()
    network = hexchat.get_info('network')
    channel = hexchat.get_info('channel')
    nickname = word[0]
    text = word[1]
    try:
        rank = word[2]
    except IndexError:
        rank = ''
    event_text = LOG_FORMAT.format(userdata, network, channel, rank, nickname, text)
    context.prnt(event_text)
    return hexchat.EAT_NONE


def on_debug(word, word_eol, userdata):
    """
    Callback function which tests logging interface with simple message.

    Command usage:
        /log-debug
    """
    event_text = LOG_FORMAT.format('DBG', 'network', 'channel', 'rank', 'nickname', 'phrase')
    context = highlights_tab()
    context.prnt(event_text)
    return hexchat.EAT_ALL


hexchat.prnt('{}, version {}'.format(__module_name__, __module_version__))
hexchat.hook_print('Channel Action Hilight', on_log_highlight, userdata='ACT')
hexchat.hook_print('Channel Msg Hilight', on_log_highlight, userdata='MSG')
hexchat.hook_print('Private Message', on_log_highlight, userdata='PVT')
hexchat.hook_print('Private Message to Dialog', on_log_highlight, userdata='PVD')
hexchat.hook_print('Private Action to Dialog', on_log_highlight, userdata='PAD')
hexchat.hook_command('log-debug', on_debug)
