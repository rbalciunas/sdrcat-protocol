from sdrcat_protocol.definitions import DataTypes, DispositionTypes, SectionTypes, DeviceProtocolState
from sdrcat_protocol.network import *
from sdrcat_protocol.action import ActionItem, GenerateFromDeviceCoordinator as Generate

def  DeviceReportingPropertyValue(currentState:int, currentEnumeration:EnumerationSection, propertyName:str, value) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information(f"Reporting value of property {propertyName}"))

    if currentState != DeviceProtocolState.LinkEstablished:
        actions.append(Generate.Information("Link is not established. Aborting."))
        return actions

    element = currentEnumeration.GetPropertyByName(propertyName)
    if element is None or (element.disposition != DispositionTypes.EditableProperty.value and element.disposition != DispositionTypes.ReadonlyProperty.value):
        actions.append(Generate.Information("No such property has been defined. Aborting."))
        return actions

    section = PropertyValueSection(SectionTypes.NotifyProperty, element.elementId, element.EncodeValue(value))
    actions.append(Generate.CommTransmit(Packet([section]).Encode()))
    return actions


def DeviceSendingDataToClient(currentState:int, currentEnumeration:EnumerationSection, streamName: str, data: any, metadata: dict) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information(f"Sending data through stream {streamName}"))

    if currentState != DeviceProtocolState.LinkEstablished:
        actions.append(Generate.Information("Link is not established. Aborting."))
        return actions

    element = currentEnumeration.GetPropertyByName(streamName)
    if element is None or element.disposition != DispositionTypes.DeviceToClientStream.value:
        actions.append(Generate.Information("Stream name is invalid. Aborting."))
        return actions

    encodedMetadata = []
    if metadata is not None:
        for k in metadata:
            metaElement = currentEnumeration.GetPropertyByName(k)
            if metaElement is None or metaElement.disposition != DispositionTypes.Metadata:
                actions.append(Generate.Information(f"Supplied metadata with name {k} has not been defined. Ignoring."))
                continue

            item = MetadataItem(metaElement.metadataId, metaElement.EncodeValue(metadata[k]))
            encodedMetadata.append(item)

    section = DataSection(SectionTypes.DeviceToClientStream, element.elementId, element.EncodeStream(data), encodedMetadata)
    actions.append(Generate.CommTransmit(Packet([section]).Encode()))
    return actions

def  DeviceStarting(currentState:int, connectionParams:dict[str,any]) -> list[ActionItem]:
    actions = []

    if currentState == DeviceProtocolState.Startup:
        actions.append(Generate.Information("Device Starting."))
        actions.append(Generate.DeviceReset())
        actions.append(Generate.ChangeState(DeviceProtocolState.NotReadyDisconnected))
        actions.append(Generate.CommConnect(connectionParams))

    return actions

def  DeviceReadying(currentState:int, currentEnumeration:EnumerationSection) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information("Device Readying."))

    if currentState == DeviceProtocolState.NotReadyDisconnected:
        actions.append(Generate.Information("Changing state to ReadyDisconnected."))
        actions.append(Generate.ChangeState(DeviceProtocolState.ReadyDisconnected))

    elif currentState == DeviceProtocolState.NotReadyConnected:
        actions.append(Generate.Information("Changing state to ReadyConnected"))
        actions.append(Generate.ChangeState(DeviceProtocolState.ReadyConnected))

    elif currentState == DeviceProtocolState.NotReadyEnumerated:
        actions.append(Generate.Information("Changing state to LinkEstablished."))
        actions.append(Generate.ChangeState(DeviceProtocolState.LinkEstablished))
        actions.append(Generate.Information("Sending enumeration."))
        actions.append(Generate.CommTransmit(Packet([currentEnumeration]).Encode()))

    return actions

def DeviceResetting(currentState:int) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information("Device Resetting."))
    
    if currentState == DeviceProtocolState.ReadyDisconnected:
        actions.append(Generate.Information("Changing state to NotReadyDisconnected"))
        actions.append(Generate.ChangeState(DeviceProtocolState.NotReadyDisconnected))
        actions.append(Generate.ClearEnumeration())
        actions.append(Generate.ResetNextElementId())

    elif currentState == DeviceProtocolState.ReadyConnected:
        actions.append(Generate.Information("Changing state to NotReadyConnected."))
        actions.append(Generate.ChangeState(DeviceProtocolState.NotReadyConnected))
        actions.append(Generate.ClearEnumeration())
        actions.append(Generate.ResetNextElementId())

    elif currentState == DeviceProtocolState.LinkEstablished:
        actions.append(Generate.Information("Changing state to NotReadyConnected."))
        actions.append(Generate.ChangeState(DeviceProtocolState.NotReadyConnected))
        actions.append(Generate.ClearEnumeration())
        actions.append(Generate.ResetNextElementId())

        actions.append(Generate.Information("Sending reset notification."))
        actions.append(Generate.CommTransmit(Packet([Section(SectionTypes.Reset)]).Encode()))

    return actions

def DeviceDefiningAvailableProperty(currentState:int, nextElementId:int, propertyName: str, propertyType: DataTypes, readOnly: bool = False) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information(f"Defining Property '{propertyName}', type {propertyType}, read only = {readOnly}"))

    if currentState != DeviceProtocolState.NotReadyDisconnected and currentState != DeviceProtocolState.NotReadyConnected and currentState != DeviceProtocolState.NotReadyEnumerated:
        actions.append(Generate.Information("Device is already in 'ready' status. Aborting"))
        return actions
        
    el = ElementDescription()
    el.disposition = DispositionTypes.ReadonlyProperty.value if readOnly else DispositionTypes.EditableProperty.value
    el.elementId = nextElementId
    actions.append(Generate.IncrementNextElementId())
    el.dataType = propertyType.value
    el.name = propertyName

    actions.append(Generate.AppendEnumeration(el))
    return actions

def DeviceDefiningAvailableMetadata(currentState:int, nextElementId:int, metadataName: str, metadataType: DataTypes) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information(f"Defining Metadata '{metadataName}', type {metadataType}"))

    if currentState != DeviceProtocolState.NotReadyDisconnected and currentState != DeviceProtocolState.NotReadyConnected and currentState != DeviceProtocolState.NotReadyEnumerated:
        actions.append(Generate.Information("Device is already in 'ready' status. Aborting"))
        return actions

    el = ElementDescription()
    el.disposition = DispositionTypes.Metadata.value
    el.elementId = nextElementId
    actions.append(Generate.IncrementNextElementId())
    el.dataType = metadataType.value
    el.name = metadataName

    actions.append(Generate.AppendEnumeration(el))
    return actions

def DeviceDefiningAvailableStream(currentState:int, nextElementId:int, streamName: str, streamDataType: DataTypes, outgoing: bool = False) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information(f"Defining stream '{streamName}', type {streamDataType}, outgoing = {outgoing}"))

    if currentState != DeviceProtocolState.NotReadyDisconnected and currentState != DeviceProtocolState.NotReadyConnected and currentState != DeviceProtocolState.NotReadyEnumerated:
        actions.append(Generate.Information("Device is already in 'ready' status. Aborting"))
        return actions

    el = ElementDescription()
    el.disposition = DispositionTypes.DeviceToClientStream.value if outgoing else DispositionTypes.ClientToDeviceStream.value
    el.elementId = nextElementId
    actions.append(Generate.IncrementNextElementId())
    el.dataType = streamDataType.value
    el.name = streamName

    actions.append(Generate.AppendEnumeration(el))
    return actions

def CommConnectiong(currentState:int) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information("Connecting."))

    if currentState == DeviceProtocolState.NotReadyDisconnected:
        actions.append(Generate.Information("Changing state to NotReadyConnected."))
        actions.append(Generate.ChangeState(DeviceProtocolState.NotReadyConnected))

    elif currentState == DeviceProtocolState.ReadyDisconnected:
        actions.append(Generate.Information("Changing state to ReadyConnected."))
        actions.append(Generate.ChangeState(DeviceProtocolState.ReadyConnected))

    return actions

def CommDisconnecting(currentState:int) -> list[ActionItem]:
    actions = []
    actions.append(Generate.Information("Disconnecting."))

    if currentState == DeviceProtocolState.NotReadyConnected or currentState == DeviceProtocolState.NotReadyEnumerated:
        actions.append(Generate.Information("Changing state to NotReadyDisconnected."))
        actions.append(Generate.ChangeState(DeviceProtocolState.NotReadyDisconnected))

    elif currentState == DeviceProtocolState.ReadyConnected or currentState == DeviceProtocolState.LinkEstablished:
        actions.append(Generate.Information("Changing state to ReadyDisconnected."))
        actions.append(Generate.ChangeState(DeviceProtocolState.ReadyDisconnected))

    return actions

def CommReceivingData(currentState:int, currentEnumeration:EnumerationSection, reader:StreamReader, data:bytes) -> list[ActionItem]:
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

        if currentState == DeviceProtocolState.NotReadyConnected:
            if section.sectionType == SectionTypes.Enumerate.value:
                actions.append(Generate.Information("Changing state to NotReadyEnumerated."))
                actions.append(Generate.ChangeState(DeviceProtocolState.NotReadyEnumerated))
            else:
                actions.append(Generate.Information("Sending NotAllowed."))
                actions.append(Generate.CommTransmit(Packet([Section(SectionTypes.NotAllowed)]).Encode()))

        elif currentState == DeviceProtocolState.ReadyConnected:
            if section.sectionType == SectionTypes.Enumerate.value:
                actions.append(Generate.Information("Changing state to LinkEstablished."))
                actions.append(Generate.ChangeState(DeviceProtocolState.LinkEstablished))
                actions.append(Generate.Information("Sending Enumeration."))
                actions.append(Generate.CommTransmit(Packet([currentEnumeration]).Encode()))
            else:
                actions.append(Generate.Information("Sending NotAllowed."))
                actions.append(Generate.CommTransmit(Packet([Section(SectionTypes.NotAllowed)]).Encode()))

        elif currentState == DeviceProtocolState.NotReadyEnumerated:
            actions.append(Generate.Information("Sending NotAllowed."))
            actions.append(Generate.CommTransmit(Packet([Section(SectionTypes.NotAllowed)]).Encode()))

        elif currentState == DeviceProtocolState.LinkEstablished:
            if section.sectionType == SectionTypes.Reset.value:
                actions.append(Generate.Information("Forwarding reset request."))
                actions.append(Generate.DeviceReset())
                actions.append(Generate.Information("Changing state to LinkEstablished."))
                actions.append(Generate.ChangeState(DeviceProtocolState.LinkEstablished))
                actions.append(Generate.Information("Responding with confirmation reset signal."))
                actions.append(Generate.CommTransmit(Packet([Section(SectionTypes.Reset)]).Encode()))
                
            elif section.sectionType == SectionTypes.ClientToDeviceStream.value:
                element = currentEnumeration.GetPropertyById(section.streamId)
                if element is None or element.disposition != DispositionTypes.ClientToDeviceStream.value:
                    actions.append(Generate.Information("The referenced element is not a ClientToDeviceStream. Sending NotAllowed and aborting packet."))
                    actions.append(Generate.CommTransmit(Packet([Section(SectionTypes.NotAllowed)]).Encode()))
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
                    actions.append(Generate.Information("Encountered at least one metadata element with an invalid ID. Sending NotAllowed and aborting packet."))
                    actions.append(Generate.CommTransmit(Packet([Section(SectionTypes.NotAllowed)]).Encode()))
                    continue
                
                decodedData = element.DecodeStream(section.dataBytes)
                actions.append(Generate.Information(f"Forwarding data for stream {element.name}."))
                actions.append(Generate.DeviceStreamData(element.name, decodedData, metadata))
                actions.append(Generate.Information("Sending Confirmed."))
                actions.append(Generate.CommTransmit(Packet([Section(SectionTypes.Confirmed)]).Encode()))

            elif section.sectionType == SectionTypes.GetProperty.value:
                element = currentEnumeration.GetPropertyById(section.elementId)
                if element is None or (element.disposition != DispositionTypes.ReadonlyProperty.value and element.disposition != DispositionTypes.EditableProperty.value):
                    actions.append(Generate.Information("The referenced element was not found, or is not ReadonlyProperty or EditableProperty. Sending NotAllowed and aborting packet."))
                    actions.append(Generate.CommTransmit(Packet([Section(SectionTypes.NotAllowed)]).Encode()))
                    continue
                
                actions.append(Generate.Information(f"Forwarding get request for {element.name}."))
                actions.append(Generate.DeviceGetProperty(element.name))

            elif section.sectionType == SectionTypes.SetProperty.value:
                element = currentEnumeration.GetPropertyById(section.elementId)
                if element is None or element.disposition != DispositionTypes.EditableProperty.value:
                    actions.append(Generate.Information("The referenced element was not found, or is not EditableProperty. Sending NotAllowed and aborting packet."))
                    actions.append(Generate.CommTransmit(Packet([Section(SectionTypes.NotAllowed)]).Encode()))
                    continue

                actions.append(Generate.Information(f"Forwarding set request for {element.name}."))
                value = element.DecodeValue(section.propertyValueBytes)
                actions.append(Generate.DeviceSetProperty(element.name, value))

            elif section.sectionType == SectionTypes.Enumerate.value:
                actions.append(Generate.Information("Sending enumeration"))
                actions.append(Generate.CommTransmit(Packet([currentEnumeration]).Encode()))

            else:
                actions.append(Generate.Information("Unexpected packet type. Sending NotAllowed."))
                actions.append(Generate.CommTransmit(Packet([Section(SectionTypes.NotAllowed)]).Encode()))

    return actions