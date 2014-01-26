#!/bin/sh

PIN=$1

echo "Exporting GPIO $PIN to userland"
echo $PIN > /sys/class/gpio/export
echo "Configuring GPIO $PIN for output"
echo out > /sys/class/gpio/gpio$PIN/direction

for ITER in `seq 1 60`
do
    echo "Seeting GPIO $PIN value to 1"
    echo "1" > /sys/class/gpio/gpio$PIN/value
    sleep 1
    echo "Seeting GPIO $PIN value to 0"
    echo "0" > /sys/class/gpio/gpio$PIN/value
    sleep 1
done
