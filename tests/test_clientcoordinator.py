from sdrcat_protocol.coordinator import ClientCoordinator
from sdrcat_protocol.definitions import SectionTypes, DataTypes, DispositionTypes, ClientProtocolState
from sdrcat_protocol.network import Packet, Section, GetPropertySection, DataSection, PropertyValueSection, EnumerationSection, ElementDescription
from sdrcat_protocol.deviceinfo import DeviceInfo
from sdrcat_protocol.action import Actions, GenerateFromClient as CliGen, GenerateFromComm as ComGen

# TODO: Write tests involving sending/receiving streams with metadata



def test1():
    dut = ClientCoordinator()
    res:list[ActionItem] = []

    # verify initial state
    assert dut._state == ClientProtocolState.Disconnected

    res.extend(dut.ProcessAction(CliGen.Connect({"test": "value"})))

    # path 1
    assert len(res) == 1
    assert res[0].action == Actions.ToCommConnect
    assert len(res[0].params.connectionParams) == 1
    assert res[0].params.connectionParams["test"] == "value"
    
    res.extend(dut.ProcessAction(ComGen.Connect()))

    # path 3
    assert res[1].action == Actions.ToClientStatus
    assert res[1].params.state == ClientProtocolState.Enumerating

    # path 2
    assert len(res) == 3
    assert res[2].action == Actions.ToCommTransmit
    decoded = Packet.Decode(res[2].params.data)
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.Enumerate.value

    # path 4
    assert dut._state == ClientProtocolState.Enumerating

def test2():
    dut = ClientCoordinator()
    res:list[ActionItem] = []

    # setup
    dut.ProcessAction(ComGen.Connect())

    #test

    res.extend(dut.ProcessAction(CliGen.Disconnect()))

    # path 5
    assert len(res) == 1
    assert res[0].target == "comm"
    assert res[0].action == Actions.ToCommDisconnect

    res.extend(dut.ProcessAction(ComGen.Disconnect()))

    # path 6
    assert len(res) == 2
    assert res[1].target == "client"
    assert res[1].action == Actions.ToClientStatus
    assert res[1].params.state == ClientProtocolState.Disconnected

    # path 7
    assert dut._state == ClientProtocolState.Disconnected

def test3():
    dut = ClientCoordinator()
    res:list[ActionItem] = []

    # setup
    dut.ProcessAction(ComGen.Connect())
    
    # test

    enumeration = EnumerationSection(0, [ElementDescription(5, DispositionTypes.EditableProperty, DataTypes.uint32, "test")])
    res.extend(dut.ProcessAction(ComGen.Receive(Packet([enumeration]).Encode())))

    # path 8

    assert len(res) == 2
    assert res[0].target == "client"
    assert res[0].action == Actions.ToClientDeviceInfo
    assert res[0].params.deviceInfo.elements["test"].dataType == DataTypes.uint32.value
    assert res[0].params.deviceInfo.elements["test"].disposition == DispositionTypes.EditableProperty.value

    # path 10
    assert res[1].target == "client"
    assert res[1].action == Actions.ToClientStatus
    assert res[1].params.state == ClientProtocolState.LinkEstablished

    # path 11
    assert dut._state == ClientProtocolState.LinkEstablished

def test4():
    client = MockClient()
    comm = MockComm()
    dut = ClientCoordinator(client, comm)

    # setup
    comm.OnConnected()
    comm.OnReceive(Packet([EnumerationSection(0, [ElementDescription(5, DispositionTypes.EditableProperty, DataTypes.uint32, "test")])]).Encode())
    comm.ClearCalls()
    client.ClearCalls()

    # test

    client.Disconnect()

    # path 23
    assert len(comm.calls) == 1
    assert comm.calls[0][0] == "Disconnect"

    comm.OnDisconnected()

    # path 12
    assert len(client.calls) == 1
    assert client.calls[0][0] == "OnStatusChange"
    assert client.calls[0][1] == ProtocolState.Disconnected

    # path 20
    assert dut.state == ProtocolState.Disconnected

def test5():
    client = MockClient()
    comm = MockComm()
    dut = ClientCoordinator(client, comm)

    # setup
    comm.OnConnected()
    comm.OnReceive(Packet([EnumerationSection(0, [ElementDescription(5, DispositionTypes.EditableProperty, DataTypes.uint32, "test")])]).Encode())
    comm.ClearCalls()
    client.ClearCalls()

    # test

    client.Reset()

    # path 13
    assert len(comm.calls) == 1
    assert comm.calls[0][0] == "Transmit"
    decoded = Packet.Decode(comm.calls[0][1])
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.Reset.value

def test6():
    client = MockClient()
    comm = MockComm()
    dut = ClientCoordinator(client, comm)

    # setup
    comm.OnConnected()
    comm.OnReceive(Packet([EnumerationSection(0, [ElementDescription(5, DispositionTypes.EditableProperty, DataTypes.uint32, "test")])]).Encode())
    comm.ClearCalls()
    client.ClearCalls()

    # test

    client.GetPropertyValue("test")

    # path 14
    assert len(comm.calls) == 1
    assert comm.calls[0][0] == "Transmit"
    decoded = Packet.Decode(comm.calls[0][1])
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.GetProperty.value
    assert decoded.sections[0].elementId == 5

def test7():
    client = MockClient()
    comm = MockComm()
    dut = ClientCoordinator(client, comm)

    # setup
    comm.OnConnected()
    comm.OnReceive(Packet([EnumerationSection(0, [ElementDescription(5, DispositionTypes.EditableProperty, DataTypes.uint32, "test")])]).Encode())
    comm.ClearCalls()
    client.ClearCalls()

    # test

    client.SetPropertyValue("test", 42)

    # path 15
    assert len(comm.calls) == 1
    assert comm.calls[0][0] == "Transmit"
    decoded = Packet.Decode(comm.calls[0][1])
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.SetProperty.value
    assert decoded.sections[0].elementId == 5
    assert decoded.sections[0].propertyValueBytes == b'\x00\x00\x00\x2A'

def test8():
    client = MockClient()
    comm = MockComm()
    dut = ClientCoordinator(client, comm)

    # setup
    comm.OnConnected()
    comm.OnReceive(Packet([EnumerationSection(0, [ElementDescription(5, DispositionTypes.ClientToDeviceStream, DataTypes.uint32, "test")])]).Encode())
    comm.ClearCalls()
    client.ClearCalls()

    # test

    client.SendDataToDevice("test", [1, 2, 3], {})

    # path 16
    assert len(comm.calls) == 1
    assert comm.calls[0][0] == "Transmit"
    decoded = Packet.Decode(comm.calls[0][1])
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.ClientToDeviceStream.value
    assert decoded.sections[0].streamId == 5
    assert decoded.sections[0].dataBytes == b'\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03'

def test9():
    client = MockClient()
    comm = MockComm()
    dut = ClientCoordinator(client, comm)

    # setup
    comm.OnConnected()
    comm.OnReceive(Packet([EnumerationSection(0, [ElementDescription(5, DispositionTypes.ClientToDeviceStream, DataTypes.uint32, "test")])]).Encode())
    comm.ClearCalls()
    client.ClearCalls()
    
    # test

    comm.OnReceive(Packet([Section(SectionTypes.Reset)]).Encode())

    # path 17
    assert len(comm.calls) == 1
    assert comm.calls[0][0] == "Transmit"
    decoded = Packet.Decode(comm.calls[0][1])
    assert len(decoded.sections) == 1
    assert decoded.sections[0].sectionType == SectionTypes.Enumerate.value

    # path 21
    assert len(client.calls) == 1
    assert client.calls[0][0] == "OnStatusChange"
    assert client.calls[0][1] == ProtocolState.Enumerating
    
    # path 22
    assert dut.state == ProtocolState.Enumerating

def test10():
    client = MockClient()
    comm = MockComm()
    dut = ClientCoordinator(client, comm)

    # setup
    comm.OnConnected()
    comm.OnReceive(Packet([EnumerationSection(0, [ElementDescription(5, DispositionTypes.EditableProperty, DataTypes.uint32, "test")])]).Encode())
    comm.ClearCalls()
    client.ClearCalls()
    
    # test

    comm.OnReceive(Packet([PropertyValueSection(SectionTypes.NotifyProperty, 5, b'\x00\x00\x00\x2a')]).Encode())

    # path 18
    assert len(client.calls) == 1
    assert client.calls[0][0] == "OnPropertyValueReported"
    assert client.calls[0][1] == "test"
    assert client.calls[0][2] == 42

def test11():
    client = MockClient()
    comm = MockComm()
    dut = ClientCoordinator(client, comm)

    # setup
    comm.OnConnected()
    comm.OnReceive(Packet([EnumerationSection(0, [ElementDescription(5, DispositionTypes.DeviceToClientStream, DataTypes.uint32, "test")])]).Encode())
    comm.ClearCalls()
    client.ClearCalls()
    
    # test

    comm.OnReceive(Packet([DataSection(SectionTypes.DeviceToClientStream, 5, b'\x00\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00\x06', [])]).Encode())

    # path 19
    assert len(client.calls) == 1
    assert client.calls[0][0] == "OnDataReceivedFromDevice"
    assert client.calls[0][1] == "test"
    assert len(client.calls[0][2]) == 3
    assert client.calls[0][2][0] == 4
    assert client.calls[0][2][1] == 5
    assert client.calls[0][2][2] == 6