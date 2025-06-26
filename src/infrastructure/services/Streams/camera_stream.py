# src/infrastructure/camera_stream.py

import cv2
from threading import Thread, Lock
import queue

class VideoStream:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls(*args, **kwargs)
        return cls._instance

    def __init__(self, src=0):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self.stream = cv2.VideoCapture(src)
        self.queue = queue.Queue(maxsize=1)
        self.stopped = False
        self.thread = None

    def start(self):
        self.stopped = False
        if self.thread is None or not self.thread.is_alive():
            self.thread = Thread(target=self.update, daemon=True)
            self.thread.start()
        return self

    def update(self):
        while not self.stopped:
            if not self.queue.full():
                ret, frame = self.stream.read()
                if not ret:
                    self.stop()
                    return
                self.queue.put(frame)

    def read(self):
        return self.queue.get()

    def stop(self):
        self.stopped = True
        if self.thread is not None:
            self.thread.join(timeout=2)
            self.thread = None
        self.stream.release()
