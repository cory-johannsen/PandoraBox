#!/bin/sh
# LCD
for PIN in 30 60 31 40 48 51 4 5 125 122
do
    echo "Exporting GPIO $PIN for output"
    echo $PIN > /sys/class/gpio/export
    echo out > /sys/class/gpio/gpio$PIN/direction
done
# Pushbuttons
for PIN in 3 2 49 15 117 14 125 122 41 42
do
    echo "Exporting GPIO $PIN for input"
    echo $PIN > /sys/class/gpio/export
    echo in > /sys/class/gpio/gpio$PIN/direction
done
