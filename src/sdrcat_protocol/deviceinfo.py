from sdrcat_protocol.definitions import DispositionTypes, DataTypes
from sdrcat_protocol.network import EnumerationSection

class DeviceInfo:
    def __init__(self, enumeration: EnumerationSection):
        self.elements : dict[str, DeviceElement] = {}

        for element in enumeration.elements:
            self.elements[element.name] = DeviceElement(element.disposition, element.dataType)

class DeviceElement:
    def __init__(self, disposition: int, dataType: int):
        self.disposition = DispositionTypes(disposition)
        self.dataType = DataTypes(dataType)