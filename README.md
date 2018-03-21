# pi-cyclevid

A very simple Python script for playing back RLV style videos on a Raspberry Pi based on ANT+ feedback.

This script depends on [python-ant](https://github.com/baderj/python-ant) and [python-omxplayer-wrapper](https://github.com/willprice/python-omxplayer-wrapper).

```
$ sudo cp ant2.rules /etc/udev/rules.d/
$ sudo apt-get install -y python-setuptools
$ git clone https://github.com/baderj/python-ant.git
$ git clone https://github.com/willprice/python-omxplayer-wrapper.git
```

## Links
* https://www.johannesbader.ch/2014/06/track-your-heartrate-on-raspberry-pi-with-ant/
