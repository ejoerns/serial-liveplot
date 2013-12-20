serial-liveplot
===============

Live plotting of data from serial interface (including AVR library)

Consists of two simple components:

* live plot python program
* AVR data encoder libray

Features

* Platform independent python program!
* No channel setup required on computer side (plug-in and plot!)
* Plot up to 16 data channels with up to 16 sub-channels (vector) each

Simple Workflow
---

1. Add the AVR library to your mikrocontoller project
2. Add some lines in your code to setup channels and send data
3. Programm your device
3. Connect to your PC (mostly with UART-USB converter)
4. Start plot script
5. Start your device
