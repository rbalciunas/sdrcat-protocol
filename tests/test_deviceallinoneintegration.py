from sdrcat_protocol.device import DeviceAllInOne

from sdrcat_protocol.definitions import DataTypes, DeviceProtocolState, SectionTypes, DispositionTypes
from sdrcat_protocol.network import Packet, DataSection, GetPropertySection, PropertyValueSection, Section
from sdrcat_protocol.deviceinfo import DeviceInfo

class TestDevice(DeviceAllInOne):
    def __init__(self):
        super().__init__()

        self.properties = {}
        self.lastStreamDataReceived = ""
        self.lastOutgoingData = b''

        self.InitSimplifiedProtocol()
        self.Start({})

    def OnDefine(self):
        self.DefineProperty("prop1", DataTypes.sint32)
        self.properties["prop1"] = 15
        self.DefineStream("stream0", DataTypes.utf8)
        self.DefineStream("stream1", DataTypes.utf8, True)

    def OnGetProperty(self, name:str) -> any:
        return self.properties[name]

    def OnSetProperty(self, name:str, value: any) -> bool:
        self.properties[name] = value
        return True

    def OnReceiveStreamData(self, name:str, data:any, metadata:dict[str,any]):
        if name == "stream0":
            self.lastStreamDataReceived = data

    def OnCommRequestWrite(self, data:bytes):
       self.lastOutgoingData = data

def test_device_initialization():
    dut = TestDevice()
    assert dut.properties["prop1"] == 15
    assert dut.hub.registeredCommunicators["coordinator"]._state == DeviceProtocolState.LinkEstablished

def test_outgoing_stream():
    dut = TestDevice()
    dut.ReportStreamData("stream1", "teststreamdata", {})
    
    assert len(dut.lastOutgoingData) > 0

    p = Packet.Decode(dut.lastOutgoingData)

    assert p.sections[0].sectionType == SectionTypes.DeviceToClientStream
    assert p.sections[0].dataBytes == "teststreamdata".encode("utf8")

def test_incoming_stream():
    dut = TestDevice()
    dut.CommReceiving(Packet([DataSection(SectionTypes.ClientToDeviceStream, 1025, "teststreamdata".encode("utf8"), [])]).Encode())

    assert dut.lastStreamDataReceived == "teststreamdata"

def test_property_get():
    dut = TestDevice()
    dut.CommReceiving(Packet([GetPropertySection(1024)]).Encode())

    p = Packet.Decode(dut.lastOutgoingData)
    assert p.sections[0].sectionType == SectionTypes.NotifyProperty
    assert p.sections[0].propertyValueBytes == b'\x00\x00\x00\x0F'

def test_property_set():
    dut = TestDevice()
    dut.CommReceiving(Packet([PropertyValueSection(SectionTypes.SetProperty, 1024, b'\x00\x00\x00\x10')]).Encode())

    assert dut.properties["prop1"] == 16

    p = Packet.Decode(dut.lastOutgoingData)

    assert p.sections[0].sectionType == SectionTypes.NotifyProperty
    assert p.sections[0].elementId == 1024
    assert p.sections[0].propertyValueBytes == b'\x00\x00\x00\x10'

def test_property_notify():
    dut = TestDevice()
    dut.ReportPropertyChanged("prop1", 16)

    p = Packet.Decode(dut.lastOutgoingData)

    assert p.sections[0].sectionType == SectionTypes.NotifyProperty
    assert p.sections[0].elementId == 1024
    assert p.sections[0].propertyValueBytes == b'\x00\x00\x00\x10'

def test_enumerate():
    dut = TestDevice()
    dut.CommReceiving(Packet([Section()]).Encode())

    p = Packet.Decode(dut.lastOutgoingData)

    assert p.sections[0].sectionType == SectionTypes.Enumeration

    di = DeviceInfo(p.sections[0])

    assert di.elements["prop1"].disposition == DispositionTypes.EditableProperty
    assert di.elements["prop1"].dataType == DataTypes.sint32
    assert di.elements["stream0"].disposition == DispositionTypes.ClientToDeviceStream
    assert di.elements["stream0"].dataType == DataTypes.utf8
    assert di.elements["stream1"].disposition == DispositionTypes.DeviceToClientStream
    assert di.elements["stream1"].dataType == DataTypes.utf8