from sdrcat_protocol.network import *
from sdrcat_protocol.util import PrintHex
import pytest

def test_getNextChunkZeroOffset():
   provided_bytestream = b'\x00\x06\xDE\xAD\xBE\xEF\x00\x00'

   expected_bytestream = b'\x00\x06\xDE\xAD\xBE\xEF'
   received_bytestream = GetNextChunk(provided_bytestream, 0)

   assert received_bytestream == expected_bytestream

def test_getNextChunkNonZeroOffset():
   provided_bytestream = b'\x00\x00\x00\x06\xDE\xAD\xBE\xEF\x00\x00'

   expected_bytestream = b'\x00\x06\xDE\xAD\xBE\xEF'
   received_bytestream = GetNextChunk(provided_bytestream, 2)

   assert received_bytestream == expected_bytestream

def test_getNextChunkTooShortException():
   provided_bytestream = b'\x00\x06\xDE\xAD\xBE'

   with pytest.raises(Exception):
      received_bytestream = GetNextChunk(provided_bytestream)

def test_getNextChunkWayTooShortException():
   provided_bytestream = b'\x00'
   
   with pytest.raises(Exception):
      received_bytestream = GetNextChunk(provided_bytestream)

def test_verifyLength():
   bytestream = b'\x00\x06\xDE\xAD\xBE\xEF'
   length = VerifyLength(bytestream)
   assert length == 6

def test_verifyLength_IncorrectLength():
   bytestream = b'\x00\x06\xDE\xAD\xBE'
   
   with pytest.raises(Exception):
      VerifyLength(bytestream)

def test_verifyLength_WayTooShort():
   bytestream = b'\x00'
   
   with pytest.raises(Exception):
      VerifyLength(bytestream)

def test_decodeSection_enumerate():
   bytestream = bytes([0, 3, 0])
   s = DecodeSection(bytestream)

   assert s is not None
   assert isinstance(s, Section)
   assert s.sectionType == SectionTypes.Enumerate.value

def test_decodeSection_reset():
   bytestream = bytes([0, 3, 1])
   s = DecodeSection(bytestream)

   assert s is not None
   assert isinstance(s, Section)
   assert s.sectionType == SectionTypes.Reset.value

def test_decodeSection_notAllowed():
   bytestream = bytes([0, 3, 8])
   s = DecodeSection(bytestream)

   assert s is not None
   assert isinstance(s, Section)
   assert s.sectionType == SectionTypes.NotAllowed.value

def test_decodeSection_confirmed():
   bytestream = bytes([0, 3, 9])
   s = DecodeSection(bytestream)

   assert s is not None
   assert isinstance(s, Section)
   assert s.sectionType == SectionTypes.Confirmed.value

def test_decodeSection_getProperty():
   bytestream = bytes([0, 5, 2, 2, 0])
   s = DecodeSection(bytestream)

   assert s is not None
   assert isinstance(s, GetPropertySection)
   assert s.sectionType == SectionTypes.GetProperty.value

def test_decodeSection_setProperty():
   bytestream = bytes([0, 9, 3, 2, 0, 222, 173, 190, 239])
   s = DecodeSection(bytestream)

   assert s is not None
   assert isinstance(s, PropertyValueSection)
   assert s.sectionType == SectionTypes.SetProperty.value

def test_decodeSection_notifyProperty():
   bytestream = bytes([0, 9, 4, 2, 0, 222, 173, 190, 239])
   s = DecodeSection(bytestream)

   assert s is not None
   assert isinstance(s, PropertyValueSection)
   assert s.sectionType == SectionTypes.NotifyProperty.value

def test_decodeSection_clientToDeviceStream():
   bytestream = bytes([0, 38, 5, 0, 42, 0, 14, 0, 6, 0, 1, 0x73, 0x37, 0, 6, 0, 2, 0xDE, 0xAD, 0xFE, 0xED, 0xC0, 0xFF, 0xEE, 0x02, 0xDE, 0xAD, 0xBE, 0xEF, 0x04, 0x73, 0x37, 0x70, 0x75, 0x01, 0x02, 0x03, 0x04])
   s = DecodeSection(bytestream)

   assert s is not None
   assert isinstance(s, DataSection)
   assert s.sectionType == SectionTypes.ClientToDeviceStream.value

def test_decodeSection_deviceToClientStream():
   bytestream = bytes([0, 19, 6, 0, 43, 0, 8, 0, 6, 0, 3, 0xFE, 0xED, ord('c'), ord('o'), ord('f'), ord('f'), ord('e'), ord('e')])
   s = DecodeSection(bytestream)

   assert s is not None
   assert isinstance(s, DataSection)
   assert s.sectionType == SectionTypes.DeviceToClientStream.value

def test_decodeSection_enumeration():
   bytestream = bytes([0, 109, 7, 0, 0, 19, 0, 255, 0, 0, ord('t'), ord('e'), ord('s'), ord('t'), ord('.'), ord('p'), ord('a'), ord('r'), ord('a'), ord('m'), ord('2'), ord('5'), ord('5'), 
                       0, 19, 0, 42, 3, 1, ord('t'), ord('e'), ord('s'), ord('t'), ord('.'), ord('s'), ord('t'), ord('r'), ord('e'), ord('a'), ord('m'), ord('4'), ord('2'),
                       0, 19, 0, 43, 3, 9, ord('t'), ord('e'), ord('s'), ord('t'), ord('.'), ord('s'), ord('t'), ord('r'), ord('e'), ord('a'), ord('m'), ord('4'), ord('3'),
                       0, 16, 0, 1, 2, 0, ord('t'), ord('e'), ord('s'), ord('t'), ord('.'), ord('m'), ord('e'), ord('t'), ord('a'), ord('1'),
                       0, 16, 0, 2, 2, 0, ord('t'), ord('e'), ord('s'), ord('t'), ord('.'), ord('m'), ord('e'), ord('t'), ord('a'), ord('2'),
                       0, 16, 0, 3, 2, 0, ord('t'), ord('e'), ord('s'), ord('t'), ord('.'), ord('m'), ord('e'), ord('t'), ord('a'), ord('3')])

   s = DecodeSection(bytestream)

   assert s is not None
   assert isinstance(s, EnumerationSection)
   assert s.sectionType == SectionTypes.Enumeration.value

def test_streamReader_continuous():
   bytestream = bytes([0, 7, 0, 0, 0, 3, 1, 0, 7, 0, 0, 0, 3, 0])
   r = StreamReader()
   r.ProcessBytes(bytestream)

   p1 = r.GetNextPacket()
   p2 = r.GetNextPacket()
   p3 = r.GetNextPacket()

   assert p1 is not None
   assert isinstance(p1, Packet)
   assert len(p1.sections) == 1
   assert p1.sections[0].sectionType == 1

   assert p2 is not None
   assert isinstance(p2, Packet)
   assert len(p2.sections) == 1
   assert p2.sections[0].sectionType == 0

   assert p3 is None

def test_streamReader_multiple_packet_boundary():
   bytestream1 = bytes([0, 7, 0, 0, 0, 3, 1])
   bytestream2 = bytes([0, 7, 0, 0, 0, 3, 0])
   r = StreamReader()
   r.ProcessBytes(bytestream1)
   r.ProcessBytes(bytestream2)

   p1 = r.GetNextPacket()
   p2 = r.GetNextPacket()
   p3 = r.GetNextPacket()

   assert p1 is not None
   assert isinstance(p1, Packet)
   assert len(p1.sections) == 1
   assert p1.sections[0].sectionType == 1

   assert p2 is not None
   assert isinstance(p2, Packet)
   assert len(p2.sections) == 1
   assert p2.sections[0].sectionType == 0

   assert p3 is None

def test_streamReader_multiple_random_boundary():
   bytestream1 = bytes([0, 7, 0, 0, 0, 3, 1, 0, 7, 0])
   bytestream2 = bytes([0, 0, 3, 0])
   r = StreamReader()
   r.ProcessBytes(bytestream1)
   r.ProcessBytes(bytestream2)

   p1 = r.GetNextPacket()
   p2 = r.GetNextPacket()
   p3 = r.GetNextPacket()

   assert p1 is not None
   assert isinstance(p1, Packet)
   assert len(p1.sections) == 1
   assert p1.sections[0].sectionType == 1

   assert p2 is not None
   assert isinstance(p2, Packet)
   assert len(p2.sections) == 1
   assert p2.sections[0].sectionType == 0

   assert p3 is None

def test_section_encode():
   expected_bytestream = bytes([0,3,1])
   s = Section(SectionTypes.Reset)
   result_bytestream = s.Encode()

   assert result_bytestream == expected_bytestream

def test_section_decode():
   bytestream = bytes([0,3,0])

   s = Section.Decode(bytestream)
   
   assert s is not None
   assert s.sectionType == SectionTypes.Enumerate.value

def test_getPropertySection_encode():
   expected_bytestream = bytes([0,5,2,0,1])
   s = GetPropertySection(1)
   result_bytestream = s.Encode()

   assert result_bytestream == expected_bytestream

def test_getPropertySection_decode():
   bytestream = bytes([0,5,2,0,1])
   
   s = GetPropertySection.Decode(bytestream)

   assert s is not None
   assert s.sectionType == SectionTypes.GetProperty.value
   assert s.elementId == 1

def test_getPropertySection_decode_invalid_section():
   bytestream = bytes([0,5,6,0,1])
   
   with pytest.raises(Exception):
      GetPropertySection.Decode(bytestream)

def test_propertyValueSection_encode():
   expected_bytestream = bytes([0,7,3,0,1,222,173])
   s = PropertyValueSection(SectionTypes.SetProperty, 1, b'\xDE\xAD')
   result_bytestream = s.Encode()

   assert result_bytestream == expected_bytestream

def test_propertyValueSection_decode():
   bytestream = bytes([0,7,3,0,1,190,239])
   s = PropertyValueSection.Decode(bytestream)

   assert s is not None
   assert s.sectionType == 3
   assert s.elementId == 1
   assert s.propertyValueBytes == b'\xBE\xEF'

def test_propertyValueSection_decode_invalid_section():
   bytestream = bytes([0,7,6,0,1,255,255])
   with pytest.raises(Exception):
      PropertyValueSection.Decode(bytestream)

def test_dataSection_encode_no_meta():
   expected_bytestream = bytes([0,11,5,0,42,0,2,222,173,190,239])

   s = DataSection(SectionTypes.ClientToDeviceStream, 42, bytes([222,173,190,239]))
   result_bytestream = s.Encode()

   assert result_bytestream == expected_bytestream

def test_dataSection_decode_no_meta():
   bytestream = bytes([0,11,5,0,42,0,2,222,173,190,239])
   s = DataSection.Decode(bytestream)

   assert s is not None
   assert s.sectionType == SectionTypes.ClientToDeviceStream.value
   assert s.streamId == 42
   assert s.metadata is not None
   assert isinstance(s.metadata, list)
   assert len(s.metadata) == 0
   assert s.dataBytes == b'\xDE\xAD\xBE\xEF'

def test_dataSection_decode_invalid_section():
   bytestream = bytes([0,11,2,0,42,0,2,222,173,190,239])
   with pytest.raises(Exception):
      DataSection.Decode()

def test_metadataItem_encode():
   expected_bytestream = bytes([0,8,0,1,1,2,3,4])
   s = MetadataItem(1, b'\x01\x02\x03\x04')
   result_bytestream = s.Encode()

   assert result_bytestream == expected_bytestream

def test_metadataItem_decode():
   bytestream = bytes([0,8,0,1,1,2,3,4])
   s = MetadataItem.Decode(bytestream)

   assert s is not None
   assert s.metadataId == 1
   assert s.metadataValueBytes == b'\x01\x02\x03\x04'

def test_dataSection_encode_with_meta():
   expected_bytestream = bytes([0,36,6,0,42,0,27,0,5,0,1,254,0,5,0,2,237,0,5,0,3,192,0,5,0,4,255,0,5,0,5,238,222,173,190,239])

   m = []
   m.append(MetadataItem(1, b'\xFE'))
   m.append(MetadataItem(2, b'\xED'))
   m.append(MetadataItem(3, b'\xC0'))
   m.append(MetadataItem(4, b'\xFF'))
   m.append(MetadataItem(5, b'\xEE'))

   s = DataSection(SectionTypes.DeviceToClientStream, 42, bytes([222,173,190,239]), m)
   result_bytestream = s.Encode()

   assert result_bytestream == expected_bytestream

def test_dataSection_decode_with_meta():
   bytestream = bytes([0,36,6,0,42,0,27,0,5,0,1,254,0,5,0,2,237,0,5,0,3,192,0,5,0,4,255,0,5,0,5,238,222,173,190,239])
   s = DataSection.Decode(bytestream)

   assert s is not None
   assert s.sectionType == SectionTypes.DeviceToClientStream.value
   assert s.streamId == 42
   assert s.metadata is not None
   assert isinstance(s.metadata, list)
   assert len(s.metadata) == 5
   assert s.metadata[0].metadataId == 1
   assert s.metadata[0].metadataValueBytes == b'\xFE'
   assert s.metadata[1].metadataId == 2
   assert s.metadata[1].metadataValueBytes == b'\xED'
   assert s.metadata[2].metadataId == 3
   assert s.metadata[2].metadataValueBytes == b'\xC0'
   assert s.metadata[3].metadataId == 4
   assert s.metadata[3].metadataValueBytes == b'\xFF'
   assert s.metadata[4].metadataId == 5
   assert s.metadata[4].metadataValueBytes == b'\xEE'
   assert s.dataBytes == b'\xDE\xAD\xBE\xEF'

def test_elementDescription_encode():
   expected_bytestream = bytes([0,19,0,42,2,9,ord('t'),ord('e'),ord('s'),ord('t'),ord('.'),ord('t'),ord('e'),ord('s'),ord('t'),ord('p'),ord('r'),ord('o'),ord('p')])
   s = ElementDescription(42, DispositionTypes.Metadata, DataTypes.float32, "test.testprop")
   result_bytestream = s.Encode()

   assert result_bytestream == expected_bytestream

def test_elementDescription_decode():
   bytestream = bytes([0,19,0,42,2,9,ord('t'),ord('e'),ord('s'),ord('t'),ord('.'),ord('t'),ord('e'),ord('s'),ord('t'),ord('p'),ord('r'),ord('o'),ord('p')])
   s = ElementDescription.Decode(bytestream)

   assert s is not None
   assert s.elementId == 42
   assert s.disposition == DispositionTypes.Metadata.value
   assert s.dataType == DataTypes.float32.value
   assert s.name == "test.testprop"

@pytest.mark.parametrize("datatype, value, expected_encoding", [
   (DataTypes.raw, b'\xDE\xEA\xBE\xEF', b'\xDE\xEA\xBE\xEF'),
   (DataTypes.utf8, "test", b'test'),
   (DataTypes.uint8, 42, b'\x2A'),
   (DataTypes.sint8, -42, b'\xD6'),
   (DataTypes.uint16, 460, b'\x01\xCC'),
   (DataTypes.sint16, -460, b'\xFE\x34'),
   (DataTypes.uint32, 90005342, b'\x05\x5D\x5F\x5E'),
   (DataTypes.sint32, -90005342, b'\xFA\xA2\xA0\xA2'),
   (DataTypes.uint64, 100000000000000000, b'\x01\x63\x45\x78\x5D\x8A\x00\x00'),
   (DataTypes.sint64, -100000000000000000, b'\xFE\x9C\xBA\x87\xA2\x76\x00\x00'),
   (DataTypes.float32, 3.1415926536, b'\x40\x49\x0F\xDB'),
   (DataTypes.float64, 3.1415926536, b'\x40\x09\x21\xFB\x54\x44\x86\xE0'),
   (DataTypes.complex64, 3.1415926536 + 3.1415926536j, b'\x40\x49\x0F\xDB\x40\x49\x0F\xDB'),
   (DataTypes.complex128, 3.1415926536 + 3.1415926536j, b'\x40\x09\x21\xFB\x54\x44\x86\xE0\x40\x09\x21\xFB\x54\x44\x86\xE0')
])
def test_elementDescription_encodeValue(datatype, value, expected_encoding):
   s = ElementDescription(dataType=datatype)
   result_encoding = s.EncodeValue(value)
   assert result_encoding == expected_encoding

@pytest.mark.parametrize("datatype, expected_value, encoding", [
   (DataTypes.raw, b'\xDE\xEA\xBE\xEF', b'\xDE\xEA\xBE\xEF'),
   (DataTypes.utf8, "test", b'test'),
   (DataTypes.uint8, 42, b'\x2A'),
   (DataTypes.sint8, -42, b'\xD6'),
   (DataTypes.uint16, 460, b'\x01\xCC'),
   (DataTypes.sint16, -460, b'\xFE\x34'),
   (DataTypes.uint32, 90005342, b'\x05\x5D\x5F\x5E'),
   (DataTypes.sint32, -90005342, b'\xFA\xA2\xA0\xA2'),
   (DataTypes.uint64, 100000000000000000, b'\x01\x63\x45\x78\x5D\x8A\x00\x00'),
   (DataTypes.sint64, -100000000000000000, b'\xFE\x9C\xBA\x87\xA2\x76\x00\x00'),
   (DataTypes.float32, 3.1415926536, b'\x40\x49\x0F\xDB'),
   (DataTypes.float64, 3.1415926536, b'\x40\x09\x21\xFB\x54\x44\x86\xE0'),
   (DataTypes.complex64, 3.1415926536 + 3.1415926536j, b'\x40\x49\x0F\xDB\x40\x49\x0F\xDB'),
   (DataTypes.complex128, 3.1415926536 + 3.1415926536j, b'\x40\x09\x21\xFB\x54\x44\x86\xE0\x40\x09\x21\xFB\x54\x44\x86\xE0')
])
def test_elementDescription_decodeValue(datatype, expected_value, encoding):
   import math
   s = ElementDescription(dataType=datatype)
   result_value = s.DecodeValue(encoding)
   if datatype == DataTypes.float32:
      assert math.isclose(result_value, expected_value, rel_tol=0.000001)
   elif datatype == DataTypes.complex64:
      assert math.isclose(abs(result_value), abs(expected_value), rel_tol=0.000001)
   else:
      assert result_value == expected_value

@pytest.mark.parametrize("datatype, provided_stream, encoded_stream", [
   (DataTypes.raw, b'\x01\x02\x03\x04', b'\x01\x02\x03\x04'),
   (DataTypes.utf8, 'test', b'test'),
   (DataTypes.uint8, [1,2,3,4],      b'\x01\x02\x03\x04'),
   (DataTypes.sint8, [-1,-2,-3,-4],  b'\xFF\xFE\xFD\xFC'),
   (DataTypes.uint16, [1,2,3,4],     b'\x00\x01\x00\x02\x00\x03\x00\x04'),
   (DataTypes.sint16, [-1,-2,-3,-4], b'\xFF\xFF\xFF\xFE\xFF\xFD\xFF\xFC'),
   (DataTypes.uint32, [1,2,3,4],     b'\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00\x04'),
   (DataTypes.sint32, [-1,-2,-3,-4], b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFE\xFF\xFF\xFF\xFD\xFF\xFF\xFF\xFC'),
   (DataTypes.uint64, [1,2,3,4],     b'\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x04'),
   (DataTypes.sint64, [-1,-2,-3,-4], b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFE\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFD\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFC'),
   (DataTypes.float32, [1.10000002384185791015625, 1.2000000476837158203125, 1.2999999523162841796875, 1.39999997615814208984375], b'\x3F\x8C\xCC\xCD\x3F\x99\x99\x9A\x3F\xA6\x66\x66\x3F\xB3\x33\x33'),
   (DataTypes.float64, [1.100000000000000088817841970012523233890533447265625,1.1999999999999999555910790149937383830547332763671875,
                        1.3000000000000000444089209850062616169452667236328125,1.399999999999999911182158029987476766109466552734375],
                        b'\x3F\xF1\x99\x99\x99\x99\x99\x9A\x3F\xF3\x33\x33\x33\x33\x33\x33\x3F\xF4\xCC\xCC\xCC\xCC\xCC\xCD\x3F\xF6\x66\x66\x66\x66\x66\x66'),
   (DataTypes.complex64, [1.10000002384185791015625 + 1.2000000476837158203125j, 1.2999999523162841796875 + 1.39999997615814208984375j],b'\x3F\x8C\xCC\xCD\x3F\x99\x99\x9A\x3F\xA6\x66\x66\x3F\xB3\x33\x33'),
   (DataTypes.complex128, [1.100000000000000088817841970012523233890533447265625+1.1999999999999999555910790149937383830547332763671875j,
                        1.3000000000000000444089209850062616169452667236328125+1.399999999999999911182158029987476766109466552734375j],
                        b'\x3F\xF1\x99\x99\x99\x99\x99\x9A\x3F\xF3\x33\x33\x33\x33\x33\x33\x3F\xF4\xCC\xCC\xCC\xCC\xCC\xCD\x3F\xF6\x66\x66\x66\x66\x66\x66'),
])
def test_elementDescription_encodeStream(datatype, provided_stream, encoded_stream):
   s = ElementDescription(dataType=datatype)
   result_stream = s.EncodeStream(provided_stream)
   assert result_stream == encoded_stream

@pytest.mark.parametrize("datatype, expected_stream, encoded_stream", [
   (DataTypes.raw, b'\x01\x02\x03\x04', b'\x01\x02\x03\x04'),
   (DataTypes.utf8, 'test', b'test'),
   (DataTypes.uint8, [1,2,3,4],      b'\x01\x02\x03\x04'),
   (DataTypes.sint8, [-1,-2,-3,-4],  b'\xFF\xFE\xFD\xFC'),
   (DataTypes.uint16, [1,2,3,4],     b'\x00\x01\x00\x02\x00\x03\x00\x04'),
   (DataTypes.sint16, [-1,-2,-3,-4], b'\xFF\xFF\xFF\xFE\xFF\xFD\xFF\xFC'),
   (DataTypes.uint32, [1,2,3,4],     b'\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00\x04'),
   (DataTypes.sint32, [-1,-2,-3,-4], b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFE\xFF\xFF\xFF\xFD\xFF\xFF\xFF\xFC'),
   (DataTypes.uint64, [1,2,3,4],     b'\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x04'),
   (DataTypes.sint64, [-1,-2,-3,-4], b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFE\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFD\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFC'),
   (DataTypes.float32, [1.10000002384185791015625, 1.2000000476837158203125, 1.2999999523162841796875, 1.39999997615814208984375], b'\x3F\x8C\xCC\xCD\x3F\x99\x99\x9A\x3F\xA6\x66\x66\x3F\xB3\x33\x33'),
   (DataTypes.float64, [1.100000000000000088817841970012523233890533447265625,1.1999999999999999555910790149937383830547332763671875,
                        1.3000000000000000444089209850062616169452667236328125,1.399999999999999911182158029987476766109466552734375],
                        b'\x3F\xF1\x99\x99\x99\x99\x99\x9A\x3F\xF3\x33\x33\x33\x33\x33\x33\x3F\xF4\xCC\xCC\xCC\xCC\xCC\xCD\x3F\xF6\x66\x66\x66\x66\x66\x66'),
   (DataTypes.complex64, [1.10000002384185791015625 + 1.2000000476837158203125j, 1.2999999523162841796875 + 1.39999997615814208984375j],b'\x3F\x8C\xCC\xCD\x3F\x99\x99\x9A\x3F\xA6\x66\x66\x3F\xB3\x33\x33'),
   (DataTypes.complex128, [1.100000000000000088817841970012523233890533447265625+1.1999999999999999555910790149937383830547332763671875j,
                        1.3000000000000000444089209850062616169452667236328125+1.399999999999999911182158029987476766109466552734375j],
                        b'\x3F\xF1\x99\x99\x99\x99\x99\x9A\x3F\xF3\x33\x33\x33\x33\x33\x33\x3F\xF4\xCC\xCC\xCC\xCC\xCC\xCD\x3F\xF6\x66\x66\x66\x66\x66\x66'),
])
def test_elementDescription_decodeStream(datatype, expected_stream, encoded_stream):
   s = ElementDescription(dataType=datatype)
   result_stream = s.DecodeStream(encoded_stream)
   assert result_stream == expected_stream

def test_enumerationSection_encoding():
   expected_bytestream = bytes([0,36,7,1,0,16,0,42,2,9,ord('t'),ord('e'),ord('s'),ord('t'),ord('.'),ord('p'),ord('r'),ord('o'),ord('p'),ord('1'),0,16,0,43,0,1,ord('t'),ord('e'),ord('s'),ord('t'),ord('.'),ord('p'),ord('r'),ord('o'),ord('p'),ord('2')])
   s = EnumerationSection(1, [
      ElementDescription(42, DispositionTypes.Metadata, DataTypes.float32, name="test.prop1"),
      ElementDescription(43, DispositionTypes.EditableProperty, DataTypes.uint8, name="test.prop2")
   ])

   result_bytestream = s.Encode()

   assert result_bytestream == expected_bytestream

def test_enumerationSection_decoding():
   bytestream = bytes([0,36,7,1,0,16,0,42,2,9,ord('t'),ord('e'),ord('s'),ord('t'),ord('.'),ord('p'),ord('r'),ord('o'),ord('p'),ord('1'),0,16,0,43,0,1,ord('t'),ord('e'),ord('s'),ord('t'),ord('.'),ord('p'),ord('r'),ord('o'),ord('p'),ord('2')])
   s = EnumerationSection.Decode(bytestream)

   assert s is not None
   assert s.protocolVersion == 1
   assert len(s.elements) == 2
   assert s.elements[0].elementId == 42
   assert s.elements[0].disposition == DispositionTypes.Metadata.value
   assert s.elements[0].dataType == DataTypes.float32.value
   assert s.elements[0].name == "test.prop1"
   assert s.elements[1].elementId == 43
   assert s.elements[1].disposition == DispositionTypes.EditableProperty.value
   assert s.elements[1].dataType == DataTypes.uint8.value
   assert s.elements[1].name == "test.prop2"

def test_enumerationSection_getElementById():
   el1 = ElementDescription(42, DispositionTypes.Metadata, DataTypes.float32, name="test.prop1")
   el2 = ElementDescription(43, DispositionTypes.EditableProperty, DataTypes.uint8, name="test.prop2")
   s = EnumerationSection(1, [el1, el2])

   result = s.GetPropertyById(43)
   assert result == el2

def test_enumerationSection_getElementById_Fail():
   el1 = ElementDescription(42, DispositionTypes.Metadata, DataTypes.float32, name="test.prop1")
   el2 = ElementDescription(43, DispositionTypes.EditableProperty, DataTypes.uint8, name="test.prop2")
   s = EnumerationSection(1, [el1, el2])

   result = s.GetPropertyById(44)
   assert result is None

def test_enumerationSection_getElementByName():
   el1 = ElementDescription(42, DispositionTypes.Metadata, DataTypes.float32, name="test.prop1")
   el2 = ElementDescription(43, DispositionTypes.EditableProperty, DataTypes.uint8, name="test.prop2")
   s = EnumerationSection(1, [el1, el2])

   result = s.GetPropertyByName("test.prop2")
   assert result == el2

def test_enumerationSection_getElementByName_Fail():
   el1 = ElementDescription(42, DispositionTypes.Metadata, DataTypes.float32, name="test.prop1")
   el2 = ElementDescription(43, DispositionTypes.EditableProperty, DataTypes.uint8, name="test.prop2")
   s = EnumerationSection(1, [el1, el2])

   result = s.GetPropertyByName("test.prop3")
   assert result is None

def test_packet_encoding():
    p = Packet([Section(SectionTypes.Enumerate)])
    bytestream = p.Encode()

    assert bytestream == bytes([0, 7, 0, 0, 0, 3, 0])

def test_packet_decoding():
    bytestream = bytes([0, 212, 0, 0, # packet, it is 212 bytes long
                           0, 3, 0, # enumerate command, this section is 3 bytes long
                           0, 3, 1, # reset command, this section is 3 bytes long
                           0, 5, 2, 0, 255, # get param 255 command, this section is 5 bytes long
                           0, 9, 3, 0, 255, 0xDE, 0xAD, 0xBE, 0xEF, # set param 255 to 0xDEADBEEF, this section is 9 bytes long
                           0, 9, 4, 0, 255, 0xDE, 0xAD, 0xBE, 0xEF, # notify that current value of param 255 is 0xDEADBEEF, this section is 9 bytes long

                           0, 38, 5, 0, 42, # send data 0xFEEDC0FFEE02DEADBEEF047337707501020304 to stream id 42 with some metadata, this section is 38 bytes long
                              0, 14, # metadata collection, 14 bytes long
                                  0, 6, 0, 1, 0x73, 0x37,  # metadata id 1, value 0x7337, 6 bytes long
                                  0, 6, 0, 2, 0xDE, 0xAD,  # metadata id 2, value 0xDEAD, 6 bytes long
                              0xFE, 0xED, 0xC0, 0xFF, 0xEE, 0x02, 0xDE, 0xAD, 0xBE, 0xEF, 0x04, 0x73, 0x37, 0x70, 0x75, 0x01, 0x02, 0x03, 0x04,  # data

                           0, 19, 6, 0, 43, # receive data "coffee" from stream id 43 with some metadata, this section is 19 bytes long
                              0, 8, # metadata collection, 8 bytes long
                                 0, 6, 0, 3, 0xFE, 0xED, # metadata id  3, value 0xFEED, 6 bytes long
                              ord('c'), ord('o'), ord('f'), ord('f'), ord('e'), ord('e'), # data

                           0, 13, 6, 0, 43, # receive data "coffee" from stream id 43 with no metadata this time, this section is 13 bytes long
                              0, 2, # metadata collection, 2 bytes long
                              ord('c'), ord('o'), ord('f'), ord('f'), ord('e'), ord('e'), # data

                           0, 109, 7, 0, # enumeration, protocol version 0, this section is 105 bytes long
                              0, 19, 0, 255, 0, 0, ord('t'), ord('e'), ord('s'), ord('t'), ord('.'), ord('p'), ord('a'), ord('r'), ord('a'), ord('m'), ord('2'), ord('5'), ord('5'), # editable param called "test.param255", byte array, id 255
                              0, 19, 0, 42, 3, 1, ord('t'), ord('e'), ord('s'), ord('t'), ord('.'), ord('s'), ord('t'), ord('r'), ord('e'), ord('a'), ord('m'), ord('4'), ord('2'), # stream called "test.stream42", unsigned ints, id 42
                              0, 19, 0, 43, 3, 9, ord('t'), ord('e'), ord('s'), ord('t'), ord('.'), ord('s'), ord('t'), ord('r'), ord('e'), ord('a'), ord('m'), ord('4'), ord('3'), # stream called "test.stream43", floats, id 43
                              0, 16, 0, 1, 2, 0, ord('t'), ord('e'), ord('s'), ord('t'), ord('.'), ord('m'), ord('e'), ord('t'), ord('a'), ord('1'), # metadata called "test.meta1", byte array, id 1
                              0, 16, 0, 2, 2, 0, ord('t'), ord('e'), ord('s'), ord('t'), ord('.'), ord('m'), ord('e'), ord('t'), ord('a'), ord('2'), # metadata called "test.meta2", byte array, id 2
                              0, 16, 0, 3, 2, 0, ord('t'), ord('e'), ord('s'), ord('t'), ord('.'), ord('m'), ord('e'), ord('t'), ord('a'), ord('3') # metadata called "test.meta3", byte array, id 3
                        ])

    r = StreamReader()
    r.ProcessBytes(bytestream)
    p = r.GetNextPacket()
    
    assert p is not None

    recoded = p.Encode()

    assert recoded == bytestream