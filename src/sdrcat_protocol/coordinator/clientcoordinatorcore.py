from sdrcat_protocol.definitions import DataTypes, DispositionTypes, SectionTypes, ClientProtocolState
from sdrcat_protocol.network import *
from sdrcat_protocol.action import ActionItem, GenerateFromClientCoordinator as Generate
from sdrcat_protocol.deviceinfo import DeviceInfo

def ClientGettingPropertyValue(currentState:int, currentEnumeration:EnumerationSection, propertyName:str) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information(f"Sending GetProperty for '{propertyName}'"))

    if currentState != ClientProtocolState.LinkEstablished:
        actions.append(Generate.Information("Link is not established. Aborting."))
        return actions

    element = currentEnumeration.GetPropertyByName(propertyName)
    if element is None or (element.disposition != DispositionTypes.EditableProperty.value and element.disposition != DispositionTypes.ReadonlyProperty.value):
        actions.append(Generate.Information("Property with that name has not been defined. Aborting."))
        return actions

    actions.append(Generate.CommTransmit(Packet([GetPropertySection(element.elementId)]).Encode()))
    return actions


def ClientSettingPropertyValue(currentState:int, currentEnumeration:EnumerationSection, propertyName:str, value) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information(f"Sending SetProperty for {propertyName}"))

    if currentState != ClientProtocolState.LinkEstablished:
        actions.append(Generate.Information("Link is not established. Aborting."))
        return actions

    element = currentEnumeration.GetPropertyByName(propertyName)
    encodedValue = element.EncodeValue(value)
    if element is None or element.disposition != DispositionTypes.EditableProperty.value:
        actions.append(Generate.Information("Editable property with that name has not been defined. Aborting."))
        return actions

    actions.append(Generate.CommTransmit(Packet([PropertyValueSection(SectionTypes.SetProperty, element.elementId, encodedValue)]).Encode()))
    return actions


def ClientSendingDataToDevice(currentState:int, currentEnumeration:EnumerationSection, streamName, data, metadata) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information(f"Sending data through stream {streamName}"))

    if currentState != ClientProtocolState.LinkEstablished:
        actions.append(Generate.Information("Link is not established. Aborting."))
        return actions

    element = currentEnumeration.GetPropertyByName(streamName)
    if element is None or element.disposition != DispositionTypes.ClientToDeviceStream.value:
        actions.append(Generate.Information("Stream name is invalid. Aborting."))
        return actions

    encodedMetadata = []
    for k in metadata:
        metaElement = currentEnumeration.GetPropertyByName(k)
        if metaElement is None or metaElement.disposition != DispositionTypes.Metadata.value:
            actions.append(Generate.Information(f"Supplied metadata with name {k} has not been defined. Ignoring."))
            continue

        item = MetadataItem(metaElement.metadataId, metaElement.EncodeValue(metadata[k]))
        encodedMetadata.append(item)

    section = DataSection(SectionTypes.ClientToDeviceStream, element.elementId, element.EncodeStream(data), encodedMetadata)
    actions.append(Generate.CommTransmit(Packet([section]).Encode()))
    return actions


def ClientResetting(currentState:int) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information("Requesting reset."))

    if currentState != ClientProtocolState.LinkEstablished:
        actions.append(Generate.Information("Link is not established. Aborting."))
        return actions

    actions.append(Generate.CommTransmit(Packet([Section(SectionTypes.Reset)]).Encode()))
    return actions


def CommConnectiong(currentState:int) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information("Connecting."))

    if currentState == ClientProtocolState.Disconnected:
        actions.append(Generate.Information("Changing state to Enumerating."))
        actions.append(Generate.ChangeState(ClientProtocolState.Enumerating))
        actions.append(Generate.ClientStatus(ClientProtocolState.Enumerating))

        actions.append(Generate.Information("Sending Enumerate."))
        actions.append(Generate.CommTransmit(Packet([Section(SectionTypes.Enumerate)]).Encode()))

    return actions


def CommDisconnecting(currentState:int) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information("Disconnecting."))

    if currentState == ClientProtocolState.Enumerating or currentState == ClientProtocolState.LinkEstablished:
        actions.append(Generate.Information("Changing state to Disconnected."))
        actions.append(Generate.ChangeState(ClientProtocolState.Disconnected))
        actions.append(Generate.ClientStatus(ClientProtocolState.Disconnected))
        actions.append(Generate.ClearEnumeration())

    return actions


def ClientConnecting(currentState:int, params: dict) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information("Requesting connection"))

    if currentState == ClientProtocolState.Disconnected:
        actions.append(Generate.CommConnect(params))

    return actions


def ClientDisconnecting(currentState:int) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information("Requesting disconnection"))

    if currentState == ClientProtocolState.Enumerating or currentState == ClientProtocolState.LinkEstablished:
        actions.append(Generate.CommDisconnect())

    return actions


def CommReceivingData(currentState:int, currentEnumeration:EnumerationSection, reader:StreamReader, data) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information("Receiving data."))

    reader.ProcessBytes(data)

    while True:
        packet:Packet = reader.GetNextPacket()
        if packet is None:
            break
        
        if len(packet.sections) != 1:
            actions.append(Generate.Information("Packet does not have exactly one section. This is not supported. Ignoring packet."))
            continue

        section = packet.sections[0]

        actions.append(Generate.Information(f"Received {SectionTypes(section.sectionType).name}."))
        
        if currentState == ClientProtocolState.Enumerating:
            if section.sectionType == SectionTypes.Enumeration.value:
                actions.append(Generate.SetEnumeration(section))

                actions.append(Generate.Information("Forwarding DeviceInfo."))
                actions.append(Generate.ClientDeviceInfo(DeviceInfo(section)))

                actions.append(Generate.Information("Changing state to LinkEstablished."))
                actions.append(Generate.ChangeState(ClientProtocolState.LinkEstablished))
                actions.append(Generate.ClientStatus(ClientProtocolState.LinkEstablished))
            
            else:
                actions.append(Generate.Information("Ignoring packet."))

        elif currentState == ClientProtocolState.LinkEstablished:
            if section.sectionType == SectionTypes.NotAllowed.value:
                pass

            elif section.sectionType == SectionTypes.Confirmed.value:
                pass
                
            elif section.sectionType == SectionTypes.NotifyProperty.value:
                element = currentEnumeration.GetPropertyById(section.elementId)
                if element is None or (element.disposition != DispositionTypes.ReadonlyProperty.value and element.disposition != DispositionTypes.EditableProperty.value):
                    actions.append(Generate.Information("Referenced element does not exist or is not ReadonlyProperty or Editable Property. Aborting packet."))
                    continue
                
                actions.append(Generate.Information("Forwarding property value."))
                actions.append(Generate.ClientPropertyValue(element.name, element.DecodeValue(section.propertyValueBytes)))

            elif section.sectionType == SectionTypes.DeviceToClientStream.value:
                element = currentEnumeration.GetPropertyById(section.streamId)
                if element is None or element.disposition != DispositionTypes.DeviceToClientStream.value:
                    actions.append(Generate.Information("Referenced stream does not exist or is not DeviceToClientStream. Aborting packet."))
                    continue

                metadata = {}
                metadataOk = True
                for m in section.metadata:
                    metaElement = currentEnumeration.GetPropertyById(m.metadataId)
                    if metaElement is None or metaElement.disposition != DispositionTypes.Metadata:
                        metadataOk = False
                        break

                    metadata[metaElement.name] = metaElement.DecodeValue(m.metadataValueBytes)

                if not metadataOk:
                    actions.append(Generate.Information("Encountered at least one metadata element with an invalid ID. Aborting packet."))
                    continue
                
                decodedData = element.DecodeStream(section.dataBytes)

                actions.append(Generate.Information("Forwarding data stream."))
                actions.append(Generate.ClientStreamData(element.name, decodedData, metadata))

            elif section.sectionType == SectionTypes.Reset.value:
                actions.append(Generate.Information("Changing state to Enumerating."))
                actions.append(Generate.ChangeState(ClientProtocolState.Enumerating))
                actions.append(Generate.ClientStatus(ClientProtocolState.Enumerating))
                actions.append(Generate.ClearEnumeration())

                actions.append(Generate.Information("Sending Enumerate."))
                actions.append(Generate.CommTransmit(Packet([Section(SectionTypes.Enumerate)]).Encode()))

    return actions