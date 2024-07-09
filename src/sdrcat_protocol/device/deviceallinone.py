from sdrcat_protocol.device import DeviceBase
from sdrcat_protocol.comm.commbase import CommBase
from sdrcat_protocol.definitions import DataTypes
from sdrcat_protocol.action import ActionItem, GenerateFromDevice, GenerateFromComm, Actions, ActionHub
from sdrcat_protocol.coordinator import DeviceCoordinatorSimplified

class DeviceAllInOne(DeviceBase, CommBase):
    def __init__(self):
        super().__init__()

    def InitSimplifiedProtocol(self):
        hub = ActionHub()
        hub.Register(self, "device")
        hub.Register(self, "comm")
        hub.Register(DeviceCoordinatorSimplified(), "coordinator")

    def DefineProperty(self, name:str, dataType:DataTypes, isReadOnly:bool = False):
        self.hub.SendAction(GenerateFromDevice.DefineProperty(name, dataType, isReadOnly))

    def DefineStream(self, name:str, dataType:DataTypes, isOutgoing:bool = False):
        self.hub.SendAction(GenerateFromDevice.DefineStream(name, dataType, isOutgoing))

    def DefineMetadata(self, name:str, dataType:DataTypes):
        self.hub.SendAction(GenerateFromDevice.DefineMetadata(name, dataType))

    def ReportPropertyChanged(self, name:str, value: any):
        self.hub.SendAction(GenerateFromDevice.PropertyValue(name, value))

    def ReportStreamData(self, name:str, data:any, metadata:dict[str,any]):
        self.hub.SendAction(GenerateFromDevice.StreamData(name, data, metadata))

    def Start(self, connectionParams:dict[str,any]):
        self.hub.SendAction(GenerateFromDevice.Start(connectionParams))

    def Reset(self):
        self.hub.SendAction(GenerateFromDevice.Reset())

    def CommReceiving(self, data:bytes):
        self.hub.SendAction(GenerateFromComm.Receive(data))

    def OnDefine(self): pass
    def OnGetProperty(self, name:str) -> any: return None
    def OnSetProperty(self, name:str, value: any) -> bool: return False
    def OnReceiveStreamData(self, name:str, data:any, metadata:dict[str,any]): pass
    def OnCommRequestWrite(self, data:bytes): pass

    def _DoGetProperty(self, propName:str):
        value = self.OnGetProperty(propName)
        if value is not None:
            self.hub.SendAction(GenerateFromDevice.PropertyValue(propName, value))

    def _DoSetProperty(self, propName:str, value:any):
        if self.OnSetProperty(propName, value):
            self.hub.SendAction(GenerateFromDevice.PropertyValue(propName, value))

    def _DoReset(self):
        self.OnDefine()
        self.hub.SendAction(GenerateFromDevice.Ready())

    def HandleActionItem(self, action:ActionItem) -> list[ActionItem]:
        if action.target != "device" and action.target != "comm" and action.target != "*":
            raise Exception("Received action that is not destined for 'device' or 'comm'.  There might have been a routing error somehwere.")

        if action.action == Actions.ToDeviceGetProperty:
            self._DoGetProperty(action.params.name)

        elif action.action == Actions.ToDeviceSetProperty:
            self._DoSetProperty(action.params.name, action.params.value)

        elif action.action == Actions.ToDeviceStreamData: 
            self.OnReceiveStreamData(action.params.name, action.params.data, action.params.metadata)

        elif action.action == Actions.ToDeviceReset:
            self._DoReset()

        elif action.action == Actions.ToCommTransmit:
            self.OnCommRequestWrite(action.params.data)

        elif action.action == Actions.ToCommConnect:
            self.OnCommRequestConnectAsync(action.params.connectionParams)

        elif action.action == Actions.ToCommDisconnect:
            self.OnCommRequestDisconnectAsync()

        return []


