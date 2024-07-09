from sdrcat_protocol.comm.commbase import CommBase

import asyncio

class CommClientTCP(CommBase):
    def __init__(self):
        super().__init__()
        self.writer : asyncio.StreamWriter = None
        self.serverTasks: list[Task] = []

    async def OnCommRequestWriteAsync(self, data:bytes):
        if self.writer is None:
            return

        self.writer.write(data)
        await self.writer.drain()

    async def OnCommRequestDisconnectAsync(self):
        if self.writer is None:
            return

        self.writer.close()
        await self.writer.wait_closed()
        
    async def OnCommRequestConnectAsync(self, connectionParams:dict[str, any]):
        if self.writer is not None:
            return

        reader:asyncio.StreamReader = None
        writer:asyncio.StreamReader = None

        reader, writer = await asyncio.open_connection(connectionParams["host"], connectionParams["port"])

        self.writer = writer
        self.CommConnecting()

        try:
            while True:
                payload:bytes = await reader.read(1024)
                if len(payload) == 0:
                    break

                self.CommReceiving(payload)
            
        except Exception as ex:
            print(ex)

        self.CommDisconnecting()
        self.writer = None