from sdrcat_protocol.coordinator import DeviceCoordinatorSimplified as DeviceCoordinator
from sdrcat_protocol.definitions import SectionTypes, DataTypes, DispositionTypes, DeviceProtocolState
from sdrcat_protocol.network import Packet, Section, GetPropertySection, DataSection, PropertyValueSection
from sdrcat_protocol.action import Actions, GenerateFromDevice as DevGen, GenerateFromComm as ComGen

# TODO: Write tests involving defining, transmitting and receiving metadata

def test0():
    dut = DeviceCoordinator()
    res:list[ActionItem] = []

    # verify initial state
    assert dut._state == DeviceProtocolState.NotReadyConnected

    res.extend(dut.HandleActionItem(DevGen.Start({})))

    # path 0
    assert dut._state == DeviceProtocolState.NotReadyConnected
    assert len(res) == 0

def test1():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))

    # verify initial state
    assert dut._state == DeviceProtocolState.NotReadyDisconnected

    dut.HandleActionItem(DevGen.Ready())

    # path 4
    assert dut._state == DeviceProtocolState.ReadyDisconnected

    dut.HandleActionItem(DevGen.Reset())

    # path 5
    assert dut._state == DeviceProtocolState.NotReadyDisconnected

def test2():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))

    assert dut._state == DeviceProtocolState.NotReadyDisconnected

    dut.HandleActionItem(ComGen.Connect())

    # path 8
    assert dut._state == DeviceProtocolState.NotReadyConnected

    dut.HandleActionItem(ComGen.Disconnect())

    # path 9
    assert dut._state == DeviceProtocolState.NotReadyDisconnected

def test3():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))

    dut.HandleActionItem(DevGen.Ready())
    dut.HandleActionItem(ComGen.Connect())

    # path 10
    assert dut._state == DeviceProtocolState.ReadyConnected

    dut.HandleActionItem(ComGen.Disconnect())

    # path 11
    assert dut._state == DeviceProtocolState.ReadyDisconnected

def test4():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))

    dut.HandleActionItem(ComGen.Connect())
    dut.HandleActionItem(ComGen.Receive(Packet([Section(SectionTypes.Enumerate)]).Encode()))

    # path 16
    assert dut._state == DeviceProtocolState.NotReadyEnumerated

    dut.HandleActionItem(ComGen.Disconnect())

    # path 6
    assert dut._state == DeviceProtocolState.NotReadyDisconnected

def test5():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))
    res:list[ActionItem] = []

    res.extend(dut.HandleActionItem(ComGen.Connect()))
    res.extend(dut.HandleActionItem(ComGen.Receive(Packet([GetPropertySection(0)]).Encode())))

    # path 17
    assert len(res) == 1
    assert res[0].target == "comm"
    assert res[0].action == Actions.ToCommTransmit
    decoded = Packet.Decode(res[0].params.data)
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.NotAllowed.value

def test6():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))

    dut.HandleActionItem(ComGen.Connect())
    dut.HandleActionItem(DevGen.Ready())

    # path 12
    assert dut._state == DeviceProtocolState.ReadyConnected

    dut.HandleActionItem(DevGen.Reset())

    # path 13
    assert dut._state == DeviceProtocolState.NotReadyConnected

def test7():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))
    res:list[ActionItem] = []

    dut.HandleActionItem(ComGen.Connect())
    dut.HandleActionItem(DevGen.Ready())

    res.extend(dut.HandleActionItem(ComGen.Receive(Packet([Section(SectionTypes.Enumerate)]).Encode())))

    # path 18
    assert len(res) == 1
    assert res[0].target == "comm"
    assert res[0].action == Actions.ToCommTransmit
    decoded = Packet.Decode(res[0].params.data)
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.Enumeration.value

    # path 20
    assert  dut._state == DeviceProtocolState.LinkEstablished

def test8():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))
    res:list[ActionItem] = []

    dut.HandleActionItem(ComGen.Connect())
    dut.HandleActionItem(DevGen.Ready())

    res.extend(dut.HandleActionItem(ComGen.Receive(Packet([GetPropertySection(0)]).Encode())))
        
    # path 19
    assert len(res) == 1
    assert res[0].target == "comm"
    assert res[0].action == Actions.ToCommTransmit
    decoded = Packet.Decode(res[0].params.data)
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.NotAllowed.value

def test9():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))
    res:list[ActionItem] = []
    
    res.extend(dut.HandleActionItem(ComGen.Connect()))
    res.extend(dut.HandleActionItem(ComGen.Receive(Packet([Section(SectionTypes.Enumerate)]).Encode())))
    res.extend(dut.HandleActionItem(ComGen.Receive(Packet([GetPropertySection(0)]).Encode())))

    # path 29
    assert len(res) == 1
    assert res[0].target == "comm"
    assert res[0].action == Actions.ToCommTransmit
    decoded = Packet.Decode(res[0].params.data)
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.NotAllowed.value

def test10():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))
    res:list[ActionItem] = []

    res.extend(dut.HandleActionItem(ComGen.Connect()))
    res.extend(dut.HandleActionItem(ComGen.Receive(Packet([Section(SectionTypes.Enumerate)]).Encode())))
    res.extend(dut.HandleActionItem(DevGen.Ready()))

    # path 30
    assert len(res) == 1
    assert res[0].target == "comm"
    assert res[0].action == Actions.ToCommTransmit
    decoded = Packet.Decode(res[0].params.data)
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.Enumeration.value

    # path 15
    assert dut._state == DeviceProtocolState.LinkEstablished

def test11():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))

    dut.HandleActionItem(ComGen.Connect())
    dut.HandleActionItem(DevGen.Ready())
    dut.HandleActionItem(ComGen.Receive(Packet([Section(SectionTypes.Enumerate)]).Encode()))
    dut.HandleActionItem(ComGen.Disconnect())

    # path 7
    assert dut._state == DeviceProtocolState.ReadyDisconnected

def test12():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))
    res:list[ActionItem] = []

    dut.HandleActionItem(ComGen.Connect())
    dut.HandleActionItem(DevGen.Ready())
    dut.HandleActionItem(ComGen.Receive(Packet([Section(SectionTypes.Enumerate)]).Encode()))

    res.extend(dut.HandleActionItem(ComGen.Receive(Packet([Section(SectionTypes.Reset)]).Encode())))

    # path 21

    assert len(res) == 1
    assert res[0].target == "device"
    assert res[0].action == Actions.ToDeviceReset

    res.extend(dut.HandleActionItem(DevGen.Reset()))

    # path 28
    assert len(res) == 2
    assert res[1].target == "comm"
    assert res[1].action == Actions.ToCommTransmit
    decoded = Packet.Decode(res[1].params.data)
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.Reset.value

    # path 14
    assert dut._state == DeviceProtocolState.NotReadyConnected

def test13():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))
    res:list[ActionItem] = []

    res.extend(dut.HandleActionItem(ComGen.Connect()))
    res.extend(dut.HandleActionItem(DevGen.DefineStream("test", DataTypes.uint32)))
    res.extend(dut.HandleActionItem(DevGen.Ready()))
    res.extend(dut.HandleActionItem(ComGen.Receive(Packet([Section(SectionTypes.Enumerate)]).Encode())))

    # path 1
    assert len(res) == 1
    assert res[0].target == "comm"
    assert res[0].action == Actions.ToCommTransmit
    decoded = Packet.Decode(res[0].params.data)
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.Enumeration.value
    assert len(decoded.sections[0].elements) == 1
    assert decoded.sections[0].elements[0].disposition == DispositionTypes.ClientToDeviceStream.value
    assert decoded.sections[0].elements[0].dataType == DataTypes.uint32.value
    assert decoded.sections[0].elements[0].name == "test"
    streamId = decoded.sections[0].elements[0].elementId

    res.extend(dut.HandleActionItem(ComGen.Receive(Packet([DataSection(SectionTypes.ClientToDeviceStream, streamId, b'\x00\x00\x00\x00',[])]).Encode())))

    # path 22
    assert len(res) == 3
    assert res[1].target == "device"
    assert res[1].action == Actions.ToDeviceStreamData
    assert res[1].params.name == "test"
    assert len(res[1].params.data) == 1
    assert res[1].params.data[0] == 0
    assert len(res[1].params.metadata) == 0

    # path 27
    assert res[2].target == "comm"
    assert res[2].action == Actions.ToCommTransmit
    decoded = Packet.Decode(res[2].params.data)
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.Confirmed.value

def test14():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))
    res:list[ActionItem] = []

    dut.HandleActionItem(ComGen.Connect())
    dut.HandleActionItem(DevGen.DefineStream("test", DataTypes.uint32))
    dut.HandleActionItem(DevGen.Ready())
    dut.HandleActionItem(ComGen.Receive(Packet([Section(SectionTypes.Enumerate)]).Encode()))

    res.extend(dut.HandleActionItem(ComGen.Receive(Packet([DataSection(SectionTypes.ClientToDeviceStream, 5, b'\x00\x00\x00\x00',[])]).Encode())))

    # path 22 negative
    # path 27
    assert len(res) == 1
    assert res[0].target == "comm"
    assert res[0].action == Actions.ToCommTransmit
    decoded = Packet.Decode(res[0].params.data)
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.NotAllowed.value

def test15():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))
    res:list[ActionItem] = []

    res.extend(dut.HandleActionItem(ComGen.Connect()))
    res.extend(dut.HandleActionItem(DevGen.DefineProperty("test", DataTypes.uint32)))
    res.extend(dut.HandleActionItem(DevGen.Ready()))
    res.extend(dut.HandleActionItem(ComGen.Receive(Packet([Section(SectionTypes.Enumerate)]).Encode())))

    # path 2
    assert len(res) == 1
    assert res[0].target == "comm"
    assert res[0].action == Actions.ToCommTransmit
    decoded = Packet.Decode(res[0].params.data)
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.Enumeration.value
    assert len(decoded.sections[0].elements) == 1
    assert decoded.sections[0].elements[0].disposition == DispositionTypes.EditableProperty.value
    assert decoded.sections[0].elements[0].dataType == DataTypes.uint32.value
    assert decoded.sections[0].elements[0].name == "test"
    propertyId = decoded.sections[0].elements[0].elementId

    res.extend(dut.HandleActionItem(ComGen.Receive(Packet([PropertyValueSection(SectionTypes.SetProperty, propertyId, b'\x00\x00\x00\xFF')]).Encode())))

    # path 23
    assert len(res) == 2
    assert res[1].target == "device"
    assert res[1].action == Actions.ToDeviceSetProperty
    assert res[1].params.name == "test"
    assert res[1].params.value == 255

def test16():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))
    res:list[ActionItem] = []

    res.extend(dut.HandleActionItem(ComGen.Connect()))
    res.extend(dut.HandleActionItem(DevGen.DefineProperty("test", DataTypes.uint32)))
    res.extend(dut.HandleActionItem(DevGen.Ready()))
    res.extend(dut.HandleActionItem(ComGen.Receive(Packet([Section(SectionTypes.Enumerate)]).Encode())))

    decoded = Packet.Decode(res[0].params.data)
    propertyId = decoded.sections[0].elements[0].elementId

    res.extend(dut.HandleActionItem(ComGen.Receive(Packet([GetPropertySection(propertyId)]).Encode())))

    # path 24
    assert len(res) == 2
    assert res[1].target == "device"
    assert res[1].action == Actions.ToDeviceGetProperty
    assert res[1].params.name == "test"

def test17():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))
    res:list[ActionItem] = []

    res.extend(dut.HandleActionItem(ComGen.Connect()))
    res.extend(dut.HandleActionItem(DevGen.DefineProperty("test", DataTypes.uint32)))
    res.extend(dut.HandleActionItem(DevGen.Ready()))
    res.extend(dut.HandleActionItem(ComGen.Receive(Packet([Section(SectionTypes.Enumerate)]).Encode())))

    decoded = Packet.Decode(res[0].params.data)
    propertyId = decoded.sections[0].elements[0].elementId

    res.extend(dut.HandleActionItem(DevGen.PropertyValue("test", 42)))

    # path 26
    assert len(res) == 2
    assert res[1].target == "comm"
    assert res[1].action == Actions.ToCommTransmit
    decoded = Packet.Decode(res[1].params.data)
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.NotifyProperty.value
    assert decoded.sections[0].elementId == propertyId
    assert len(decoded.sections[0].propertyValueBytes) == 4
    assert decoded.sections[0].propertyValueBytes[0] == 0
    assert decoded.sections[0].propertyValueBytes[1] == 0
    assert decoded.sections[0].propertyValueBytes[2] == 0
    assert decoded.sections[0].propertyValueBytes[3] == 42

def test18():
    dut = DeviceCoordinator()
    dut.HandleActionItem(DevGen.Start({}))
    res:list[ActionItem] = []

    res.extend(dut.HandleActionItem(ComGen.Connect()))
    res.extend(dut.HandleActionItem(DevGen.DefineStream("test", DataTypes.uint32, True)))
    res.extend(dut.HandleActionItem(DevGen.Ready()))
    res.extend(dut.HandleActionItem(ComGen.Receive(Packet([Section(SectionTypes.Enumerate)]).Encode())))
        
    decoded = Packet.Decode(res[0].params.data)
    streamId = decoded.sections[0].elements[0].elementId

    res.extend(dut.HandleActionItem(DevGen.StreamData("test", [0, 0, 4], {})))

    # path 25
    assert len(res) == 2
    assert res[1].target == "comm"
    assert res[1].action == Actions.ToCommTransmit
    decoded = Packet.Decode(res[1].params.data)
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.DeviceToClientStream.value
    assert decoded.sections[0].streamId == streamId
    assert len(decoded.sections[0].dataBytes) == 12
    assert decoded.sections[0].dataBytes[0] == 0
    assert decoded.sections[0].dataBytes[1] == 0
    assert decoded.sections[0].dataBytes[2] == 0
    assert decoded.sections[0].dataBytes[3] == 0
    assert decoded.sections[0].dataBytes[4] == 0
    assert decoded.sections[0].dataBytes[5] == 0
    assert decoded.sections[0].dataBytes[6] == 0
    assert decoded.sections[0].dataBytes[7] == 0
    assert decoded.sections[0].dataBytes[8] == 0
    assert decoded.sections[0].dataBytes[9] == 0
    assert decoded.sections[0].dataBytes[10] == 0
    assert decoded.sections[0].dataBytes[11] == 4