

from omxplayer.player import OMXPlayer
from pathlib import Path
from time import sleep
import dbus.types

VIDEO_PATH = Path("/home/pi/DE_Stormarn-1.avi")

player = OMXPlayer(VIDEO_PATH)

sleep(5)

print "min rate"
print player._player_interface_property('MinimumRate')
print "max rate"
print player._player_interface_property('MaximumRate')
print "rate"
print player._player_interface_property('Rate')
print "setting rate to 0.2"
print player._player_interface_property('Rate', dbus.Double(0.2))
sleep(5)
print "setting rate to 1.5"
print player._player_interface_property('Rate', dbus.Double(1.5))
sleep(5)

player.quit()
