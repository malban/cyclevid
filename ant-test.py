import sys
import time
from ant.core import driver, node, event, message, log
from ant.core.constants import CHANNEL_TYPE_TWOWAY_RECEIVE, TIMEOUT_NEVER

def toInt(raw):
    value = ord(raw[1]) << 8
    value += ord(raw[0])
    return value / 1024

class AntSpeedSensor(event.EventCallback):
    def __init__(self, serial, netkey):
        self.serial = serial
        self.netkey = netkey
        self.antnode = None
        self.channel = None

    def start(self):
        print("starting node")
        self._start_antnode()
        print("setup channel")
        self._setup_channel()
        print("register callback")
        self.channel.registerCallback(self)
        print("start listening for events")
        # TODO The start function hangs after killing the script and restarting.
        #      It works again only after removing the Ant+ stick and re-inserting.
        #      Find correct way to disconnect/reconnect from device.

    def stop(self):
        if self.channel:
            self.channel.close()
            self.channel.unassign()
        if self.antnode:
            self.antnode.stop()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.stop()

    def _start_antnode(self):
        stick = driver.USB2Driver(self.serial)
        self.antnode = node.Node(stick)
        self.antnode.start()

    def _setup_channel(self):
        key = node.NetworkKey('N:ANT+', self.netkey)
        self.antnode.setNetworkKey(0, key)
        self.channel = self.antnode.getFreeChannel()
        self.channel.name = 'C:pi-cyclevid'
        self.channel.assign('N:ANT+', CHANNEL_TYPE_TWOWAY_RECEIVE)
        self.channel.setID(121, 0, 0)  # "Bike Speed and Cadence Sensors"
        # TODO: Will 123: bike speed sensor also work if it is a combined sensor?
        # TODO: Is there a way to auto detect and select the correct one?
        self.channel.setSearchTimeout(TIMEOUT_NEVER)
        self.channel.setPeriod(8070)
        self.channel.setFrequency(57)
        self.channel.open()

    def process(self, msg):
        if isinstance(msg, message.ChannelBroadcastDataMessage):
            print msg.payload
            print 'cadence (ms): %d' % (toInt(msg.payload[0:2]))
            print 'cadence (rev): %d' % (toInt(msg.payload[2:4]))
            print 'speed (ms): %d' % (toInt(msg.payload[4:6]))
            print 'speed (rev): %d' % (toInt(msg.payload[6:8]))

SERIAL = '/dev/ant'
NETKEY = 'B9A521FBBD72C345'.decode('hex') # TODO: What is this?

with AntSpeedSensor(serial=SERIAL, netkey=NETKEY) as ant_sensor:
    ant_sensor.start()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)
