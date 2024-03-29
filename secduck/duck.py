"""
A class that represents the Duck.
"""

from enum import Enum
import logging
from threading import Timer

from .recorder import Recorder
from .speaker import Speaker
from .device_input import DeviceInput
from .device_output import DeviceOutput
from .connector import Connector

logger = logging.getLogger("Duck")


class DuckState(Enum):
    """States Duck can take"""

    PAUSE = 1
    FOCUS = 2
    BREAK = 3
    BUSY = 4


class Duck:
    """
    A class that represents the Duck.

    Args:
        device_input: DeviceInput
        device_output: DeviceOutput
        connector: Connector
        speaker: Speaker
        recorder: Recorder
    """

    def __init__(
        self,
        device_input: DeviceInput,
        device_output: DeviceOutput,
        connector: Connector,
        speaker: Speaker,
        recorder: Recorder,
    ):
        self.device_input = device_input
        self.device_output = device_output
        self.connector = connector
        self.speaker = speaker
        self.recorder = recorder

        # Interaction mappings
        self.device_input.on_pause = self.on_pause
        self.device_input.on_break = self.on_break
        self.device_input.on_focus = self.on_focus
        self.device_input.on_start_recording = self.on_start_recording
        self.device_input.on_stop_recording = self.on_stop_recording
        self.device_input.on_review = self.on_review
        self.device_input.on_sync = self.on_sync
        self.device_input.on_before = self.on_before

        self.on_sync()

        self.timer = None
        self.state = DuckState.PAUSE
        self.device_output.on_pause()

    def on_pause(self):
        """Duck starts pausing."""
        logger.info("Start pausing")
        if self.state == DuckState.BUSY:
            logger.warning("Busy now")
            return
        elif self.state == DuckState.PAUSE:
            logger.warning("Already paused")
            return
        self.state = DuckState.BUSY
        self.device_output.on_pause()
        audio = self.connector.fetch("pause")
        if audio:
            self.speaker.start(audio, self.device_input.volume)
        self.state = DuckState.PAUSE

    def on_break(self):
        """Duck takes a break."""
        logger.info("Take a break")
        if self.state == DuckState.BUSY:
            logger.warning("Busy now")
            return
        elif self.state == DuckState.BREAK:
            logger.warning("Already on break")
            return
        self.state = DuckState.BUSY
        self.device_output.on_break()
        audio = self.connector.fetch("break")
        if audio:
            self.speaker.start(audio, self.device_input.volume)
        self.state = DuckState.BREAK

        self.timer = Timer(5 * 60, self.on_focus)
        self.timer.start()

    def on_focus(self):
        """Duck starts focusing."""
        logger.info("Start focusing")
        if self.state == DuckState.BUSY:
            logger.warning("Busy now")
            return
        elif self.state == DuckState.FOCUS:
            logger.warning("Already focusing")
            return
        self.state = DuckState.BUSY
        self.device_output.on_focus()
        audio = self.connector.fetch("focus")
        if audio:
            self.speaker.start(audio, self.device_input.volume)
        self.state = DuckState.FOCUS

        self.timer = Timer(25 * 60, self.on_break)
        self.timer.start()

    def on_review(self):
        """Duck starts reviewing."""
        logger.info("Start reviewing")
        if self.state == DuckState.BUSY:
            logger.warning("Busy now")
            return
        self.state = DuckState.BUSY
        self.device_output.on_review()
        audio = self.connector.fetch("review")
        if audio:
            self.speaker.start(audio, self.device_input.volume)
        self.state = DuckState.PAUSE

    def on_start_recording(self):
        """Duck starts recording."""
        logger.info("Start recording")
        self.recorder.start()

    def on_stop_recording(self):
        """Duck stops recording."""
        logger.info("Stop recording")
        self.recorder.stop()
        audio = self.recorder.export()
        self.connector.log_record(audio)

    def on_wakeup(self):
        """Duck wakes up."""
        logger.info("Wake up")
        if self.state == DuckState.BUSY:
            logger.warning("Busy now")
            return
        audio = self.connector.fetch("wakeup")
        if audio:
            self.speaker.start(audio, self.device_input.volume)

    def on_exit(self):
        """Duck exits."""
        logger.info("Exit")
        if self.state == DuckState.BUSY:
            logger.warning("Busy now")
            return
        audio = self.connector.fetch("exit")
        if audio:
            self.speaker.start(audio, self.device_input.volume)

    def on_sync(self):
        """Duck syncs."""
        logger.info("Sync")
        self.connector.sync()

    def on_before(self):
        """Callback before interaction."""
        logger.info("Call `before` process")
        if self.timer:
            self.timer.cancel()
            self.timer = None
