#!/usr/bin/env python
# vim: set fileencoding=UTF-8 :

# Based on bluezio modification of code for the HMC5888L Magnetometer (Digital Compass), but this is
# for the QMC5883L Magnetometer component. It has the same function but it
# works quite differently!
# This version uses MicroPython for ESP8266

from machine import I2C, Pin
import math
import time
import sys

class qmc5883l:
    REG_MODE = 0x09
    REG_SET_RESET = 0x0b
    REG_STATUS = 0x06

    def __init__(self, i2c=None, scl=None, sda=None, port=1, address=0x0d):
        if i2c is not None:
            self.bus = i2c
        else:
            self.bus = I2C(-1, Pin(scl), Pin(sda))
        self.address = address
        self.bus.writeto_mem(self.address, self.REG_SET_RESET, bytes([0x01])) # turn on

        # 09H OSR[1:0] RNG[1:0] ODR[1:0] MODE[1:0]
        # Value 00      01         10      11
        # OSR   512     256        128     64
        # RNG   2G      8G         Reserve Reserve
        # ODR   10Hz    50Hz       100Hz   200Hz
        # Mode  Standby Continuous Reserve Reserve
        self.bus.writeto_mem(self.address, self.REG_MODE, bytes([0b00001101])) # OSR=512, RNG=2G, ODR=200Hz, Mode=Continuous


    def twos_complement(self, val, len):
        # Convert twos complement to integer
        if (val & (1 << len - 1)):
            val = val - (1<<len)
        return val

    def __convert(self, data, offset):
        return self.twos_complement(data[offset+1] << 8 | data[offset], 16)

    def isReady(self):
        return (self.bus.readfrom_mem(self.address,  self.REG_STATUS, 1)[0] & 1) > 0

    def axes(self):
        data = self.bus.readfrom_mem(self.address,  0x00, 6)
        x = self.__convert(data, 0)
        y = self.__convert(data, 2)
        z = self.__convert(data, 4)
        return (x,y,z)

    def __str__(self):
        (x, y, z) = self.axes()
        return "Axis X: {0:6d}\nAxis Y: {1:6d}\nAxis Z: {2:6d}".format(x, y, z)


class calibrator:
    """
    On-the-fly calibration and readjustment for a magnetometer sensor.
    
    Uses the calibration approach discussed in
    https://github.com/kriswiner/MPU6050/wiki/Simple-and-Effective-Magnetometer-Calibration
    """

    def __init__(self, declination):
        self.allMin = None
        self.allMax = None
        declDeg, declMin = declination
        self.declinationRad = (declDeg + declMin/60.) * math.pi / 180

    def add_sample(self, axes):
        self.allMin = axes if self.allMin is None else [min(val, existing) for val, existing in zip(axes, self.allMin)]
        self.allMax = axes if self.allMax is None else [max(val, existing) for val, existing in zip(axes, self.allMax)]
        self.bias   = [(a+b)/2 for a, b in zip(self.allMin, self.allMax)]

        scales = [(b-a)/2 for a, b in zip(self.allMin, self.allMax)]
        # avoid division by zero
        if all(x != 0 for x in scales):
            avgScale = float(sum(scales))/len(scales)
            self.factors = [avgScale/x for x in scales]
        else:
            self.factors = [1,] * len(axes)

    def adjust(self, axes):
        """Returns an adjusted reading for the axes, based on previous readings."""
        return [(val - bias) * factor for val, bias, factor in zip(axes, self.bias, self.factors)]
        #return [(val - bias) for val, bias, factor in zip(axes, self.bias, self.factors)]

    def rad2deg(self, headingRad):
        """Converts the radians-based angle to degrees.

        The angle should normally be obtained through atan(y, x) if the sensor
        is horizontal, or atan(x, z) if the sensor is standing."""
        headingRad += self.declinationRad

        # Correct for reversed heading
        if headingRad < 0:
            headingRad += 2 * math.pi

        # Check for wrap and compensate
        elif headingRad > 2 * math.pi:
            headingRad -= 2 * math.pi

        # Convert to degrees from radians
        headingDeg = headingRad * 180 / math.pi
        return headingDeg

    def heading_h(self, axes):
        x, y, z = self.adjust(axes)
        return self.rad2deg(math.atan2(y, x))

    def heading_v(self, axes):
        x, y, z = self.adjust(axes)
        return self.rad2deg(math.atan2(x, z))


if __name__ == "__main__":
    # http://magnetic-declination.com/Great%20Britain%20(UK)/Harrogate#
    compass = qmc5883l()
    cal = calibrator(declination=(-1, 14))
    while True:
        sys.stdout.flush()
        if compass.isReady():
            axes = compass.axes()
            cal.add_sample(axes)
            print "heading = {}".format(cal.heading_v(axes))
        time.sleep(0.5)

