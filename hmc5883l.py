#!/usr/bin/env python
# vim: set fileencoding=UTF-8 :

# HMC5888L Magnetometer (Digital Compass) wrapper class
# Based on https://bitbucket.org/thinkbowl/i2clibraries/src/14683feb0f96,
# but uses smbus rather than quick2wire and sets some different init
# params.

from machine import I2C, Pin
import math
import time
import sys

class hmc5883l:

    __scales = {
        0.88: [0, 0.73],
        1.30: [1, 0.92],
        1.90: [2, 1.22],
        2.50: [3, 1.52],
        4.00: [4, 2.27],
        4.70: [5, 2.56],
        5.60: [6, 3.03],
        8.10: [7, 4.35],
    }

    def __init__(self, i2c=None, scl=None, sda=None, address=0x1e, gauss=1.3):
        if i2c is not None:
            self.bus = i2c
        else:
            self.bus = I2C(-1, Pin(scl), Pin(sda))
        self.address = address

        (reg, self.__scale) = self.__scales[gauss]
        # 8 Average, 15 Hz, normal measurement
        # Scale
        # Continuous measurement
        i2c.writeto_mem(self.address, 0x00, bytes([0x70, reg << 5, 0x00]))

    def twos_complement(self, val, len):
        # Convert twos compliment to integer
        if (val & (1 << len - 1)):
            val = val - (1<<len)
        return val

    def __convert(self, data, offset):
        val = self.twos_complement(data[offset] << 8 | data[offset+1], 16)
        if val == -4096: return None
        return round(val * self.__scale, 4)

    def axes(self):
        data = self.bus.readfrom_mem(self.address,  0x03, 6)
        x = self.__convert(data, 0)
        y = self.__convert(data, 4)
        z = self.__convert(data, 2)
        return (x,y,z)


from qmc5883l import calibrator

if __name__ == "__main__":
    # http://magnetic-declination.com/Great%20Britain%20(UK)/Harrogate#
    compass = hmc5883l(gauss = 4.7)
    cal = calibrator(declination=(-1,13))
    while True:
        axes = compass.axes()
        cal.add_sample(axes)
        sys.stdout.write("\rHeading: {}".format(cal.heading_h(axes)))
        sys.stdout.flush()
        time.sleep(0.5)

