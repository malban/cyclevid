# pi-cyclevid

A very simple Python script for playing back RLV style videos on a Raspberry Pi based on ANT+ feedback.

This script depends on [python-ant](https://github.com/baderj/python-ant), [python-omxplayer-wrapper](https://github.com/willprice/python-omxplayer-wrapper), and [gpxpy](https://github.com/tkrajina/gpxpy).

## Instructions

```
~ $ sudo apt-get install -y python-setuptools python-dbus python-pathlib python-virtualenv
~ $ git clone https://github.com/malban/pi-cyclevid.git
~ $ cd pi-cyclevid 
~/pi-cyclevid $ virtualenv --system-site-packages env
~/pi-cyclevid $ source env/bin/activate
~/pi-cyclevid $ pip install -I -e git+https://github.com/baderj/python-ant.git@develop#egg=ant
~/pi-cyclevid $ pip install omxplayer-wrapper gpxpy
~/pi-cyclevid $ sudo cp ant2.rules /etc/udev/rules.d/
```

## Links
* https://www.johannesbader.ch/2014/06/track-your-heartrate-on-raspberry-pi-with-ant/
* http://www.trackprofiler.com/gpxpy/index.html
* https://github.com/tkrajina/srtm.py
* http://cycleseven.org/effect-of-hills-on-cycling-effort
* http://www.sportsci.org/jour/9804/dps.html
* https://github.com/davidzof/wattzap-ce
