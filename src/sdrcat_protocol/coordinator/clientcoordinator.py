from . import clientcoordinatorcore as core

from sdrcat_protocol.definitions import ClientProtocolState
from sdrcat_protocol.action import ActionItem, Actions, Communicator
from sdrcat_protocol.network import EnumerationSection, StreamReader

class ClientCoordinator(Communicator):
    def __init__(self):
        super().__init__()
        
        self.include_informational_messages = False

        # Coordinator State
        self._enumeration = EnumerationSection()
        self._reader = StreamReader()
        self._state = ClientProtocolState.Disconnected
        
    def HandleActionItem(self, action:ActionItem) -> list[ActionItem]:
        if action.target != "coordinator" and aciton.target != "*":
            raise Exception("Action was misrouted.")

        intermediateActions:list[ActionItem] = []

        if action.action == Actions.FromClientGetProperty:
            intermediateActions = core.ClientGettingPropertyValue(self._state, self._enumeration, action.params.name)

        elif action.action == Actions.FromClientSetProperty:
            intermediateActions = core.ClientSettingPropertyValue(self._state, self._enumeration, action.params.name, action.params.value)

        elif action.action == Actions.FromClientStreamData:
            intermediateActions = core.ClientSendingDataToDevice(self._state, self._enumeration, action.params.name, action.params.data, action.params.metadata)

        elif action.action == Actions.FromClientReset:
            intermediateActions = core.ClientResetting(self._state)

        elif action.action == Actions.FromClientConnect:
            intermediateActions = core.ClientConnecting(self._state, action.params.connectionParams)

        elif action.action == Actions.FromClientDisconnect:
            intermediateActions = core.ClientDisconnecting(self._state)

        elif action.action == Actions.FromCommConnect:
            intermediateActions = core.CommConnectiong(self._state)

        elif action.action == Actions.FromCommDisconnect:
            intermediateActions = core.CommDisconnecting(self._state)

        elif action.action == Actions.FromCommReceive:
            intermediateActions = core.CommReceivingData(self._state, self._enumeration, self._reader, action.params.data)

        resultActions:list[ActionItem] = []

        for action in intermediateActions:
            if action.target == "coordinator":
                if action.action == Actions.CoordinatorState:
                    self._state = action.params[0]

                elif action.action == Actions.CoordinatorClearEnumeration:
                    self._enumeration = EnumerationSection()

                elif action.action == Actions.CoordinatorSetEnumeration:
                    self._enumeration = action.params[0]

            elif action.action != Actions.CoordinatorInformation or (action.action == Actions.CoordinatorInformation and self.include_informational_messages):
                resultActions.append(action)

        return resultActions