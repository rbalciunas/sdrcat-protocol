from __future__ import annotations
from sdrcat_protocol.definitions import DataTypes, SectionTypes, DispositionTypes
import struct

def GetNextChunk(bytestream: bytes, offset: int = 0) -> bytes:
    if len(bytestream) < offset + 2:
        raise Exception('Trying to read two bytes starting at position {} but but the byte stream is only {} bytes long'.format(offset, len(bytestream)))

    expectedLength = int.from_bytes(bytestream[offset : offset + 2], 'big')
    
    if len(bytestream) < offset + expectedLength:
        raise Exception("Trying to read {} bytes starting at position {} but the byte stream is only {} bytes long".format(expectedLength, offset, len(bytestream)))

    return bytestream[offset : offset + expectedLength]

def VerifyLength(bytstreamSection: bytes) -> int:
    if len(bytstreamSection) < 2:
        raise Exception("Invalid bytes: expecting at least two to define the length")

    expectedLength = int.from_bytes(bytstreamSection[:2], 'big')
    
    if len(bytstreamSection) < expectedLength:
        raise Exception("Invalid bytes: length of byte stream is different than expected")

    return expectedLength

def DecodeSection(data:bytes) -> Section:
    VerifyLength(data)
    sectionType = int.from_bytes(data[2:3], 'big')

    if sectionType == SectionTypes.Enumerate.value\
        or sectionType == SectionTypes.Reset.value\
        or sectionType == SectionTypes.NotAllowed.value\
        or sectionType == SectionTypes.Confirmed.value:
        return Section.Decode(data)

    elif sectionType == SectionTypes.GetProperty.value:
        return GetPropertySection.Decode(data)

    elif sectionType == SectionTypes.SetProperty.value\
        or sectionType == SectionTypes.NotifyProperty.value:
        return PropertyValueSection.Decode(data)

    elif sectionType == SectionTypes.ClientToDeviceStream.value\
        or sectionType == SectionTypes.DeviceToClientStream.value:
        return DataSection.Decode(data)

    elif sectionType == SectionTypes.Enumeration.value:
        return EnumerationSection.Decode(data)

    else:
        raise Exception("Unexpected section type {}".format(sectionType))

class StreamReader:
    def __init__(self):
        self._buffer = b''
        self._packets = []

    def ProcessBytes(self, bytestream:bytes):
        self._buffer += bytestream

        while len(self._buffer) > 2:
            expectedLength = int.from_bytes(self._buffer[:2], 'big')
            
            if len(self._buffer) < expectedLength:
                break

            p = Packet.Decode(self._buffer[:expectedLength])
            self._packets.append(p)
            self._buffer = self._buffer[expectedLength:]

    def GetNextPacket(self):
        if len(self._packets) == 0:
            return None

        return self._packets.pop(0)
        
class Packet:
    def __init__(self,
            sections:list[Section] = []):

        self.sections:list[Section] = sections.copy()

    def Encode(self) -> bytes:
        result = b''
        for s in self.sections:
            result += s.Encode()

        result = b'\x00\x00' + result # TODO: replace with CRC16 calculation of result

        result = (2 + len(result)).to_bytes(2, 'big') + result

        return result

    def Decode(data:bytes) -> Packet:
        expectedLength = VerifyLength(data)
        result = Packet()
        expectedCRC = data[2:4]
        i = 4 # start of sections
        while i < expectedLength:
            sectionData = GetNextChunk(data, i)
            result.sections.append(DecodeSection(sectionData))
            i += len(sectionData)
        
        # TODO: calculate and validate CRC
        return result

    def __repr__(self):
        return "[" + ", ".join(s.__repr__() for s in self.sections) + "]"

class Section:
    def __init__(self,
            sectionType: SectionTypes = SectionTypes.Enumerate):

        self.sectionType = sectionType.value

    def Encode(self) -> bytes:
        length = 3
        return length.to_bytes(2, 'big')\
            + self.sectionType.to_bytes(1, 'big')

    def Decode(data:bytes) -> Section:
        VerifyLength(data)

        result = Section()
        result.sectionType = int.from_bytes(data[2:3], 'big')

        return result

    def __repr__(self):
        if self.sectionType == SectionTypes.Enumerate.value: return "{Enumerate Cmd}"
        elif self.sectionType == SectionTypes.Reset.value: return "{Reset Cmd}"
        else: return "{Section}"

class GetPropertySection(Section):
    def __init__(self,
            elementId: int = 0):

        super().__init__(SectionTypes.GetProperty)

        self.elementId = elementId

    def Encode(self) -> bytes:
        length = 5
        return length.to_bytes(2, 'big')\
            + self.sectionType.to_bytes(1, 'big')\
            + self.elementId.to_bytes(2, 'big')

    def Decode(data:bytes) -> GetPropertySection:
        VerifyLength(data)

        result = GetPropertySection()
        result.sectionType = int.from_bytes(data[2:3], 'big')
        result.elementId = int.from_bytes(data[3:5], 'big')

        if result.sectionType != SectionTypes.GetProperty.value:
            raise Exception("Invalid section. Expecting section type to be {}, but was {}".format(SectionTypes.GetProperty.value, result.sectionType))

        return result

    def __repr__(self):
        return "{{Get Property {}}}".format(self.elementId)

class PropertyValueSection(Section):
    def __init__(self,
            sectionType: SectionTypes = SectionTypes.NotifyProperty,
            elementId:int = 0,
            propertyValueBytes:bytes = b''):

        super().__init__(sectionType)

        self.elementId = elementId
        self.propertyValueBytes = propertyValueBytes

    def Encode(self) -> bytes:
        return (len(self.propertyValueBytes) + 5).to_bytes(2, 'big')\
            + self.sectionType.to_bytes(1, 'big')\
            + self.elementId.to_bytes(2, 'big')\
            + self.propertyValueBytes

    def Decode(data:bytes) -> PropertyValueSection:
        VerifyLength(data)

        result = PropertyValueSection()
        result.sectionType = int.from_bytes(data[2:3], 'big')
        result.elementId = int.from_bytes(data[3:5], 'big')
        result.propertyValueBytes = data[5:]

        if result.sectionType != SectionTypes.SetProperty.value and result.sectionType != SectionTypes.NotifyProperty.value:
            raise Exception("Invalid section. Expecting section type to be {} or {}, but was {}".format(SectionTypes.SetProperty.value, SectionTypes.NotifyProperty.value, result.sectionType))

        return result

    def __repr__(self):
        if self.sectionType == SectionTypes.SetProperty.value:
            return "{{Set Property {}}}".format(self.elementId)
        elif self.sectionType == SectionTypes.NotifyProperty.value:
            return "{{Notify Property {}}}".format(self.elementId)
        else: return "{{Property Value Section}}"

class DataSection(Section):
    def __init__(self,
            sectionType:SectionTypes = SectionTypes.ClientToDeviceStream,
            streamId: int = 0,
            data: bytes = b'',
            metadata:list[MetadataItem] = []):

        super().__init__(sectionType)

        self.streamId = streamId
        self.dataBytes = data
        self.metadata = metadata.copy()

    def Encode(self) -> bytes:
        mresult = b''
        for m in self.metadata:
            mresult += m.Encode()
        
        result = self.sectionType.to_bytes(1, 'big')
        result += self.streamId.to_bytes(2, 'big')
        result += (2 + len(mresult)).to_bytes(2, 'big')
        result += mresult
        result +=  self.dataBytes

        result = (2 + len(result)).to_bytes(2, 'big') + result
        return result

    def Decode(bytestream: bytes) -> DataSection:
        VerifyLength(bytestream)
        result = DataSection()
        result.sectionType = int.from_bytes(bytestream[2:3], 'big')
        result.streamId = int.from_bytes(bytestream[3:5], 'big')

        if result.sectionType != SectionTypes.ClientToDeviceStream.value and result.sectionType != SectionTypes.DeviceToClientStream.value:
            raise Exception("Invalid section. Expecting section type to be {} or {}, but was {}".format(SectionTypes.ClientToDeviceStream.value, SectionTypes.DeviceToClientStream.value, result.sectionType))
        
        metadataChunk = GetNextChunk(bytestream, 5)
        expectedLength = VerifyLength(metadataChunk)
        i = 2
        while i < expectedLength:
            chunk = GetNextChunk(metadataChunk, i)
            result.metadata.append(MetadataItem.Decode(chunk))
            i += len(chunk)

        result.dataBytes = bytestream[5 + len(metadataChunk):]
        return result

    def __repr__(self):
        if self.sectionType == SectionTypes.ClientToDeviceStream.value:
            return "{{Client To Device Stream {}}}".format(self.streamId)
        elif self.sectionType == SectionTypes.DeviceToClientStream.value:
            return "{{Device To Client Stream {}}}".format(self.streamId)
        else:
            return "{{Stream?}}"

class EnumerationSection(Section):
    def __init__(self,
            protocolVersion: int = 0,
            elements:list[ElementDescription] = []):

        super().__init__(SectionTypes.Enumeration)

        self.protocolVersion = protocolVersion
        self.elements = elements.copy()

    def Encode(self) -> bytes:
        result = self.sectionType.to_bytes(1, 'big')
        result += self.protocolVersion.to_bytes(1, 'big')

        for p in self.elements:
            result += p.Encode()

        result = (len(result) + 2).to_bytes(2, 'big') + result
        return result

    def Decode(data:bytes) -> EnumerationSection:
        VerifyLength(data)

        result = EnumerationSection()
        result.sectionType = int.from_bytes(data[2:3], 'big')

        if result.sectionType != SectionTypes.Enumeration.value:
            raise Exception("Invalid section. Expecting section type to be 7, but was {}".format(self.sectionType))

        result.protocolVersion = int.from_bytes(data[3:4], 'big')
        i = 4
        while i < len(data):
            chunk = GetNextChunk(data, i)
            i += len(chunk)
            result.elements.append(ElementDescription.Decode(chunk))

        return result

    def GetPropertyByName(self, name: str) -> ElementDescription:
        for e in self.elements:
            if e.name == name:
                return e

        return None

    def GetPropertyById(self, id: int) -> ElementDescription:
        for e in self.elements:
            if e.elementId == id:
                return e

        return None

    def __repr__(self):
        return "{Enumeration}"

class ElementDescription:
    def __init__(self,
            elementId: int = 0,
            disposition: DispositionTypes = DispositionTypes.EditableProperty,
            dataType: DataTypes = DataTypes.uint8,
            name: str = ''):

        self.elementId = elementId
        self.disposition = disposition.value
        self.dataType = dataType.value
        self.name = name

    def Encode(self) -> bytes:
        length = 6 + len(self.name)
        return length.to_bytes(2, 'big')\
            + self.elementId.to_bytes(2, 'big')\
            + self.disposition.to_bytes(1, 'big')\
            + self.dataType.to_bytes(1, 'big')\
            + self.name.encode('utf-8')

    def Decode(data:bytes) -> ElementDescription:
        VerifyLength(data)

        result = ElementDescription()
        result.elementId = int.from_bytes(data[2:4], 'big')
        result.disposition = int.from_bytes(data[4:5], 'big')
        result.dataType = int.from_bytes(data[5:6], 'big')
        result.name = data[6:].decode('utf-8')

        return result

    def EncodeValue(self, value) -> bytes:
        if   self.dataType == DataTypes.raw.value and isinstance(value, bytes): return value
        elif self.dataType == DataTypes.utf8.value:       return str(value).encode('utf-8')
        elif self.dataType == DataTypes.sint8.value:      return int(value).to_bytes(1, 'big', signed=True)
        elif self.dataType == DataTypes.uint8.value:      return int(value).to_bytes(1, 'big', signed=False)
        elif self.dataType == DataTypes.sint16.value:     return int(value).to_bytes(2, 'big', signed=True)
        elif self.dataType == DataTypes.uint16.value:     return int(value).to_bytes(2, 'big', signed=False)
        elif self.dataType == DataTypes.sint32.value:     return int(value).to_bytes(4, 'big', signed=True)
        elif self.dataType == DataTypes.uint32.value:     return int(value).to_bytes(4, 'big', signed=False)
        elif self.dataType == DataTypes.sint64.value:     return int(value).to_bytes(8, 'big', signed=True)
        elif self.dataType == DataTypes.uint64.value:     return int(value).to_bytes(8, 'big', signed=False)
        elif self.dataType == DataTypes.float32.value:    return float(struct).pack(">f", value)
        elif self.dataType == DataTypes.float64.value:    return float(struct).pack(">d", value)
        elif self.dataType == DataTypes.complex64.value:  return complex(struct).pack(">ff", value.real, value.imag)
        elif self.dataType == DataTypes.complex128.value: return complex(struct).pack(">dd", value.real, value.imag)
        else: raise Exception("Either data type {} is not supported or the value passed is not compatible with that data type.".format(self.dataType))

    def EncodeStream(self, streamValues) -> bytes:
        if   self.dataType == DataTypes.raw.value        and isinstance(streamValues, bytes): return streamValues
        elif self.dataType == DataTypes.utf8.value       and isinstance(streamValues, str):  return streamValues.encode('utf-8') 
        elif self.dataType == DataTypes.sint8.value      and isinstance(streamValues, list): return struct.pack('>{}b'.format(len(streamValues)), *streamValues)
        elif self.dataType == DataTypes.uint8.value      and isinstance(streamValues, list): return struct.pack('>{}B'.format(len(streamValues)), *streamValues)
        elif self.dataType == DataTypes.sint16.value     and isinstance(streamValues, list): return struct.pack('>{}h'.format(len(streamValues)), *streamValues)
        elif self.dataType == DataTypes.uint16.value     and isinstance(streamValues, list): return struct.pack('>{}H'.format(len(streamValues)), *streamValues)
        elif self.dataType == DataTypes.sint32.value     and isinstance(streamValues, list): return struct.pack('>{}i'.format(len(streamValues)), *streamValues)
        elif self.dataType == DataTypes.uint32.value     and isinstance(streamValues, list): return struct.pack('>{}I'.format(len(streamValues)), *streamValues)
        elif self.dataType == DataTypes.sint64.value     and isinstance(streamValues, list): return struct.pack('>{}q'.format(len(streamValues)), *streamValues)
        elif self.dataType == DataTypes.uint64.value     and isinstance(streamValues, list): return struct.pack('>{}Q'.format(len(streamValues)), *streamValues)
        elif self.dataType == DataTypes.float32.value    and isinstance(streamValues, list): return struct.pack('>{}f'.format(len(streamValues)), *streamValues)
        elif self.dataType == DataTypes.float64.value    and isinstance(streamValues, list): return struct.pack('>{}d'.format(len(streamValues)), *streamValues)
        elif self.dataType == DataTypes.complex64.value  and isinstance(streamValues, list): return struct.pack('>{0}f{0}f'.format(len(streamValues)), *[f for c in streamValues for f in [c.real, c.imag]])
        elif self.dataType == DataTypes.complex128.value and isinstance(streamValues, list): return struct.pack('>{0}d{0}d'.format(len(streamValues)), *[f for c in streamValues for f in [c.real, c.imag]])
        else: raise Exception("Either data type {} is not supported or the value passed is not compatible with that data type.".format(self.dataType))
        
    def DecodeStream(self, streamBytes: bytes) -> any:
        if   self.dataType == DataTypes.raw.value:        return streamBytes
        elif self.dataType == DataTypes.utf8.value:       return streamBytes.decode('utf-8')
        elif self.dataType == DataTypes.sint8.value:      return [u[0] for u in struct.iter_unpack('>b', streamBytes)]
        elif self.dataType == DataTypes.uint8.value:      return [u[0] for u in struct.iter_unpack('>B', streamBytes)]
        elif self.dataType == DataTypes.sint16.value:     return [u[0] for u in struct.iter_unpack('>h', streamBytes)]
        elif self.dataType == DataTypes.uint16.value:     return [u[0] for u in struct.iter_unpack('>H', streamBytes)]
        elif self.dataType == DataTypes.sint32.value:     return [u[0] for u in struct.iter_unpack('>i', streamBytes)]
        elif self.dataType == DataTypes.uint32.value:     return [u[0] for u in struct.iter_unpack('>I', streamBytes)]
        elif self.dataType == DataTypes.sint64.value:     return [u[0] for u in struct.iter_unpack('>q', streamBytes)]
        elif self.dataType == DataTypes.uint64.value:     return [u[0] for u in struct.iter_unpack('>Q', streamBytes)]
        elif self.dataType == DataTypes.float32.value:    return [u[0] for u in struct.iter_unpack(">f", streamBytes)]
        elif self.dataType == DataTypes.float64.value:    return [u[0] for u in struct.iter_unpack(">d", streamBytes)]
        elif self.dataType == DataTypes.complex64.value:  return [complex(u[0], u[1]) for u in struct.iter_unpack(">ff", streamBytes)]
        elif self.dataType == DataTypes.complex128.value: return [complex(u[0], u[1]) for u in struct.iter_unpack(">dd", streamBytes)]
        else: raise Exception("Either data type {} is not supported or the value passed is not compatible with that data type.".format(self.dataType))

    def DecodeValue(self, valueBytes: bytes):
        if   self.dataType == DataTypes.raw.value:                              return valueBytes
        elif self.dataType == DataTypes.utf8.value:                             return valueBytes.decode('utf-8')
        elif self.dataType == DataTypes.sint8.value   and len(valueBytes) == 1: return int.from_bytes(valueBytes, 'big', signed=True)
        elif self.dataType == DataTypes.uint8.value   and len(valueBytes) == 1: return int.from_bytes(valueBytes, 'big', signed=False)
        elif self.dataType == DataTypes.sint16.value  and len(valueBytes) == 2: return int.from_bytes(valueBytes, 'big', signed=True)
        elif self.dataType == DataTypes.uint16.value  and len(valueBytes) == 2: return int.from_bytes(valueBytes, 'big', signed=False)
        elif self.dataType == DataTypes.sint32.value  and len(valueBytes) == 4: return int.from_bytes(valueBytes, 'big', signed=True)
        elif self.dataType == DataTypes.uint32.value  and len(valueBytes) == 4: return int.from_bytes(valueBytes, 'big', signed=False)
        elif self.dataType == DataTypes.sint64.value  and len(valueBytes) == 8: return int.from_bytes(valueBytes, 'big', signed=True)
        elif self.dataType == DataTypes.uint64.value  and len(valueBytes) == 8: return int.from_bytes(valueBytes, 'big', signed=False)
        elif self.dataType == DataTypes.float32.value and len(valueBytes) == 4: return struct.unpack('>f', valueBytes)[0]
        elif self.dataType == DataTypes.float64.value and len(valueBytes) == 8: return struct.unpack('>d', valueBytes)[0]
        elif self.dataType == DataTypes.complex64.value and len(valueBytes) == 8:
            unpacked = struct.unpack('>ff', valueBytes)
            return complex(unpacked[0], unpacked[1])
        elif self.dataType == DataTypes.complex128.value and len(valueBytes) == 16:
            unpacked = struct.unpack('>dd', valueBytes)
            return complex(unpacked[0], unpacked[1])
        else: raise Exception("Either data type {} is not supported or value byte length does not match the data type.".format(self.dataType))

    def __repr__(self):
        if self.disposition == DispositionTypes.EditableProperty.value:
            return "{{Editable Property '{}'}}".format(self.name)
        elif self.disposition == DispositionTypes.ReadonlyProperty.value:
            return "{{Readonly Property '{}'}}".format(self.name)
        elif self.disposition == DispositionTypes.Metadata.value:
            return "{{Metadata '{}'}}".format(self.name)
        elif self.disposition == DispositionTypes.ClientToDeviceStream.value:
            return "{{Stream (client -> device) '{}'}}".format(self.name)
        elif self.disposition == DispositionTypes.DeviceToClientStream.value:
            return "{{Stream (device -> client) '{}'}}".format(self.name)
        return "{{?}}"

class MetadataItem:
    def __init__(self,
            metadataId: int = 0,
            metadataValueBytes: bytes = b''):

        self.metadataId = metadataId
        self.metadataValueBytes = metadataValueBytes

    def Encode(self) -> bytes:
        return (4 + len(self.metadataValueBytes)).to_bytes(2, 'big')\
            + self.metadataId.to_bytes(2, 'big')\
            + self.metadataValueBytes

    def Decode(bytestream: bytes) -> MetadataItem:
        VerifyLength(bytestream)
        result = MetadataItem()
        result.metadataId = int.from_bytes(bytestream[2:4], 'big')
        result.metadataValueBytes = bytestream[4:]

        return result

    def __repr__(self):
        return "{{Metadata Id {}}}".format(self.metadataId)