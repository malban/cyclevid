#!/usr/bin/python
# coding: utf-8
import argparse
import fcntl
import os
import signal
import subprocess
import sys

from flask import Flask
from flask import render_template

app = Flask(__name__)

videos = []
subproc = None
playing_video_file = None
script_path = os.path.dirname(os.path.realpath(sys.argv[0]))


def update_status():
    global subproc
    if subproc is not None:
        try:
            data_str = subproc.stdout.readline()
            if data_str.startswith("data,"):
                data_values = data_str.split(',')
                if len(data_values) == 10:
                    speed = float(data_values[5])
                    distance = float(data_values[9])
                    print data_values
        except:
            pass
            
        threading.Timer(1, update_status).start()
        
@app.route('/')
def entry_point():
    if subproc is not None:
        return render_template('playback_controls.html', video_file=playing_video_file)
    else:
        return render_template('video_selection.html', videos=videos)

@app.route('/playback_controls/<video_file>')
def playback_controls(video_file):
    global playing_video_file
    if subproc is not None:
        return render_template('playback_controls.html', video_file=playing_video_file)
    else:
        return render_template('playback_controls.html', video_file=video_file)

@app.route('/play/<video_file>')
def play(video_file):
    global playing_video_file
    global subproc
    if subproc is not None:
        return render_template('playback_controls.html', video_file=playing_video_file)
    else:
        # TODO start playback
        playing_video_file = video_file
        video_path=None
        for filepath, filename in videos:
            if filename == video_file:
                video_path = filepath
                
        if video_path is not None:
            cmd = 'python %s/pi-cyclevid.py %s' % (script_path, video_path)
            print cmd
            subproc = subprocess.Popen(['python', script_path + '/pi-cyclevid.py', video_path], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            
            # Make stdout non-blocking.
            fd = subproc.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            
            threading.Timer(1, update_status).start()
        else:
            print "failed to run video: %s" % (video_file)
        
        return render_template('playback_controls.html', video_file=video_file)

@app.route('/stop')
def stop():
    global subproc
    if subproc is not None:
        subproc.send_signal(signal.SIGINT)
        subproc = None
        playing_video_file = None
    return render_template('video_selection.html', videos=videos)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    
    parser.add_argument('--directory', 
        type=str,
        help='Video directory', 
        default="/home/pi/.pi-cyclevid/videos")
    
    args = parser.parse_args()

    extensions = {'.mp4', '.avi', '.mkv', '.webm', '.mpg'}
    for filename in os.listdir(args.directory):
        for extension in extensions:
            if filename.lower().endswith(extension):
                filepath = os.path.join(args.directory, filename)
                thumbnail_path = 'static/' + filename + '.jpg'
                videos.append([filepath, filename])
                if not os.path.isfile(thumbnail_path):
                    print "getting thumbnail for %s" % (filepath)
                    cmd = 'ffmpeg -ss 00:05:00 -i %s -vframes 1 -v:q 5 %s' % (filepath, thumbnail_path)
                    print cmd
                    proc = subprocess.Popen([cmd], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
                    output = proc.stdout.read()
                    print output

    print videos
    app.run(debug=True, host='0.0.0.0', port=8080)
