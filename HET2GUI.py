"""
Tanner Songkakul

CustomPeripheralGUI.py

Uses bleak and PyQT to connect to a CC2642 Launchpad running Custom Peripheral
and plot data on each characteristics. Utilizes single-thread asyncio loop which acts as a scheduler.

Requires bleak, pyqt, qasync and included customperipheral library
"""

from PyQt5 import QtWidgets
import sys
import asyncio
from qasync import QEventLoop
from het2 import HET2Device
from het2 import HETWindow
from bleak import BleakClient
from bleak import discover

# GLOBALS
# TODO: find a better way to use this with the notification handler without using as global
het = HET2Device()


def notification_handler(sender, data):
    """Handle incoming packets."""
    print(sender,data)
    het.datacount = het.datacount + 1
    if sender == het.CHAR1:
        het.parse_info(data)
    if sender == het.CHAR2:
        het.parse_data(data, "AMPPH")

async def plot_handler(het, win):
    """Asynchronously update the plot each second """
    while 1:  # TODO: remove loop here to allow disconnect/reconnect
        win.update_plot(het)
        await asyncio.sleep(5)


async def button_wait(win):
    """Polling for button press"""
    while not win.connect_button:  # wait for button press flag to be set in GUI
        await asyncio.sleep(.01)
    win.button_ack("connect")  # clear button press flag

async def find_device(win, het):
    """Search for device after button press"""
    await button_wait(win)  # Wait for button press
    win.display_status("Scanning...")
    devices = await discover()  # Discover devices on BLE
    het.set_name(win.device_name)  # Get device name from text input window in GUI
    device_found = het.get_address(devices)  # Check if device in list
    return device_found


async def enable_notif(het, client):
    """Start notifications on all characteristics"""
    for char in het.CHAR_LIST:
        await client.start_notify(char, notification_handler)
    # print("Notifications enabled")


async def disable_notif(het, client):
    """Stop notifications on all characteristics"""
    for char in het.CHAR_LIST:
        await client.stop_notify(char, notification_handler)


async def run(win, het, loop):
    """Main asyncio loop"""
    while 1:  # TODO replace this loop to allow for disconnect/reconnect
        # while not cp.CONNECTED:
        dev_found = await find_device(win, het)  # Find device address
        if dev_found:
            win.display_status("Device {} found! Connecting...".format(het.NAME))
            async with BleakClient(het.ADDR, loop=loop) as client:
                x = await client.is_connected()  # Attempt device connection TODO add try except with error msg
                win.display_status("Connected!")
                await enable_notif(het, client)
                await plot_handler(het, win)
                await disable_notif(het, client)
        else:
            win.display_status("ERROR: Device not found.")


def main():
    app = QtWidgets.QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)  # NEW must set the event loop

    win = HETWindow()
    win.show()

    with loop:  ## context manager calls .close() when loop completes, and releases all resources
        loop.run_until_complete(run(win, het, loop))


if __name__ == '__main__':
    main()
