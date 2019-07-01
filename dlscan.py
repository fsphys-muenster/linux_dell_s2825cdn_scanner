#!/usr/bin/python3

"""
Dlscan

Copyright (C) 2018, Fachschaftsrat Physik der Universität Münster

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
import usb.core
import usb.util
import numpy as np
import math
import os

from PIL import Image

def read_assert(expected, dev, timeout = None):
    ans = dev.read(0x82, len(bytearray(expected)),timeout)
    if ans != bytearray(expected):
        print("Expected", bytearray(expected).hex(), ", got", bytearray(ans).hex())
        
def to_int(bytearr):
    return int.from_bytes(bytearr, byteorder='big')

def to_byte(value,length=2):
    return value.to_bytes(length,byteorder='big')

def rgbs(l):
    return np.array(list(bytearray(l)))

def scan(greyscale=False):
    # Init device connection
    dev = usb.core.find(idVendor=0x413c, idProduct=0x5910)
    if dev is None:
        raise ValueError('Device not found')
    reattach = False
    if dev.is_kernel_driver_active(1):
        reattach = True
        dev.detach_kernel_driver(1)
    dev.reset()
    dev.set_configuration()

    # Init device connection
    dev.write(0x01,bytearray([0,0x5a,0,0,0,0,0,0x04,0x20,0,0,0]))
    ans = dev.read(0x82,64)

    part = bytearray([0x15, 0x4e, 0xb2, 0xdd, 0x0e, 0xe2, 0x55, 0x56])
    command = bytearray([0x00, 0x16, 0x00, 0x01, 0x00, 0x00, 0x01, 0x10, 0xec, 0xfe, 0x19, \
                     0x99, 0x13, 0x7d, 0xe5, 0xff, 0x0e, 0xff, 0xe2, 0x5f, 0x9c, 0xbb, \
                     0x00, 0x24])\
                 + 2*part + bytearray([0xc6, 0x0b, 0xa0, 0xb9, 0xb7, 0x5a, 0x3a, 0x29, 0x74,\
                                       0xcb, 0x94, 0x00, 0xe4, 0x52, 0x68, 0x4c, 0x0f, 0xd7,\
                                       0x29, 0x90, 0x73, 0x72, 0xf2, 0x00])\
                 + 2*part + bytearray([0x4c, 0x88, 0xea, 0x31, 0xae, 0xf8, 0x12, 0xb1, 0x39,\
                                       0x99, 0x42, 0x28, 0xc0, 0xc1, 0xa3, 0xa8])\
                 + 23*part
    dev.write(0x01,command)

    # Wait until init is ready
    ans2 = dev.read(0x82, 8, timeout=100000)

    current = bytearray([bytearray(ans2)[0]])
    expected = current + bytearray([0x16, 0, 0x01, 0,0,0,0])
    if ans2 != expected:
        print("Expected", expected.hex(), ", got", ans.hex())

    dev.write(0x01, current + bytearray([0x07, 0,0,0,0,0, 0x04, 0,0,0,0]))
    read_assert(current + bytearray([0x07,0,0x01,0,0,0,0]), dev)

    size = 4
    byte_resolution = bytearray(to_byte(300))
    if not greyscale:
        byte_farbe = bytearray(to_byte(0x5,1))
    else:
        byte_farbe = bytearray(to_byte(0x2,1))
    if size == 5: # Din A5
        byte_width = bytearray(to_byte(0x1b50))
        byte_height = bytearray(to_byte(0x26c0))
    else: # Din A4
        height = 3506
        width = 2496
        byte_width = bytearray(to_byte(0x26c0))
        byte_height = bytearray(to_byte(0x36cc))
    byte_realwidth = bytearray(to_byte(math.ceil(to_int(byte_width)/128)*128))
    
    # Here indention could be added
    byte_indention = bytearray(to_byte(0,1))
    
    # Scan command
    dev.write(0x01, current + bytearray([0x24, 0,0,0,0,0, 0x30, 0,0])+2*byte_resolution+bytearray(5)+byte_indention+bytearray(6)\
          +byte_realwidth+bytearray(2)+byte_height+bytearray(2)+byte_farbe+bytearray([0x08,0,0x31])+bytearray(5)\
          +byte_indention+bytearray(6)+byte_width+bytearray(2)+byte_height)
    read_assert(current + bytearray([0x24,0,0x01,0,0,0,0]), dev)

    dev.write(0x01, current + bytearray([0x1b, 0,0,0,0,0,0]))
    read_assert(current + bytearray([0x1b,0,0x01,0,0,0,0]), dev)

    dev.write(0x01, current + bytearray([0xc2, 0,0,0,0,0,0]))
    if greyscale:
        read_assert(current + bytearray([0xc2,0,0x02,0,0,0,0x0c,0x02,0,0,0,\
                                 0x00,0x85,0x91,0x40,\
                                 0x00,0x85,0x91,0x40]),dev, 100000)
    else:
        read_assert(current + bytearray([0xc2,0,0x02,0,0,0,0x0c,0x05,0,0,0,\
                                 0x01,0x90,0xb3,0xc0,\
                                 0x01,0x90,0xb3,0xc0]),dev, 100000)
    
    scan = bytearray()

    if greyscale:
        scanamount = 33
        lastcommand_end = bytearray([0x01,0x91,0x40])
        readlast2 = 101888
        readlast3 = 328
    else:
        scanamount = 100
        lastcommand_end = bytearray([0,0xb3,0xc0])
        readlast2 = 45056
        readlast3 = 456


    for i in range(0,scanamount):
        dev.write(0x01, current + bytearray([0x28, 0,0,0,0,0, 0x04,0,0x04,0,0]))
        part1 = dev.read(0x82,512)
        part2 = dev.read(0x82,261632)
        part3 = dev.read(0x82,8)
        scan += part1[8:]+part2+part3

    dev.write(0x01, current + bytearray([0x28, 0,0,0,0,0, 0x04,0])+lastcommand_end)
    part1 = dev.read(0x82,512)
    part2 = dev.read(0x82,readlast2)
    part3 = dev.read(0x82,readlast3)
    scan += part1[8:]+part2+part3
    
    dev.write(0x01, current + bytearray([0x07, 0,0,0,0,0, 0x04, 0, 0, 0, 0]))
    read_assert(current + bytearray([0x07,0,0x01,0,0,0,0]), dev)
    
    dev.write(0x01, current + bytearray([0x17, 0,0,0,0,0,0]))
    read_assert(current + bytearray([0x17,0,0x01,0,0,0,0]), dev, 100*1000)

    usb.util.dispose_resources(dev)
    if reattach:
        dev.attach_kernel_driver(1)

    colors = rgbs(scan)

    if not greyscale:
        realcolors = np.reshape(colors[0:3*height*width],(height,width,3))
    else:
        realcolors = np.reshape(colors[0:height*width],(height,width))
        
    return realcolors
    
def save_array_as_img(realcolors, name):
    im = Image.fromarray(np.uint8(realcolors))
    if name[-4] == ".":
        im.save(name)
    else:
        im.save(name,"png")

def gui():
    global QtCore, QtWidgets, QtGui, uic, ImageQt
    from PyQt5 import QtCore, QtWidgets, QtGui, uic
    from PIL.ImageQt import ImageQt
    
    class ScanGui(QtWidgets.QMainWindow):
        def __init__(self):
            QtWidgets.QMainWindow.__init__(self)
            
            _uipath1 = os.path.join(os.path.dirname(__file__), 'scan_gui.ui')
            _uipath2 = os.path.join('/usr/share/dlscan', 'scan_gui.ui')
            if os.path.isfile(_uipath1):
                uipath = _uipath1
            elif os.path.isfile(_uipath2):
                uipath = _uipath2
            else:
                return
            
            uic.loadUi(uipath, self)
                
            
            self.preview_view.ui.histogram.hide()
            self.preview_view.ui.roiBtn.hide()
            self.preview_view.ui.menuBtn.hide()
            
            self.settings_scan.clicked.connect(self.buttons_settings_scan)
            self.preview_save.clicked.connect(self.buttons_preview_save)
            
        def buttons_settings_scan(self):
            # Update UI buttons
            self.settings_scan.setEnabled(False)
            QtWidgets.QApplication.processEvents()
            
            greyscale = self.settings_color.currentIndex() == 1
            
            # Scan
            self.realcolors = scan(greyscale)
            
            # Plot
            self.preview_view.ui.histogram.show()
            if greyscale:
                arr = self.realcolors.T
            else:
                arr = self.realcolors.transpose(1,0,2)
            self.preview_view.setImage(arr)
            self.preview_view.ui.histogram.hide()
            
            # Update UI buttons
            self.preview_save.setEnabled(True)
            self.settings_scan.setEnabled(True)
            
        def buttons_preview_save(self):
            dialog = QtWidgets.QFileDialog()
            dialog.setDefaultSuffix('pdf')
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            dialog.setNameFilters(["PDF Files (*.pdf)", "Image Files (*.png *.jpg *.bmp)"])
            if dialog.exec_() != QtGui.QDialog.Accepted:
                return

            selected_files = dialog.selectedFiles()
            if len(selected_files) == 0:
                return

            if os.path.exists(selected_files[0]):
                reply = QtWidgets.QMessageBox.question(self, "Overwriting file", "The selected file already exists. Do you want to overwrite it?",
                                QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No)
            if reply != QtWidgets.QMessageBox.Yes:
                return

            save_array_as_img(self.realcolors, selected_files[0])
    
    app = QtWidgets.QApplication([])
    scan_gui = ScanGui()
    scan_gui.show()
    app.exec_()
        

if __name__ == "__main__":
    args = sys.argv[1:]
    greyscale = False
    filename = ""
    display_gui = False
    if "--gui" in args:
        display_gui = True
        gui()
    if len(args) == 2 and (args[0] == "--greyscale" or args[0] == "-gs"):
        greyscale = True
        filename = args[1]
    elif len(args) == 2 and (args[1] == "--greyscale" or args[1] == "-gs"):
        greyscale = True
        filename = args[0]
    elif len(args) == 1:
        filename = args[0]
    
    if not display_gui:
        if filename == "" or filename[0] == '-':
            print("Scan document from Dell S2825cdn device.\n" + \
                  "Usage: dlscan [--gui] [file] [--greyscale] [-gs] [FILE]\n"+\
                  "Filenames cannot start with '-'.")
        else:
            arr= scan(greyscale)
            save_array_as_img(arr, filename)
   
