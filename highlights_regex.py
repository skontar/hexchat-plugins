"""
Plugin for highlighting based on combination of network, channel, and specific phrase, when all
of them are matched using regular expressions.

HexChat Python Interface: http://hexchat.readthedocs.io/en/latest/script_python.html
IRC String Formatting: https://github.com/myano/jenni/wiki/IRC-String-Formatting
"""

import re

import hexchat

__module_name__ = 'highlight_regex'
__module_description__ = 'Highlighting on a phrase checked against regexes'
__module_version__ = '1.0'

# All regexes are checked as case insensitive
# Network | Channel | Phrase
REGEXES = {
    r'RedHat': {
        r'#-1day': [
            r'high[ -]?touch',
            r'csaw',
        ],
        r'#prodsec-brno': [
            r'(^|[^|_])lunch',  # 'lunch' but not as part of nickname
            r'nepal',
        ],
        r'#brno': [
            r'ping brq',
        ],
        r'^#(?!insights$).*$': [  # not 'insights'
            r'insights'
        ],
        r'#.*': [
            r'\ball:',
            r'ping sbr-security',
            r'ping security',
        ],
    },
    # For debugging
    # r'.*': {
    #     r'#.*': [
    #         r'.*',
    #     ],
    # }
}


def check_debug(network, channel, phrase):
    """
    Function for checking if message passes some or all regex matches. For message to be highlighted
    it needs to pass network, channel, and phrase test. Useful for regex debugging.

    Args:
        network (str): active network
        channel (str): active channel
        phrase (str): checked phrase

    Returns:
        list: list of regexes which matched
    """
    results = []
    for checked_network in REGEXES:
        if re.search(checked_network, network, re.IGNORECASE):
            results.append([checked_network])
            for checked_channel in REGEXES[checked_network]:
                if re.search(checked_channel, channel, re.IGNORECASE):
                    results.append([checked_network, checked_channel])
                    for checked_phrase in REGEXES[checked_network][checked_channel]:
                        if re.search(checked_phrase, phrase, re.IGNORECASE):
                            results.append([checked_network, checked_channel, checked_phrase])
    return results


def check(network, channel, phrase):
    """
    Function for checking if message should be highlighted based on its phrase, network, and
    channel.

    Args:
        network (str): active network
        channel (str): active channel
        phrase (str): checked phrase

    Returns:
        bool: True if message should be highlighted
    """
    for checked_network in REGEXES:
        if re.search(checked_network, network, re.IGNORECASE):
            for checked_channel in REGEXES[checked_network]:
                if re.search(checked_channel, channel, re.IGNORECASE):
                    for checked_phrase in REGEXES[checked_network][checked_channel]:
                        if re.search(checked_phrase, phrase, re.IGNORECASE):
                            return True
    return False


def on_debug(word, word_eol, userdata):
    """
    Callback function for 'regex-debug' command, which can be used for debugging this plugin and
    regex config.

    Command usage:
        /regex-debug Tested phrase which will or will not be highlighted
    """
    phrase = word_eol[1]
    network = hexchat.get_info('network')
    channel = hexchat.get_info('channel')
    hexchat.prnt('\x032 active_network = "{}"'.format(network))
    hexchat.prnt('\x032 active_channel = "{}"'.format(channel))
    hexchat.prnt('\x032 phrase = "{}"'.format(phrase))
    results = check_debug(network, channel, phrase)
    for line in results:
        result = ''
        if len(line) > 2:
            result = '\x034 ==> HIGHLIGHT'
        hexchat.prnt('\x032 -> {}{}'.format(' | '.join(['"{}"'.format(a) for a in line]), result))
    highlight = check(network, channel, phrase)
    hexchat.prnt('\x032 highlight = "{}"'.format(highlight))
    return hexchat.EAT_ALL


def on_check_msg(word, word_eol, userdata):
    """
    Callback function for checking if phrase needs to be highlighted.
    """
    phrase = word[1]
    network = hexchat.get_info('network')
    channel = hexchat.get_info('channel')
    highlight = check(network, channel, phrase)
    if highlight:
        hexchat.command('gui color 3')
        hexchat.emit_print('Channel Msg Hilight', word[0], word[1])
        return hexchat.EAT_ALL
    return hexchat.EAT_NONE


hexchat.prnt('{}, version {}'.format(__module_name__, __module_version__))
hexchat.hook_print('Channel Message', on_check_msg)
hexchat.hook_print('Channel Action', on_check_msg)
hexchat.hook_command('regex-debug', on_debug)
