"""Abstract Duck with threading"""
import threading
import logging
import base64
import requests
from requests.exceptions import RequestException
from transitions import Machine
from .recorder import Recorder
from .speaker import Speaker
from .settings import REC_CONFIG, SPK_CONFIG

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d:%(threadName)s:%(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG,
)

SERVER_URI = "http://localhost:8080"
# SERVER_URI = "https://secduck-upload-server-xwufhlvadq-an.a.run.app"


class LaptopDuck:
    """Duck who can be run on a laptop"""

    states = ["init", "pause", "work", "break", "busy"]

    def __init__(self, user_id, server):
        self.user_id = user_id
        self.server = server
        self.machine = Machine(
            model=self,
            states=LaptopDuck.states,
            initial="init",
        )
        self._lock = threading.Lock()

        self.recorder = Recorder(**REC_CONFIG)
        self.speaker = Speaker(**SPK_CONFIG)

    def start_recording(self):
        """Start listening to the mic"""
        logging.info("DUCK: Start listening to your voice")
        self.recorder.start()

    def stop_recording(self):
        """Stop listening to the mic"""
        logging.info("DUCK: Stop listening to your voice")
        self.recorder.stop()
        self._send_audio(self.recorder.get_wav())

    def start_speaking(self, file: str):
        """Start speaking from the speaker"""
        logging.info("DUCK: Start speaking")
        self.speaker.start(file)

    def stop_speaking(self):
        """Stop speaking from the speaker"""
        logging.info("DUCK: Stop speaking")
        self.speaker.stop()

    def _send_audio(self, audio: bytes):
        data = {
            "user_id": "payashi",
            "duck_id": "duck01",
            "audio": self._marshal_bytes(audio),
        }

        try:
            response = requests.post(SERVER_URI, json=data, timeout=10)
            response.raise_for_status()
            logging.info("DUCK: Receive from server: %s", str(response.text))
        except RequestException as e:
            logging.exception("DUCK: Failed to request: %s", e.response)

    def _marshal_bytes(self, data: bytes) -> str:
        return base64.b64encode(data).decode("utf-8")