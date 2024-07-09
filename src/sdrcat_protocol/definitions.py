from enum import IntEnum

class SectionTypes(IntEnum):
    Reset = 0x01                   # either->either
         
    Confirmed = 0x09               # device->client
    NotAllowed = 0x08              # device->client
    Enumeration = 0x07             # device->client
    NotifyProperty = 0x04          # device->client
    DeviceToClientStream = 0x06    # device->client
         
    Enumerate = 0x00               # client->device
    GetProperty = 0x02             # client->device
    SetProperty = 0x03             # client->device
    ClientToDeviceStream = 0x05    # client->device



class DataTypes(IntEnum):
    raw = 0x00
    uint8 = 0x01
    sint8 = 0x02
    uint16 = 0x03
    sint16 = 0x04
    uint32 = 0x05
    sint32 = 0x06
    uint64 = 0x07
    sint64 = 0x08
    float32 = 0x09
    float64 = 0x0A
    complex64 = 0x0B
    complex128 = 0x0C
    utf8 = 0x0D

class DispositionTypes(IntEnum):
    EditableProperty = 0x00
    ReadonlyProperty = 0x01
    Metadata = 0x02
    ClientToDeviceStream = 0x03
    DeviceToClientStream = 0x04

class DeviceProtocolState:
    Startup = -1
    NotReadyDisconnected = 0
    NotReadyConnected = 1
    NotReadyEnumerated = 2
    ReadyDisconnected = 3
    ReadyConnected = 4
    LinkEstablished = 5

class ClientProtocolState:
    Disconnected = 0
    Enumerating = 1
    LinkEstablished = 2
    


