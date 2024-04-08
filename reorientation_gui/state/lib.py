from typing import Callable, List
from typing_extensions import Self

class State:

    def __init__(self):
        self.callbacks: List[Callable[[Self], None]] = []

    def on_change(self, callback: Callable[[Self], None]):
        self.callbacks.append(callback)

    def notify_change(self):
        for cb in self.callbacks:
            cb(self)


