from . import devicecoordinatorsimplifiedcore as core

from sdrcat_protocol.definitions import DeviceProtocolState
from sdrcat_protocol.action import ActionItem, Actions, Communicator
from sdrcat_protocol.network import EnumerationSection, StreamReader

class DeviceCoordinatorSimplified(Communicator):
    def __init__(self):
        super().__init__()

        self.include_informational_messages = False

        # Coordinator State
        self._enumeration = EnumerationSection()
        self._nextElementId = 1024
        self._reader = StreamReader()
        self._state = DeviceProtocolState.Startup
        
    def HandleActionItem(self, action:ActionItem) -> list[ActionItem]:
        if action.target != "coordinator" and aciton.target != "*":
            raise Exception("Coordinator received action that was not destined for it. There might be an issue with routing somewhere.")

        intermediateActions:list[ActionItem] = []

        if action.action == Actions.FromDeviceStartup:
            intermediateActions = core.DeviceStarting(self._state)

        elif action.action == Actions.FromDeviceDefineProperty:
            intermediateActions = core.DeviceDefiningAvailableProperty(self._state, self._nextElementId, action.params.name, action.params.dataType, action.params.isReadOnly)

        elif action.action == Actions.FromDeviceDefineMetadata:
            intermediateActions = core.DeviceDefiningAvailableMetadata(self._state, self._nextElementId, action.params.name, action.params.dataType)

        elif action.action == Actions.FromDeviceDefineStream:
            intermediateActions = core.DeviceDefiningAvailableStream(self._state, self._nextElementId, action.params.name, action.params.dataType, action.params.isOutgoing)

        elif action.action == Actions.FromDeviceReady:
            intermediateActions = core.DeviceReadying(self._state, self._enumeration)

        elif action.action == Actions.FromDeviceReset:
            intermediateActions = core.DeviceResetting(self._state)

        if action.action == Actions.FromDevicePropertyValue:
            intermediateActions = core.DeviceReportingPropertyValue(self._state, self._enumeration, action.params.name, action.params.value)

        elif action.action == Actions.FromDeviceStreamData:
            intermediateActions = core.DeviceSendingDataToClient(self._state, self._enumeration, action.params.name, action.params.data, action.params.metadata)

        elif action.action == Actions.FromCommReceive:
            intermediateActions = core.CommReceivingData(self._state, self._enumeration, self._reader, action.params.data)

        resultActions:list[ActionItem] = []

        for action in intermediateActions:
            if action.target == "coordinator":
                if action.action == Actions.CoordinatorState:
                    self._state = action.params[0]

                elif action.action == Actions.CoordinatorSetEnumeration:
                    self._enumeration = EnumerationSection()

                elif action.action == Actions.CoordinatorResetNextElementId:
                    self._nextElementId = 1024
                    self._reader = StreamReader()

                elif action.action == Actions.CoordinatorIncrementNextElementId:
                    self._nextElementId += 1 

                elif action.action == Actions.CoordinatorAppendEnumeration:
                    self._enumeration.elements.append(action.params[0])

            elif action.action != Actions.CoordinatorInformation or (action.action == Actions.CoordinatorInformation and self.include_informational_messages):
                resultActions.append(action)

        return resultActions