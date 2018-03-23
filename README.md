# pi-cyclevid

A very simple Python script for playing back RLV style videos on a Raspberry Pi based on ANT+ feedback.

This script depends on [python-ant](https://github.com/baderj/python-ant), [python-omxplayer-wrapper](https://github.com/willprice/python-omxplayer-wrapper), and [gpxpy](https://github.com/tkrajina/gpxpy).

## Instructions

```
~ $ sudo apt-get install -y python-setuptools libdbus-1-dev libdbus-glib-1-dev
~ $ sudo pip install virtualenv
~ $ git clone https://github.com/malban/pi-cyclevid.git
~ $ cd pi-cyclevid 
~/pi-cyclevid $ virtualenv --system-site-packages env
~/pi-cyclevid $ source env/bin/activate
~/pi-cyclevid $ pip install -e git+https://github.com/baderj/python-ant.git#egg=ant
~/pi-cyclevid $ pip install omxplayer-wrapper gpxpy
~/pi-cyclevid $ sudo cp ant2.rules /etc/udev/rules.d/
```

## Links
* https://www.johannesbader.ch/2014/06/track-your-heartrate-on-raspberry-pi-with-ant/
* http://www.trackprofiler.com/gpxpy/index.html
* https://github.com/tkrajina/srtm.py
