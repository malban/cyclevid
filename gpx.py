import gpxpy
import gpxpy.gpx
import math

gpx_file = open( '/home/pi/DE_Stormarn-1.gpx', 'r' )

gpx = gpxpy.parse(gpx_file)

first_stamp = None
last_point = None

stamps = []
speeds = []

resampled_speeds = []

for track in gpx.tracks:
    for segment in track.segments:
        print "raw points: %d" % (len(segment.points))
        segment.reduce_points(10.0)
        print "reduced points: %d" % (len(segment.points))
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
print "total duration: %d seconds" % (total_duration)

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
