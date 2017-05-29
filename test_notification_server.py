import dbus

session_bus = dbus.SessionBus()
dbus_object = session_bus.get_object(bus_name='com.skontar.HexChat', object_path='/com/skontar/HexChat')
interface = dbus.Interface(object=dbus_object, dbus_interface='com.skontar.HexChat')
interface.create_notification('fenikso', 'freenode', '#fedora', 'Title',
                              '<fenikso>: Velmi žluťoučký kůň www.example.com', 'P')


# interface.quit()
