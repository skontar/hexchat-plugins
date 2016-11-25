"""
Plugin for better notifications with actions.

HexChat Python Interface: http://hexchat.readthedocs.io/en/latest/script_python.html
IRC String Formatting: https://github.com/myano/jenni/wiki/IRC-String-Formatting
"""

import subprocess
import textwrap

import dbus
import hexchat

__module_name__ = 'highlights_notifications'
__module_description__ = 'Better notifications with actions'
__module_version__ = '1.0'


def server_start():
    subprocess.Popen('python3 /home/skontar/Python/HexChat/notification_server.py', shell=True)


def get_dbus_interface():
    try:
        session_bus = dbus.SessionBus()
        proxy = session_bus.get_object('com.skontar.HexChat', '/com/skontar/HexChat')
        interface = dbus.Interface(proxy, dbus_interface='com.skontar.HexChat')
        return interface
    except dbus.exceptions.DBusException:
        server_start()
        return None


def focus_tab(word, word_eol, userdata):
    global active_channel
    active_channel = hexchat.get_info('channel')


def highlight_notification(word, word_eol, userdata):
    global interface
    win_status = hexchat.get_info('win_status')
    network = hexchat.get_info('network')
    channel = hexchat.get_info('channel')
    nickname = word[0]
    text = word[1]
    message_type = userdata

    if message_type == 'HLT':
        title = 'Highlighted message from: {} ({})'.format(nickname, channel)
    else:
        title = 'Private message from: {} ({})'.format(nickname, network)
    new_text = textwrap.fill(text, 60)

    # Ignore notification if window is active and active channel is the one where message arrived
    if win_status == 'active' and channel == active_channel:
        return hexchat.EAT_NONE

    if interface is None:
        interface = get_dbus_interface()

    if interface is None:
        hexchat.command('TRAY -b "{}" {}'.format(title, text))
    else:
        try:
            interface.create_notification(nickname, network, channel, title, new_text, message_type)
        except dbus.exceptions.DBusException:
            hexchat.command('TRAY -b "{}" {}'.format(title, text))
            interface = None

    return hexchat.EAT_NONE


def unload(userdata):
    global interface
    hexchat.prnt('Unloading {}, version {}'.format(__module_name__, __module_version__))
    hexchat.command('set input_balloon_hilight 1')
    hexchat.command('set input_balloon_priv 1')

    try:
        interface.quit()
    except (AttributeError, dbus.exceptions.DBusException):
        pass
    # When interface is used at least once, unloading plugin hangs unless Exception is raised
    raise Exception


active_channel = None
win_status = None
interface = None

server_start()

hexchat.prnt('{}, version {}'.format(__module_name__, __module_version__))
hexchat.command('set input_balloon_hilight 0')
hexchat.command('set input_balloon_priv 0')
hexchat.hook_print('Focus Tab', focus_tab)
hexchat.hook_unload(unload)
hexchat.hook_print('Channel Action Hilight', highlight_notification, userdata='HLT')
hexchat.hook_print('Channel Msg Hilight', highlight_notification, userdata='HLT')
hexchat.hook_print('Private Message', highlight_notification, userdata='PVT')
hexchat.hook_print('Private Message to Dialog', highlight_notification, userdata='PVT')
hexchat.hook_print('Private Action to Dialog', highlight_notification, userdata='PVT')
