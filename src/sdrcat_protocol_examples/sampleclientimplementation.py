from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Input, Log

import asyncio
import aiofiles
import datetime

from sdrcat_protocol.coordinator import ClientCoordinator
from sdrcat_protocol.deviceinfo import DeviceInfo
from sdrcat_protocol.action import ActionItem, ActionHub
from sdrcat_protocol.client import ClientBase
from sdrcat_protocol.comm import CommClientTCP
from sdrcat_protocol.definitions import ClientProtocolState, DispositionTypes, DataTypes

class InteractiveCLI(App, ClientBase):
    def __init__(self):
        super().__init__()

        # Textual stuff
        self.input_widget = Input()
        self.log_widget = Log()

        # SDRCat stuff
        hub = ActionHub()
        hub.Register(self, "client")
        hub.Register(ClientCoordinator(), "coordinator")
        hub.Register(CommClientTCP(), "comm")

        # Client stuff
        self.state = ClientProtocolState.Disconnected
        self.deviceInfo = None

    # Textual stuff
    def compose(self) -> ComposeResult:
        yield self.log_widget
        yield self.input_widget

    @on(Input.Submitted)
    def HandleUserInput(self):
        command = self.input_widget.value
        self.input_widget.value = ""
        self.Print(f"> {command}")

        try:
            if self.state == ClientProtocolState.Disconnected:
                if command.lower().startswith("connect"):
                    parts = command.split(' ')
                    self.Connect({"host": parts[1], "port": parts[2]})

                elif command.lower() == "exit":
                    self.exit() # Textual

                else:
                    self.Print("Not allow. Must connect first")

            elif self.state == ClientProtocolState.LinkEstablished:
                if command.lower() == "disconnect":
                    self.Disconnect()

                elif command.lower() == "exit":
                    self.Disconnect() # SDRCat
                    self.exit() # Textual

                elif command.lower().startswith("set"):
                    parts = command.split(' ')
                    self.SetPropertyValue(parts[1], parts[2])

                elif command.lower() == "list":
                    for k in self.deviceInfo.elements:
                        self.Print(f"{k}: {self.deviceInfo.elements[k].dataType}, {self.deviceInfo.elements[k].disposition}")

                elif command.lower().startswith("get"):
                    parts = command.split(' ')
                    self.GetPropertyValue(parts[1])

                elif command.lower() == "all":
                    for k in self.deviceInfo.elements:
                        if self.deviceInfo.elements[k].disposition == DispositionTypes.EditableProperty or self.deviceInfo.elements[k].disposition == DispositionTypes.ReadonlyProperty:
                            self.GetPropertyValue(k)

                elif command.lower().startswith("send"):
                    parts = command.split(' ')
                    self.SendData(parts[1], ' '.join(parts[2:]), {})

        except Exception as ex:
            self.Print(str(ex))

    async def OnReceiveDeviceInfoAsync(self, info:DeviceInfo):
        self.Print("Receiving Device Info")
        self.deviceInfo = info

    async def OnReceiveStatusChangeAsync(self, status:int): 
        self.Print(f"Status is now {status}")
        self.state = status

    async def OnReceiveDataAsync(self, streamName:str, streamValues:any, metadata:dict[str, any]):
        self.Print(f"Receiving Data on {streamName}: {streamValues}")

    async def OnReceivePropertyValueAsync(self, name:str, value:any):
        self.Print(f"Receiving Property Update: {name} = {value}")

    async def OnReveiveInformation(self, message:str): 
        self.Print(f"Info: {message}")

    def Print(self, value: str):
        self.log_widget.write_line(value)     

if __name__ == "__main__":
    app = InteractiveCLI()
    app.run()
