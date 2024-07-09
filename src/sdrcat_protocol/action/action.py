from collections import namedtuple

ActionItem = namedtuple("ActionItem", ["source", "target", "action", "params"], defaults=["", "", "", None])

DefineStreamParams = namedtuple("DefineStreamParams", ["name", "dataType", "isOutgoing"])
DefinePropertyParams = namedtuple("DefinePropertyParams", ["name", "dataType", "isReadOnly"])
DefineMetadataParams = namedtuple("DefineMetadataParams", ["name", "dataType"])
CommPayloadParams = namedtuple("CommPayloadParams", ["data"])
InformationParams = namedtuple("InformationParams", ["message"])
StateChangeParams = namedtuple("StateChangeParams", ["state"])
SetEnumerationParams = namedtuple("SetEnumerationParams", ["enumeration"])
DeviceInfoParams = namedtuple("DeviceInfoParams", ["deviceInfo"])
PropertyValueParams = namedtuple("PropertyValueParams", ["name", "value"])
PropertyParam = namedtuple("PropertyParam", ["name"])
StreamDataParams = namedtuple("StreamDataParams", ["name", "data", "metadata"])
CommConnectParams = namedtuple("CommConnectParams", ["connectionParams"])
AppendEnumerationParams = namedtuple("AppendEnumerationParams", ["elementDescription"])



