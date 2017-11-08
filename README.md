HMC8553L/QMC8553L Magnetometers (I2C digital compasses)
===========================================

Python wrapper classes for the HMC5883L/QMC5883L magnetometers (using smbus I2c). Separates the raw reading of the sensor (classes `hmc5883l` and `qmc5883l`) from its adjustment to a centered/scaled reading, and its conversion to a heading in degrees according to a magnetic declination (class `calibrator`).

References
----------
* http://magnetic-declination.com/Great%20Britain%20(UK)
* https://github.com/kriswiner/MPU6050/wiki/Simple-and-Effective-Magnetometer-Calibration
