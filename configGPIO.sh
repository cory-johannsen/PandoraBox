#!/bin/sh
# LCD
for PIN in 44 26 46 65 45 37 47 27 88 89
do
    echo $PIN > /sys/class/gpio/export
    echo out > /sys/class/gpio/gpio$PIN/direction
done
# Pushbuttons
for PIN in 73 71 72 70 39
do
    echo $PIN > /sys/class/gpio/export
    echo in > /sys/class/gpio/gpio$PIN/direction
done
