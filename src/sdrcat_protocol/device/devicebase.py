from sdrcat_protocol.action import ActionItem, GenerateFromDevice, Actions, ActionHub, Communicator
from sdrcat_protocol.deviceinfo import DeviceInfo
from sdrcat_protocol.definitions import DataTypes

import asyncio

class DeviceBase(Communicator):
    def __init__(self):
        super().__init__()

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

    async def OnDefine(self): pass
    async def OnGetProperty(self, name:str) -> any: return None
    async def OnSetProperty(self, name:str, value: any) -> bool: return False
    async def OnReceiveStreamData(self, name:str, data:any, metadata:dict[str,any]): pass

    async def _DoGetProperty(self, propName:str):
        value = await self.OnGetProperty(propName)
        if value is not None:
            self.hub.SendAction(GenerateFromDevice.PropertyValue(propName, value))

    async def _DoSetProperty(self, propName:str, value:any):
        if await self.OnSetProperty(propName, value):
            self.hub.SendAction(GenerateFromDevice.PropertyValue(propName, value))

    async def _DoReset(self):
        await self.OnDefine()
        self.hub.SendAction(GenerateFromDevice.Ready())

    def HandleActionItem(self, action:ActionItem) -> list[ActionItem]:
        if action.target != "device" and action.target != "*":
            raise Exception("Received action that is not destined for 'device'.  There might have been a routing error somehwere.")

        if action.action == Actions.ToDeviceGetProperty:
            asyncio.create_task(self._DoGetProperty(action.params.name))

        elif action.action == Actions.ToDeviceSetProperty:
            asyncio.create_task(self._DoSetProperty(action.params.name, action.params.value))

        elif action.action == Actions.ToDeviceStreamData: 
            asyncio.create_task(self.OnReceiveStreamData(action.params.name, action.params.data, action.params.metadata))

        elif action.action == Actions.ToDeviceReset:
            asyncio.create_task(self._DoReset())

        return []


        
