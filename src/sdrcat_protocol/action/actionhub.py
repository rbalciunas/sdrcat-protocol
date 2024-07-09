from __future__ import annotations

from . import ActionItem


class ActionHub:
    def __init__(self, strictRouting:bool = True):
        self.strictRouting = strictRouting
        self.registeredCommunicators = {}

    def Register(self, communicator:Communicator, name:str):
        if name in self.registeredCommunicators.keys():
            raise Exception(f"A communicator with the name {name} is already registered.")

        self.registeredCommunicators[name] = communicator
        communicator.HandleRegistrationResponse(self)

    def SendAction(self, item:ActionItem):
        if item is None:
            return

        queue = []

        queue.append(item)

        while len(queue) > 0:
            inProgressItem:ActionItem = queue.pop(0)

            if inProgressItem.target is None:
                if self.strictRouting:
                    raise Exception("Action item's target is null, so action item cannot be routed.")

                continue

            if self.registeredCommunicators[inProgressItem.target] is None and inProgressItem.target != "*":
                if (StrictRouting):
                    raise Exception(f"Action item's target {inProgressItem.target} is not registered, so action item has nowhere to go.")

                continue

            if inProgressItem.target == "*":
                for k in _registeredCommunicators:
                    _registeredCommunicators[k].HandleActionItemAsync(inProgressItem)
            else:
                inProgressResults = self.registeredCommunicators[inProgressItem.target].HandleActionItem(inProgressItem)
                queue.extend(inProgressResults)

    
class Communicator:
    def __init__(self):
        self.hub:ActionHub = None

    def HandleRegistrationResponse(self, hub:ActionHub):
        self.hub:ActionHub = hub

    # OVERRIDE THIS
    def HandleActionItem(action:ActionItem) -> list[ActionItem]:
        pass