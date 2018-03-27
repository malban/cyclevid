#!/usr/bin/python
# coding: utf-8
import argparse
import os
import subprocess

from flask import Flask
from flask import render_template

app = Flask(__name__)

videos = []

@app.route('/')
def entry_point():
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
                    subprocess.call(['ffmpeg', '-ss', '00:05:00', '-i', filepath, '-vframes', '1', '-v:q', '5', thumbnail_path], stdin=None, stdout=None, stderr=None, shell=False)

    print videos
    app.run(debug=True)
