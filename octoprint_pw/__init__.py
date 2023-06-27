# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import time
import requests
import asyncio
from threading import Thread

endpoint = "http://139.144.16.65:8888/api/upload"

class PwPlugin(
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.ProgressPlugin,
    octoprint.plugin.EventHandlerPlugin,
):
    def __init__(self):
        self.bed_buffer = []
        self.hotend_buffer = []
        self.sending = False

    def on_after_startup(self):
        self._logger.info("Print W")
        self.run_thread = True
        self._loop = Thread(target=self._run)
        self._loop.daemon = True
        self._loop.start()

    # runs every 1% progress during printing job
    # def on_print_progress(self, storage, path, progress):
    #     print("print progress confirm")
    #     return super().on_print_progress(storage, path, progress)
    def _run(self):
        while self.run_thread:
            if self._printer.is_printing():
                temperatures = self._printer.get_current_temperatures()
                bed_temp = temperatures["bed"]
                # part_id, part_model, command_temp, actual_temp, ki, kp, kd, command_power, actual_power, x_dmin, y_dmin
                bed_row = [
                    None,
                    "bed",
                    bed_temp["target"],
                    bed_temp["actual"],
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                ]
                self.bed_buffer.append(bed_row)

                hotend_temp = [temperatures[hotend_key]
                    for hotend_key in list(temperatures.keys())
                    if hotend_key[0] == "t"
                ]
                for num, hotend in enumerate(hotend_temp):
                    # part_id, part_model, command_temp, actual_temp, ki, kp, kd, command_power, actual_power
                    hotend_row = [
                        None,
                        "tool" + str(num),
                        hotend["target"],
                        hotend["actual"],
                        None,
                        None,
                        None,
                        None,
                        None,
                    ]
                    self.hotend_buffer.append(hotend_row)
                self._logger.info("BUFFER: {}".format(self.hotend_buffer))
                self._logger.info("BUFF2: {}".format(self.bed_buffer))
                if len(self.hotend_buffer) >= 128:
                    bed_data = {
                        "credentials": "7459df75-9f79-4dbf-9e7d-828aad9f95c9",
                        "image": None,
                        "data": self.bed_buffer,
                        "name": "bed",
                    }
                    hotend_data = {
                        "credentials": "7459df75-9f79-4dbf-9e7d-828aad9f95c9",
                        "image": None,
                        "data": self.hotend_buffer,
                        "name": "hotend",
                    }

                    bed_response = requests.post(endpoint, json=bed_data)
                    hotend_response = requests.post(endpoint, json=hotend_data)
                    if bed_response.status_code == 200:
                        print("bed data sent")
                    else:
                        print("bed data not sent due to ", bed_response.status_code)

                    if hotend_response.status_code == 200:
                        print("hotend data sent")
                    else:
                        print("hotend data not sent due to ", hotend_response.status_code)
                    self.hotend_buffer = []
                    self.bed_buffer = []
                time.sleep(0.25)
            else:
                time.sleep(5.0)


    def on_event(self, event, payload):  # listen for printstarted
        printer = self._printer
        if event == "PrintStarted" or event == "PrintResumed":  # infinitely collect data on 5 second intervals while the printer is printing
            if event == "PrintStarted": # if a new print job started, reset the buffer
                self.bed_buffer = []
                self.hotend_buffer = []

        if event == "PrintDone":  # send data to api once print is done
            self.bed_buffer = []
            self.hotend_buffer = []

        if event == "PrintCancelled" or "PrintFailed": # reset buffer
            self.bed_buffer = []
            self.hotend_buffer = []

        return


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Pw Plugin"


# Set the Python version your plugin is compatible with below. Recommended is Python 3 only for all new plugins.
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PwPlugin()
