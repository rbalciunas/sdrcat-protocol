from sdrcat_protocol.comm.commbase import CommBase

import asyncio

class CommDeviceTCP(CommBase):
    def __init__(self):
        super().__init__()
        self.writer : asyncio.StreamWriter = None
        self.serverTasks: list[Task] = []

    async def OnCommRequestWriteAsync(self, data:bytes):
        if self.writer is None:
            return

        self.writer.write(data)
        await self.writer.drain()
        
    async def OnCommRequestConnectAsync(self, connectionParams:dict[str, any]):
        asyncio.create_task(self._TcpConnectionListenLoop(connectionParams["host"], connectionParams["port"]))

    async def _TcpConnectionListenLoop(self, host:str, port:int):
        try:    
            server = await asyncio.start_server(self._HandleClient, host, port, limit=1)
            async with server:
                await server.serve_forever()
        except Exception as ex:
            print(ex)

    async def _HandleClient(self, reader:asyncio.StreamReader, writer:asyncio.StreamWriter):
        if self.writer is not None:
            writer.close()
            return

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