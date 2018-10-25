# Dlscan

## Overview
Scans files from device "Dell S2825cdn". Provides simple GUI and command line interfaces.
```
$ dlscan --help
Scan document from Dell S2825cdn device.
Usage: dlscan [--gui] [file] [--greyscale] [-gs] [FILE]
Filenames cannot start with '-'.

```

## Requirements
NumPy: <https://www.numpy.org/>  
PyUSB: <https://pyusb.github.io/pyusb/>  

Only if `--gui` is used:  
PyQt5: <https://www.riverbankcomputing.com/software/pyqt/>

All dependencies are available through pip.

## Installation:
```
$ sudo cp dlscan.py /usr/bin/dlscan
$ sudo chmod +x /usr/bin/dlscan
```
