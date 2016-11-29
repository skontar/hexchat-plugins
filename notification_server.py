import logging
import re
import subprocess
import textwrap
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

HEXCHAT_ICON = '/usr/share/icons/hicolor/scalable/apps/hexchat.svg'
ACTIVATE_HEXCHAT_COMMAND = 'move-to-desktop-and-activate 4'
# http://daringfireball.net/2010/07/improved_regex_for_matching_urls
URL_PATTERN = r'''(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))'''


class ComplexNotification:
    """
    Class for holding an extension of `Notify.Notification` and managing list of active
    notifications.
    """
    active_notifications = []

    def __init__(self, nickname, network, channel, title, text, message_type):
        """
        This should not be called directly, use `create` class method instead to create references
        to all active notifications.
        """
        self.nickname = nickname
        self.network = network
        self.channel = channel
        self.title = title
        self.text = text
        self.message_type = message_type

        self.url = self.find_url()
        if self.url:
            self.text = self.text.replace(self.url, '<u>' + self.url + '</u>')
        self.wrapped_text = textwrap.fill(self.text, 60)

        self.notification = Notify.Notification.new(self.title, self.wrapped_text, HEXCHAT_ICON)
        self.notification.add_action('clicked_dismiss', 'Dismiss all', self.on_dismiss)
        if self.url:
            self.notification.add_action('clicked_follow', 'Follow link', self.on_follow)
        self.notification.add_action('clicked_show', 'Show me', self.on_show)
        self.notification.show()

    @classmethod
    def create(cls, nickname, network, channel, title, text, message_type):
        """
        Create a new notification and handle notification reference list needed for
        `Notify.Notification` to be able to call callbacks.
        """
        logging.info('Creating ComplexNotification object')
        notification = cls(nickname, network, channel, title, text, message_type)
        cls.active_notifications.append(notification)
        if len(cls.active_notifications) > 10:
            del cls.active_notifications[0]
        logging.debug('Notification list: %d', len(cls.active_notifications))

    @staticmethod
    def get_hexchat_interface():
        """
        Function to connect to HexChat DBus interface.

        Returns:
            dbus.proxies.Interface: HexChat DBus interface object
        """
        session_bus = dbus.SessionBus()
        dbus_object = session_bus.get_object(bus_name='org.hexchat.service',
                                             object_path='/org/hexchat/Remote')
        interface = dbus.Interface(object=dbus_object, dbus_interface='org.hexchat.plugin')
        return interface

    def find_url(self):
        """
        Returns first found URL in the text.
        """
        logging.debug('Looking for URL')
        r = re.search(URL_PATTERN, self.text)
        if r:
            logging.debug('URL found: %s', r.group(0))
            return r.group(0)
        else:
            logging.debug('URL not found')

    def activate_hexchat(self):
        """
        Activate HexChat application and move to correct tab.
        """
        logging.debug('Activate HexChat application')
        subprocess.call(ACTIVATE_HEXCHAT_COMMAND, shell=True)

        interface = self.get_hexchat_interface()
        context = interface.FindContext(self.network, self.channel)
        interface.SetContext(context)
        if self.message_type == 'HLT':
            logging.debug('Move to channel: %s', self.channel)
            interface.Command('join {}'.format(self.channel))
        else:
            logging.debug('Move to private: %s', self.nickname)
            interface.Command('query {}'.format(self.nickname))

    def on_dismiss(self, notification, action_name):
        logging.info('Action: dismiss')
        for complex_notification in self.active_notifications:
            complex_notification.notification.close()
        self.active_notifications.clear()
        logging.debug('Notification list: %d', len(self.active_notifications))

        interface = self.get_hexchat_interface()
        logging.debug('Reset icon')
        interface.Command('TRAY -f {}'.format(HEXCHAT_ICON))

    def on_follow(self, notification, action_name):
        logging.info('Action: follow | %s | => also show', self.url)
        self.on_show(None, None)
        logging.debug('Opening URL in web browser | %s', self.url)
        webbrowser.open_new_tab(self.url)

    def on_show(self, notification, action_name):
        logging.info('Action: show | %s', [self.nickname, self.network, self.channel,
                                           self.message_type])
        self.activate_hexchat()


class HexChatNotificationService(dbus.service.Object):
    def __init__(self):
        DBusGMainLoop(set_as_default=True)
        self.loop = GLib.MainLoop()
        bus_name = dbus.service.BusName(name='com.skontar.HexChat', bus=dbus.SessionBus())
        super().__init__(conn=None, object_path='/com/skontar/HexChat', bus_name=bus_name)

        Notify.init('Hexchat notification server')

    def run(self):
        logging.info('HexChat notification server starting ==============================')
        self.loop.run()

    @dbus.service.method(dbus_interface='com.skontar.HexChat',
                         in_signature='ssssss', out_signature='')
    def create_notification(self, nickname, network, channel, title, text, message_type):
        logging.info('New notification [%s | %s | %s]', network, channel, repr(str(nickname)))
        logging.debug('Message: %s', repr(str(text)))
        ComplexNotification.create(str(nickname), str(network), str(channel), str(title),
                                   str(text), str(message_type))

    @dbus.service.method(dbus_interface='com.skontar.HexChat', in_signature='', out_signature='')
    def quit(self):
        logging.info('Quit')
        self.loop.quit()


HexChatNotificationService().run()
logging.info('HexChat notification server ending')
