"""
Plugin for better notifications with actions.

HexChat Python Interface: http://hexchat.readthedocs.io/en/latest/script_python.html
IRC String Formatting: https://github.com/myano/jenni/wiki/IRC-String-Formatting
"""

import logging
import re
import subprocess
import sys
import textwrap
from os import path

import dbus
import hexchat

__module_name__ = 'highlights_notifications'
__module_description__ = 'Better notifications with actions'
__module_version__ = '1.1'

NOTIFICATION_SERVER = '/home/skontar/Repos/hexchat-plugins/notification_server.py'

LOG = '~/highlights_notifications.log'
FORMAT = '%(asctime)-24s %(levelname)-9s %(message)s'
logging.basicConfig(filename=path.expanduser(LOG), format=FORMAT, level=logging.DEBUG)


def handle_exception(exc_type, exc_value, exc_traceback):
    logging.error('Uncaught exception', exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception


def server_start():
    logging.info('Starting server')
    subprocess.Popen('python3 {}'.format(NOTIFICATION_SERVER), shell=True)


def get_dbus_interface():
    logging.info('Getting DBus interface for Notification Server')
    try:
        session_bus = dbus.SessionBus()
        proxy = session_bus.get_object('com.skontar.HexChat', '/com/skontar/HexChat')
        interface = dbus.Interface(proxy, dbus_interface='com.skontar.HexChat')
        logging.debug('DBus interface Success')
        return interface
    except dbus.exceptions.DBusException:
        logging.debug('DBus interface Fail')
        server_start()
        return None


def on_focus_tab(word, word_eol, userdata):
    global active_channel
    active_channel = hexchat.get_info('channel')
    logging.info('Changed active tab to %s', active_channel)


def on_highlight_notification(word, word_eol, userdata):
    global interface
    win_status = hexchat.get_info('win_status')
    network = hexchat.get_info('network')
    channel = hexchat.get_info('channel')
    nickname = word[0]
    nickname = re.sub(r'\x03\d+', '', nickname)  # Remove color
    text = word[1]
    message_type = userdata

    if message_type == 'HLT':
        title = 'Highlighted message from: {} ({})'.format(nickname, channel)
    else:
        title = 'Private message from: {} ({})'.format(nickname, network)
    new_text = textwrap.fill(text, 60)

    logging.info('New notification [%s | %s | %s]', network, channel, repr(str(nickname)))
    logging.debug('Application details: [%s | %s]', win_status, active_channel)
    logging.debug('Message type: "%s"', message_type)
    logging.debug('Message: "%s"', text)

    # Ignore notification if window is active and active channel is the one where message arrived
    if win_status == 'active' and channel == active_channel:
        logging.info('Not showing notifications as channel is already active')
        return hexchat.EAT_NONE

    if interface is None:
        logging.debug('No DBus interface prepared')
        interface = get_dbus_interface()

    if interface is None:
        logging.warning('DBus connection to Notification Server fail')
        logging.warning('Notification fallback')
        hexchat.command('TRAY -b "{}" {}'.format(title, text))
    else:
        try:
            logging.info('Sending message to Notification Server through DBus')
            interface.create_notification(nickname, network, channel, title, new_text, message_type)
        except dbus.exceptions.DBusException:
            logging.warning('DBus message to Notification Server fail')
            logging.warning('Notification fallback')
            hexchat.command('TRAY -b "{}" {}'.format(title, text))
            interface = None

    return hexchat.EAT_NONE


def on_unload(userdata):
    global interface
    logging.info('HexChat notification server ending')
    hexchat.prnt('Unloading {}, version {}'.format(__module_name__, __module_version__))
    logging.info('Setting common notifications to normal')
    hexchat.command('set input_balloon_hilight 1')
    hexchat.command('set input_balloon_priv 1')

    try:
        logging.info('Sending Quit message to Notification Server')
        interface.quit()
    except (AttributeError, dbus.exceptions.DBusException):
        logging.warning('Quit message to Notification Server failed')
    logging.info('Explicitly quit')
    exit(1)


active_channel = None
win_status = None
interface = None

logging.info('HexChat notification plugin starting ==============================')

server_start()

hexchat.prnt('{}, version {}'.format(__module_name__, __module_version__))
logging.info('Setting common notifications to suspended')
hexchat.command('set input_balloon_hilight 0')
hexchat.command('set input_balloon_priv 0')
hexchat.hook_print('Focus Tab', on_focus_tab)
hexchat.hook_unload(on_unload)
hexchat.hook_print('Channel Action Hilight', on_highlight_notification, userdata='HLT')
hexchat.hook_print('Channel Msg Hilight', on_highlight_notification, userdata='HLT')
hexchat.hook_print('Private Message', on_highlight_notification, userdata='PVT')
hexchat.hook_print('Private Message to Dialog', on_highlight_notification, userdata='PVT')
hexchat.hook_print('Private Action to Dialog', on_highlight_notification, userdata='PVT')
