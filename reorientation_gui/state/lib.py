from typing import Any, Callable, List
from typing_extensions import Self


class State(object):

    def __init__(self, verify_change: bool = True):
        self.verify_change = verify_change

        self.callbacks: List[Callable[[Self], None]] = []
        self.changed = False

    def on_change(self, callback: Callable[[Self], None]):
        self.callbacks.append(callback)

    def notify_change(self, ignore_change: bool = False):
        if not ignore_change and self.verify_change and not self.changed:
            return

        self.changed = False
        for cb in self.callbacks:
            cb(self)

    def __setattr__(self, name, new_value):
        if name == "verify_change" or name == "changed" or name == "callbacks":
            super().__setattr__(name, new_value)
            return

        try:
            old_value = getattr(self, name)
        except AttributeError:
            # initial assignment
            super().__setattr__(name, new_value)
            return

        if self.verify_change and new_value == old_value:
            return

        super().__setattr__(name, new_value)
        self.changed = True

        if issubclass(type(self), BuiltInState):
            self.notify_change()


class BuiltInState(State):

    def __init__(self, value: Any):
        super().__init__()
        self.value = value

    def bind(self, other: "BuiltInState"):
        assert type(self) == type(
            other
        ), f"Binding of states is limited to same types {type(self)} != {type(other)}"
        self.on_change(lambda state: setattr(other, "value", state.value))
        other.on_change(lambda state: setattr(self, "value", state.value))

    def create_t(self, transformation_self_to_other, transformation_other_to_self):
        other = type(self)(transformation_self_to_other(self.value))
        self.on_change(lambda state: setattr(other, "value", transformation_self_to_other(state.value)))
        other.on_change(lambda state: setattr(self, "value", transformation_other_to_self(state.value)))
        return other


class IntState(BuiltInState):

    def __init__(self, value: int):
        super().__init__(value)


class FloatState(BuiltInState):

    def __init__(self, value: float):
        super().__init__(value)


class StringState(BuiltInState):

    def __init__(self, value: str):
        super().__init__(value)
