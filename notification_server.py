import logging
import re
import subprocess
import webbrowser

import dbus.service
import gi
import sys
from dbus.mainloop.glib import DBusGMainLoop
from os import path

gi.require_version('Notify', '0.7')
from gi.repository import GLib, Notify

LOG = '~/notification_server.log'
FORMAT = '%(process)-5d %(asctime)-24s %(levelname)-9s %(message)s'
logging.basicConfig(filename=path.expanduser(LOG), format=FORMAT, level=logging.DEBUG)


def handle_exception(exc_type, exc_value, exc_traceback):
    if not issubclass(exc_type, KeyboardInterrupt):  # Keyboard interrupt is common way how to end
        logging.error('Uncaught exception', exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception

WEB_URL_REGEX = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""
HEXCHAT_ICON = '/usr/share/icons/hicolor/scalable/apps/hexchat.svg'
ACTIVATE_HEXCHAT_COMMAND = 'move-to-desktop-and-activate 4'


def find_url(text):
    """
    Returns first found URL in the text.
    """
    logging.debug('Looking for URL')
    r = re.search(WEB_URL_REGEX, text)
    if r:
        logging.debug('URL found: %s', r.group(0))
        return r.group(0)
    else:
        logging.debug('URL not found')


class HexChatNotificationService(dbus.service.Object):
    def __init__(self):
        DBusGMainLoop(set_as_default=True)
        self.loop = GLib.MainLoop()

        bus_name = dbus.service.BusName(name='com.skontar.HexChat', bus=dbus.SessionBus())
        super().__init__(conn=None, object_path='/com/skontar/HexChat', bus_name=bus_name)

        Notify.init('Hexchat notification server')
        self.notifications = []

    def run(self):
        logging.info('HexChat notification server starting ==============================')
        self.loop.run()

    @dbus.service.method(dbus_interface='com.skontar.HexChat',
                         in_signature='ssssss', out_signature='')
    def create_notification(self, nickname, network, channel, title, text, message_type):
        logging.info('New notification [%s | %s | %s]', network, channel, repr(str(nickname)))
        logging.debug('Message: "%s"', text)
        url = find_url(text)
        notification = Notify.Notification.new(title, text, HEXCHAT_ICON)
        notification.add_action('clicked_dismiss', 'Dismiss all', self.on_dismiss)
        if url:
            notification.add_action('clicked_follow', 'Follow link', self.on_follow, url)
        notification.add_action('clicked_show', 'Show me', self.on_show,
                                (nickname, network, channel, message_type))
        notification.show()

        self.notifications.append(notification)
        if len(self.notifications) > 10:
            del self.notifications[0]
        logging.debug('Notification list: %d', len(self.notifications))

    @dbus.service.method(dbus_interface='com.skontar.HexChat', in_signature='', out_signature='')
    def quit(self):
        logging.info('Quit')
        self.loop.quit()

    def on_dismiss(self, notification, action_name):
        logging.info('Action: dismiss')
        for notification in self.notifications:
            notification.close()
        self.notifications.clear()
        logging.debug('Notification list: %d', len(self.notifications))

        session_bus = dbus.SessionBus()
        dbus_object = session_bus.get_object(bus_name='org.hexchat.service',
                                             object_path='/org/hexchat/Remote')
        interface = dbus.Interface(object=dbus_object, dbus_interface='org.hexchat.plugin')
        logging.debug('Reset icon')
        interface.Command('TRAY -f {}'.format(HEXCHAT_ICON))

    def on_follow(self, notification, action_name, data):
        logging.info('Action: follow | %s', data)
        url = data
        webbrowser.open_new_tab(url)

    def on_show(self, notification, action_name, data):
        logging.info('Action: show | %s', [str(a) for a in data])
        nickname, network, channel, message_type = data

        logging.debug('Activate HexChat application')
        subprocess.call(ACTIVATE_HEXCHAT_COMMAND, shell=True)

        session_bus = dbus.SessionBus()
        dbus_object = session_bus.get_object(bus_name='org.hexchat.service',
                                             object_path='/org/hexchat/Remote')
        interface = dbus.Interface(object=dbus_object, dbus_interface='org.hexchat.plugin')
        context = interface.FindContext(network, channel)
        interface.SetContext(context)
        if message_type == 'HLT':
            logging.debug('Move to channel: %s', channel)
            interface.Command('join {}'.format(channel))
        else:
            logging.debug('Move to private: %s', nickname)
            interface.Command('query {}'.format(nickname))


HexChatNotificationService().run()
logging.info('HexChat notification server ending')

