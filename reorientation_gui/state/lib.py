from typing import Callable, List
from typing_extensions import Self

class State(object):

    def __init__(self):
        self.callbacks: List[Callable[[Self], None]] = []
        self.changed = False

    def on_change(self, callback: Callable[[Self], None]):
        self.callbacks.append(callback)

    def notify_change(self):
        if not self.changed:
            return

        for cb in self.callbacks:
            cb(self)
        self.changed = False

    def __setattr__(self, name, new_value):
        if name == "changed" or name == "callbacks":
            super().__setattr__(name, new_value)
            return

        try:
            old_value = getattr(self, name)
        except AttributeError:
            # initial assignment
            super().__setattr__(name, new_value)
            return

        if new_value == old_value:
            return

        super().__setattr__(name, new_value)
        self.changed = True




if __name__ == "__main__":
    class TestState(State):
        def __init__(self):
            super().__init__()
            self.number = 0.0
            self.str = "hello"
            self.list = [1.0, 2.0, 3.0]
            self.tuple = (0.0, 1.0)

    test = TestState()
    test.on_change(lambda x: print(f"State ({test.number}, {test.str}, {test.list}, {test.tuple}) changed!"))

    test.notify_change()
    test.number = 1.0
    test.notify_change()
    test.number = 1.0
    test.notify_change()
    test.notify_change()

    print()
    test.str = "hello"
    test.notify_change()
    test.str = "world"
    test.notify_change()
    test.notify_change()

    print()
    test.list = [1.0, 2.0, 3.0]
    test.notify_change()
    test.list = [1.0, -2.0, 3.0]
    test.notify_change()


