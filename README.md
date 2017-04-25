Holter Monitor
==============

Aiden Harwood (ath23), David Zhou (dz54), Gautam Chebrolu (gsc13), Katie Gelman (krg17), and Paige Belliveau (pmb28)

BME 464L: Medical Instrument Design

## Instructions:

+ to upload data into the database: ```python holter_monitor.py --upload``` followed by the name of a data file located in the ```data/``` directory.

+ to run the server on a configured Duke VM: ```bokeh serve holter_monitor.py --port 5100 --allow-websocket-origin=152.3.52.29```.

+ to kill the server: ```fuser -k 5100/tcp```.

+ our server is located at ```colab-sbx-276.oit.duke.edu```.

## Known Issues:

+ please pan / zoom in on the plot before using the selectors on the left.  The reason for this is an open issue with the (Bokeh package)[https://github.com/bokeh/bokeh/issues/4014] that prevents the axis ranges from being properly updated.