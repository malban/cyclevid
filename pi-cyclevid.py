import argparse
import dbus.types
import gpxpy
import gpxpy.gpx
import math
import ntpath
import os.path
import signal
import sys
import time
from ant.core import driver, node, event, message, log
from ant.core.constants import CHANNEL_TYPE_TWOWAY_RECEIVE, TIMEOUT_NEVER
from omxplayer.player import OMXPlayer
from pathlib import Path
from time import sleep

player = None

def signal_handler(signal, frame):
    try:
        player.quit()
    except:
        pass
        
def main():
    global player

    parser = argparse.ArgumentParser()
    parser.add_argument('--start-position', type=float,
                    help='start position in seconds')
    parser.add_argument('--speed-scale', type=float,
                    help='speed scale factor', default=1.0)
    parser.add_argument('--video-speed', type=float,
                    help='default video speed in m/s', default=10.0)
    parser.add_argument('--weight', type=float,
                    help='weight of the cyclist and bike in kg', default=75.0)
    parser.add_argument('--use-gradient', action='store_true',
                    help='adjust speed based on road gradient.')
    parser.add_argument('video',  metavar='VIDEO_FILE', type=str,
                    help='video file path')
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)

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
    
    # TODO load GPX data if it exists
    
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

    player.play()
    player.set_position(start_position)
    while True:
        try:
            position = player.position()
        except:
            break
            
        # TODO get GPX speed if it exists
        # TODO get ANT+ speed
        # TODO calculate adjusted cycle speed
        # TODO calculate playback speed
        # TODO store position
        print "%f of %f" % (position, duration)
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

if __name__ == "__main__":
    main()

