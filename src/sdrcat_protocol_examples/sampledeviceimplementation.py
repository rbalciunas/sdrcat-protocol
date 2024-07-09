from sdrcat_protocol.device import DeviceBase
from sdrcat_protocol.action import ActionHub
from sdrcat_protocol.coordinator import DeviceCoordinator
from sdrcat_protocol.comm import CommDeviceTCP
from sdrcat_protocol.definitions import DataTypes

import asyncio
from random import randint

class SampleDeviceImplementation(DeviceBase):
    def __init__(self):
        super().__init__()

        hub = ActionHub()
        hub.Register(self, "device")
        hub.Register(DeviceCoordinator(), "coordinator")
        hub.Register(CommDeviceTCP(), "comm")

        self.device = UselessDevice()

    async def StartDevice(self, host:str, port:int):
        try:
            await asyncio.create_task(self._DeviceLoop(host, port))
        except Exception as ex:
            print(ex)

    async def _DeviceLoop(self, host:str, port:int):        
        self.Start({"host": host, "port": port})

        while True:
            await asyncio.sleep(5) # make the device "do" someting every 5 seconds

            whattodo = randint(0, 1)

            if whattodo == 0:
                if self.device.changePropertiesRandomly == "true": # set prop1 to a random value
                    newValue = ["foo", "bar", "baz"][randint(0,2)]
                    self.device.prop1 = newValue

                    self.ReportPropertyChanged("prop1", newValue)

                else: # send "Nothing to report." through stream0
                    self.ReportStreamData("stream0", "Nothing to report.", {})

            elif whattodo == 1: # send data through stream0
                self.ReportStreamData("stream0", self.device.provideIncomingStreamData(), {})

    async def OnDefine(self):
        self.DefineProperty("prop1", DataTypes.utf8, isReadOnly=True)
        self.DefineProperty("prop2", DataTypes.utf8, isReadOnly=False)
        self.DefineProperty("prop3", DataTypes.uint32, isReadOnly=False)
        self.DefineProperty("changePropertiesRandomly", DataTypes.utf8, isReadOnly=False)
        self.DefineStream("stream0", DataTypes.utf8, isOutgoing=True)
        self.DefineStream("stream1", DataTypes.utf8, isOutgoing=False)

    async def OnGetProperty(self, name:str) -> any:
        return getattr(self.device, name)

    async def OnSetProperty(self, name:str, value: any) -> bool:
        setattr(self.device, name, value)
        return True

    async def OnReceiveStreamData(self, name:str, data:any, metadata:dict[str,any]):
        self.device.consumeOutgoingStreamData(data)

class UselessDevice:
    def __init__(self):
        self.prop1: str = "foo"
        self.prop2: str = "bar"
        self.prop3: int = 7337
        self.changePropertiesRandomly:str = "true"

        self.receivedStreamData:str = ''

    def consumeOutgoingStreamData(self, data:str) -> None:
        self.receivedStreamData = data

    def provideIncomingStreamData(self) -> str:
        if len(self.receivedStreamData) == 0:
            return "Big giant void!"

        words = self.receivedStreamData.split(' ')

        newWords = []
        while len(words) > 0:
            randPos = randint(0, len(words) - 1)
            newWords.append(words[randPos])
            words.pop(randPos)

        return ' '.join(newWords)

if __name__ == "__main__":
    deviceServer = SampleDeviceImplementation()
    asyncio.run(deviceServer.StartDevice("localhost", 1776))