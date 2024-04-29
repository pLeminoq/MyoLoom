from typing import Union

from reorientation_gui.state.lib import State, IntState

IntType = Union[int, IntState]

class Point(State):

    def __init__(self, x: IntType, y: IntType):
        super().__init__()

        self.x = x if type(x) == IntState else IntState(x)
        self.y = y if type(y) == IntState else IntState(y)

        self.x.on_change(lambda _: self.notify_change(ignore_change=True))
        self.y.on_change(lambda _: self.notify_change(ignore_change=True))

    def __iter__(self):
        return iter((self.x.value, self.y.value))

    def __getitem__(self, i):
        return (self.x.value, self.y.value)[i]

    def update(self, x: int, y: int, notify=True):
        self.x.value = x
        self.y.value = y
        
        if notify:
            self.notify_change(ignore_change=True)
