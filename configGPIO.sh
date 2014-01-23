#!/bin/sh
for PIN in 32 33 34 35 36 37 38 39 57
do
    echo $PIN > sys/class/gpio/export
    echou out > sys/class/gpio/gpio$PIN/direction
done
