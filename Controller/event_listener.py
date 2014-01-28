#!/usr/bin/python
import sys


def main():
    event = sys.argv[1]
    eventFifo = open("/home/ubuntu/.config/pandorabox/events", "w", 1)
    eventFifo.write(event + "\n")
    for line in sys.stdin.readlines():
        print  ">>> ", line
        eventFifo.write(line)


if __name__ == '__main__':
        main()

