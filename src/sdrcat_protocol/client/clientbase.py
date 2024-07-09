from sdrcat_protocol.action import ActionItem, GenerateFromClient, Actions, ActionHub, Communicator
from sdrcat_protocol.deviceinfo import DeviceInfo

import asyncio

class ClientBase(Communicator):
    def __init__(self):
        super().__init__()

    def Reset(self):
        self.hub.SendAction(GenerateFromClient.Reset())

    def GetPropertyValue(self, name:str):
        self.hub.SendAction(GenerateFromClient.GetProperty(name))

    def SetPropertyValue(self, name:str, value:any):
        self.hub.SendAction(GenerateFromClient.SetProperty(name, value))

    def SendData(self, name:str, data:any, metadata:dict[str, any]):
        self.hub.SendAction(GenerateFromClient.SendData(name, data, metadata))

    def Connect(self, connectionParams:dict[str, any]):
        self.hub.SendAction(GenerateFromClient.Connect(connectionParams))

    def Disconnect(self):
        self.hub.SendAction(GenerateFromClient.Disconnect())

    async def OnReceiveDeviceInfoAsync(self, info:DeviceInfo): pass
    async def OnReceiveStatusChangeAsync(self, status:int): pass
    async def OnReceiveDataAsync(self, streamName:str, streamValues:any, metadata:dict[str, any]): pass
    async def OnReceivePropertyValueAsync(self, name:str, value:any): pass
    async def OnReveiveInformation(self, message:str): pass

    def HandleActionItem(self, action:ActionItem) -> list[ActionItem]:
        if action.target != "client" and action.target != "*":
            raise Exception("Received action that is not destined for 'client'.  There might have been a routing error somehwere.")

        if action.action == Actions.ToClientDeviceInfo:
            asyncio.create_task(self.OnReceiveDeviceInfoAsync(action.params.deviceInfo))

        elif action.action == Actions.ToClientPropertyValue:
            asyncio.create_task(self.OnReceivePropertyValueAsync(action.params.name, action.params.value))

        elif action.action == Actions.ToClientStatus:
            asyncio.create_task(self.OnReceiveStatusChangeAsync(action.params.state))

        elif action.action == Actions.ToClientStreamData:
            asyncio.create_task(self.OnReceiveDataAsync(action.params.name, action.params.data, action.params.metadata))

        elif action.action == Actions.CoordinatorInformation:
            asyncio.create_task(self.OnReveiveInformation(action.params.message))

        return []
