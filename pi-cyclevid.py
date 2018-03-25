import argparse
import dbus.types
import fcntl
import gpxpy
import gpxpy.gpx
import math
import ntpath
import os.path
import signal
import sys
import threading
import time
from ant.core import driver, node, event, message, log
from ant.core.constants import CHANNEL_TYPE_TWOWAY_RECEIVE, TIMEOUT_NEVER
from omxplayer.player import OMXPlayer
from pathlib import Path
from time import sleep

player = None
ant_sensor = None

def signal_handler(signal, frame):
    try:
        print "\nstopping omxplayer ..."
        player.quit()
    except:
        pass

    try:
        print "stopping ANT+ device ..."
        ant_sensor.stop()
    except:
        pass

    print "done"
    sys.exit(0)

def extract_gpx_speed(gpx):
    stamps = []
    speeds = []
    for track in gpx.tracks:
        for segment in track.segments:
            print "gpx raw points: %d" % (len(segment.points))
            segment.reduce_points(10.0)
            print "gpx reduced points: %d" % (len(segment.points))
            num_points = len(segment.points)
            for index, point in enumerate(segment.points):
                if index == 0:
                    first_stamp = point.time
                    last_point = point
                elif index + 1 < num_points:
                   speed = segment.points[index -1].speed_between(segment.points[index + 1])
                   stamp = (point.time - first_stamp).total_seconds()
                   if stamp > 0 and (len(stamps) == 0 or stamp > stamps[-1]):
                       stamps.append(stamp)
                       speeds.append(speed)
                   else:
                       print "  dropping out of order data."


    total_duration = int(math.ceil(stamps[-1]))
    print "gpx total duration: %d seconds" % (total_duration)

    speed_table = (total_duration + 1) * [None]
    for index, (speed, stamp) in enumerate(zip(speeds, stamps)):
        if index == 0:
            for i in range(0, int(stamp) + 1):
                speed_table[i] = speed
        else:
            prev_speed = speeds[index - 1]
            prev_stamp = stamps[index - 1]
            elapsed = stamp - prev_stamp
            for i in range(int(math.ceil(prev_stamp)), int(stamp) + 1):
                w1 = (stamp - i) / elapsed
                w2 = (i - prev_stamp) / elapsed
                speed_table[i] = w1 * prev_speed + w2 * speed

    return speed_table

class AntSpeedCadenceSensor(event.EventCallback):
    def __init__(self, serial, netkey):
        self.device = None
        self.serial = serial
        self.netkey = netkey
        self.antnode = None
        self.channel = None

        self.last_wheel_stamp = 0
        self.last_pedal_stamp = 0
        self.last_wheel_count = 0
        self.last_pedal_count = 0
        self.last_valid_wheel_stamp = 0
        self.last_valid_pedal_stamp = 0
        self.last_wheel_time = None
        self.last_pedal_time = None

        self.wheel_rpm_ant = 0
        self.pedal_rpm_ant = 0
        self.wheel_rpm_sys = 0
        self.pedal_rpm_sys = 0

        self.wheel_stopped_count = 0

        self.mutex = threading.Lock()

    def getWheelRpmAnt(self):
        self.mutex.acquire()
        rpm = self.wheel_rpm_ant
        self.mutex.release()
        return rpm

    def getWheelRpmSys(self):
        self.mutex.acquire()
        rpm = self.wheel_rpm_sys
        self.mutex.release()
        return rpm

    def toInt(self, raw):
        print raw
        value = ord(raw[1]) << 8
        value += ord(raw[0])
        print value
        return value / 1024

    def start(self):
        print "ANT+ resetting usb device ..."
        fd = os.open(self.serial, os.O_WRONLY)
        if fd < 0: sys.exit(1)
        USBDEVFS_RESET = ord('U') << (4*2) | 20
        fcntl.ioctl(fd, USBDEVFS_RESET, 0)
        os.close(fd)

        print("ANT+ starting node")

        self.device = driver.USB2Driver(self.serial)
        self.antnode = node.Node(self.device)
        self.antnode.start()
        print("ANT+ setup channel")
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

        self.channel.registerCallback(self)
        print("ANT+ start listening for events")

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

    def process(self, msg):
        if isinstance(msg, message.ChannelBroadcastDataMessage):
            print msg.payload
            pedal_stamp = self.toInt(msg.payload[0:2])
            pedal_count = self.toInt(msg.payload[2:4])
            wheel_stamp = self.toInt(msg.payload[4:6])
            wheel_count = self.toInt(msg.payload[6:8])
            print "Data: %d %d %d %d" % (pedal_stamp, pedal_count, wheel_stamp, wheel_count)
            if self.last_wheel_time is None or self.last_pedal_time is None:
                print "ANT+ initializing values..."
                self.last_wheel_stamp = wheel_stamp
                self.last_pedal_stamp = pedal_stamp
                self.last_valid_wheel_stamp = wheel_stamp
                self.last_valid_pedal_stamp = pedal_stamp
                self.last_wheel_count = wheel_count
                self.last_pedal_count = pedal_count
                self.last_wheel_time = time.time()
                self.last_pedal_time = time.time()
                return

            # Get ANT+ wheel stamp delta in milliseconds.
            wheel_stamp_delta = 0
            if wheel_stamp < self.last_wheel_stamp:
                # Wheel stamp rolled over
                wheel_stamp_delta = wheel_stamp + (64 - self.last_wheel_stamp)
            else:
                wheel_stamp_delta = wheel_stamp - self.last_wheel_stamp
            print "wheel stamp delta: %d" % (wheel_stamp_delta)

            # Get ANT+ stamp delta in milliseconds since last valid wheel reading.
            valid_wheel_stamp_delta = 0
            if wheel_stamp < self.last_valid_wheel_stamp:
                # Wheel stamp rolled over
                valid_wheel_stamp_delta = wheel_stamp + (64 - self.last_valid_wheel_stamp)
            else:
                valid_wheel_stamp_delta = wheel_stamp - self.last_valid_wheel_stamp
            print "valid wheel stamp delta: %d" % (valid_wheel_stamp_delta)

            wheel_count_delta = 0
            if wheel_count < self.last_wheel_count:
                # wheel count rolled over
                wheel_count_delta = wheel_count + (64 - self.last_wheel_count)
            else:
                wheel_count_delta = wheel_count - self.last_wheel_count
            print "wheel count delta: %d" % (wheel_count_delta)

            measured_wheel_rpm_sys = None
            measured_wheel_rpm_ant = None
            if wheel_stamp_delta > 0 or True:
                print "A"
                if wheel_count_delta == 0:
                    self.wheel_stopped_count += 1
                    print "B; %d" % (self.wheel_stopped_count)
                    if self.wheel_stopped_count >= 2:
                        print "STOP 1"
                        measured_wheel_rpm_ant = 0
                        measured_wheel_rpm_sys = 0
                else:
                    print "C"
                    self.wheel_stopped_count = 0

                    # Get rpm based on system time
                    current_time = time.time()
                    delta_sys_time = (current_time - self.last_wheel_time) / 60.0
                    measured_wheel_rpm_sys = wheel_count_delta / delta_sys_time
                    self.last_wheel_time = current_time

                    # Get rpm based on ANT+ time
                    delta_ant_time = (valid_wheel_stamp_delta / 1000.0) / 60.0
                    measured_wheel_rpm_ant = wheel_count_delta / delta_ant_time
                    self.last_valid_wheel_stamp = wheel_stamp
            else:
                self.wheel_stopped_count += 1
                print "D: %d" % (self.wheel_stopped_count)
                if self.wheel_stopped_count >= 6:
                    print "STOP 2"
                    measured_wheel_rpm_ant = 0
                    measured_wheel_rpm_sys = 0

            if measured_wheel_rpm_ant is not None:
                print "E"
                self.mutex.acquire()
                self.wheel_rpm_ant = (self.wheel_rpm_ant + measured_wheel_rpm_ant) * 0.5
                self.wheel_rpm_sys = (self.wheel_rpm_sys + measured_wheel_rpm_sys) * 0.5
                self.mutex.release()

            self.last_wheel_stamp = wheel_stamp
            self.last_pedal_stamp = pedal_stamp
            self.last_wheel_count = wheel_count
            self.last_pedal_count = pedal_count

def main():
    global player
    global ant_sensor

    parser = argparse.ArgumentParser()
    parser.add_argument('--device', type=str,
                    help='ANT+ device path', default="/dev/ant")
    parser.add_argument('--start-position', type=float,
                    help='start position in seconds')
    parser.add_argument('--speed-scale', type=float,
                    help='speed scale factor', default=1.0)
    parser.add_argument('--video-speed', type=float,
                    help='default video speed in m/s', default=10.0)
    parser.add_argument('--weight', type=float,
                    help='weight of the cyclist and bike in kg', default=75.0)
    parser.add_argument('--wheel-diameter', type=float,
                    help='wheel diameter in meters', default=0.668)
    parser.add_argument('--use-gradient', action='store_true',
                    help='adjust speed based on road gradient.')
    parser.add_argument('video',  metavar='VIDEO_FILE', type=str,
                    help='video file path')
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)


    # Connect to ANT+ sensor
    ant_sensor = AntSpeedCadenceSensor(serial=args.device, netkey='B9A521FBBD72C345'.decode('hex'))
    ant_sensor.start()

    # Verify video file.
    if not os.path.isfile(args.video):
        print "Invalid video path."
        return
    player = OMXPlayer(args.video)
    try:
        player.pause()
    except:
        print "Invalid video file."
        player.quit()
        return

    gpx_speed = None

    # Load GPX data if it exists
    base_path, video_extenstion = os.path.splitext(args.video)
    try:
        gpx_file = open(base_path + '.gpx', 'r')
        gpx = gpxpy.parse(gpx_file)

        gpx_speed = extract_gpx_speed(gpx)
    except:
        print "Failed to load GPX data."

    # Create save directory if necessary.
    save_dir = os.path.expanduser("~/.pi-cyclevid")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Determine position in the video.
    video_name = ntpath.basename(args.video)
    progress_path = os.path.expanduser(save_dir + "/" + video_name + ".progress");
    start_position = 0.0
    if args.start_position is not None:
        start_position = args.start_position
    else:
        # Check for existing progress file.
        if os.path.isfile(args.video):
            #TODO load position
            pass

    duration = player.duration()
    position = start_position
    last_pos = position

    wheel_speed = 0.0
    playback_rate = 1.0
    paused = False

    player.play()
    player.set_position(start_position)
    while True:
        try:
            position = max(0, player.position())
        except:
            break

        video_speed = args.video_speed
        # Get GPX speed if it exists
        if gpx_speed is not None:
            index = min(int(position), len(gpx_speed) - 1)
            if index + 2 < len(gpx_speed):
               dt = position - index
               video_speed = gpx_speed[index] *  (1.0 - dt) + gpx_speed[index + 1] * dt
            else:
               video_speed = gpx_speed[index]

        # Get ANT+ speed
        wheel_rpm_ant = ant_sensor.getWheelRpmAnt()
        wheel_rpm_sys = ant_sensor.getWheelRpmSys()
        wheel_speed_ant = wheel_rpm_ant * args.wheel_diameter * math.pi / 60.0
        wheel_speed = args.speed_scale * wheel_rpm_sys * args.wheel_diameter * math.pi / 60.0

        if args.use_gradient and gpx_speed is not None:
            # TODO calculate adjusted cycle speed
            # TODO calculate playback speed
            pass
        else:
            # Calculate playback speed based only on wheel speed and video speed.
            playback_rate = wheel_speed / video_speed

        # TODO store position
        print "%f of %f (video speed: %f, wheel speed: %f (%f), playback rate: %f (%f)" % (position, duration, video_speed, wheel_speed, wheel_rpm_sys, playback_rate, (position - last_pos) / 0.25)

        if playback_rate < 0.05:
            player.pause()
            paused = True
        else:
            player._player_interface_property('Rate', dbus.Double(playback_rate))
            if paused:
                player.play()
                paused = False

        last_pos = position
        sleep(0.25)

    # Check if the video is finished.
    if duration - position < 5:
        # TODO clear progress file
        print "finished"
    print "exiting"

    try:
        player.quit()
    except:
        pass

    try:
        ant_sensor.stop()
    except:
        pass

if __name__ == "__main__":
    main()


