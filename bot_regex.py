"""
Plugin for reactions to specific messages based on combination of network, channel, and specific
phrase, when all of them are matched using regular expressions.

HexChat Python Interface: http://hexchat.readthedocs.io/en/latest/script_python.html
IRC String Formatting: https://github.com/myano/jenni/wiki/IRC-String-Formatting
"""

import logging
from os import path
import re
import sys

import hexchat

__module_name__ = 'bot_regex'
__module_description__ = 'Simple private bot'
__module_version__ = '1.0'

LOG = '~/bot_regex.log'
FORMAT = '%(asctime)-24s %(levelname)-9s %(message)s'
logging.basicConfig(filename=path.expanduser(LOG), format=FORMAT, level=logging.DEBUG)

def handle_exception(exc_type, exc_value, exc_traceback):
    logging.error('Uncaught exception', exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception


def on_case_expand(r):
    hexchat.prnt('\x0313 https://access.redhat.com/support/cases/#/case/{}'.format(r.group(1)))

# All regexes are checked as case insensitive
# Network | Channel | Phrase
REGEXES = {
    r'RedHat': {
        r'#sbr-security': [
            (r'14(\d{8})', on_case_expand),
        ],
    },
}


def check_debug(network, channel, phrase):
    """
    Function for checking if message passes some or all regex matches. For message to call callback
    it needs to pass network, channel, and phrase test. Useful for regex debugging.

    Args:
        network (str): active network
        channel (str): active channel
        phrase (str): checked phrase

    Returns:
        list: list of regexes which matched and callback function if one should be called
    """
    results = []
    for checked_network in REGEXES:
        if re.search(checked_network, network, re.IGNORECASE):
            results.append([checked_network])
            for checked_channel in REGEXES[checked_network]:
                if re.search(checked_channel, channel, re.IGNORECASE):
                    results.append([checked_network, checked_channel])
                    for checked_phrase, callback in REGEXES[checked_network][checked_channel]:
                        if re.search(checked_phrase, phrase, re.IGNORECASE):
                            results.append([checked_network, checked_channel, checked_phrase,
                                            callback])
    return results


def check(network, channel, phrase):
    """
    Function for checking if message should call callback based on its phrase, network, and channel.
    It calls appropriate callback if needed with SRE_Match object from the last comparison as
    the first argument.

    Args:
        network (str): active network
        channel (str): active channel
        phrase (str): checked phrase
    """
    for checked_network in REGEXES:
        if re.search(checked_network, network, re.IGNORECASE):
            for checked_channel in REGEXES[checked_network]:
                if re.search(checked_channel, channel, re.IGNORECASE):
                    for checked_phrase, callback in REGEXES[checked_network][checked_channel]:
                        r = re.search(checked_phrase, phrase, re.IGNORECASE)
                        if r:
                            logging.info('Phrase: "{}"'.format(repr(phrase)))
                            callback(r)


def on_debug(word, word_eol, userdata):
    """
    Callback function for 'bot-debug' command, which can be used for debugging this plugin and
    regex config.

    Command usage:
        /bot-debug Tested phrase which will or will call callback
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
        if len(line) > 3:
            result = '\x034 ==> CALLBACK'
        hexchat.prnt('\x032 -> {}{}'.format(' | '.join(['"{}"'.format(a) for a in line]), result))
    check(network, channel, phrase)
    return hexchat.EAT_ALL


def on_check_msg(word, word_eol, userdata):
    """
    Callback function for checking if phrase needs to invoke a callback function.
    """
    phrase = word[1]
    network = hexchat.get_info('network')
    channel = hexchat.get_info('channel')
    check(network, channel, phrase)
    return hexchat.EAT_NONE


hexchat.prnt('{}, version {}'.format(__module_name__, __module_version__))
hexchat.hook_print('Channel Message', on_check_msg)
hexchat.hook_print('Channel Action', on_check_msg)
hexchat.hook_command('bot-debug', on_debug)
