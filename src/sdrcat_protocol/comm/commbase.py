from sdrcat_protocol.action import GenerateFromComm, ActionHub, Communicator, ActionItem, Actions

import asyncio

class CommBase(Communicator):
    def __init__(self):
        super().__init__()

    def CommReceiving(self, data:bytes):
        self.hub.SendAction(GenerateFromComm.Receive(data))

    def CommDisconnecting(self):
        self.hub.SendAction(GenerateFromComm.Disconnect())

    def CommConnecting(self):
        self.hub.SendAction(GenerateFromComm.Connect())

    async def OnCommRequestWriteAsync(self, data:bytes): pass
    async def OnCommRequestDisconnectAsync(self): pass
    async def OnCommRequestConnectAsync(self, connectionParams:dict[str, any]): pass

    def HandleActionItem(self, action:ActionItem) -> list[ActionItem]:
        if action.target != "comm" and action.target != "*":
            raise Exception("Received action that is not destined for 'comm'.  There might have been a routing error somehwere.")

        if action.action == Actions.ToCommTransmit:
            asyncio.create_task(self.OnCommRequestWriteAsync(action.params.data))

        elif action.action == Actions.ToCommConnect:
            asyncio.create_task(self.OnCommRequestConnectAsync(action.params.connectionParams))

        elif action.action == Actions.ToCommDisconnect:
            asyncio.create_task(self.OnCommRequestDisconnectAsync())

        return []