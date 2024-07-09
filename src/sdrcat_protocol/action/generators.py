from sdrcat_protocol.action.action import ActionItem, DefineStreamParams, DefinePropertyParams, DefineMetadataParams, CommPayloadParams, InformationParams, StateChangeParams, SetEnumerationParams, DeviceInfoParams, PropertyValueParams, PropertyParam, StreamDataParams, CommConnectParams, AppendEnumerationParams
from sdrcat_protocol.action.definitions import Actions

from sdrcat_protocol.network import EnumerationSection, ElementDescription
from sdrcat_protocol.deviceinfo import DeviceInfo
from sdrcat_protocol.definitions import DataTypes

class GenerateFromClient:
    def Connect(connectionParams:dict[str, any]):              return ActionItem("client", "coordinator", Actions.FromClientConnect,        CommConnectParams(connectionParams))
    def Disconnect():                                          return ActionItem("client", "coordinator", Actions.FromClientDisconnect,     None)
    def Reset():                                               return ActionItem("client", "coordinator", Actions.FromClientReset,          None)
    def GetProperty(name: str):                                return ActionItem("client", "coordinator", Actions.FromClientGetProperty,    PropertyParam(name))
    def SetProperty(name:str, value:any):                      return ActionItem("client", "coordinator", Actions.FromClientSetProperty,    PropertyValueParams(name, value))
    def SendData(name:str, data:any, metadata:dict[str, any]): return ActionItem("client", "coordinator", Actions.FromClientStreamData,     StreamDataParams(name, data, metadata))

class GenerateFromDevice:
    def Start(connectionParams:dict[str,any]):                               return ActionItem("device", "coordinator", Actions.FromDeviceStartup,        CommConnectParams(connectionParams))
    def Ready():                                                             return ActionItem("device", "coordinator", Actions.FromDeviceReady,          None)
    def Reset():                                                             return ActionItem("device", "coordinator", Actions.FromDeviceReset,          None)
    def DefineStream(name:str, dataType:DataTypes, isOutgoing:bool=False):   return ActionItem("device", "coordinator", Actions.FromDeviceDefineStream,   DefineStreamParams(name, dataType, isOutgoing))
    def DefineProperty(name:str, dataType:DataTypes, isReadOnly:bool=False): return ActionItem("device", "coordinator", Actions.FromDeviceDefineProperty, DefinePropertyParams(name, dataType, isReadOnly))
    def DefineMetadata(name:str, dataType:DataTypes):                        return ActionItem("device", "coordinator", Actions.FromDeviceDefineMetadata, DefineMetadataParams(name, dataType))
    def PropertyValue(name:str, value:any):                                  return ActionItem("device", "coordinator", Actions.FromDevicePropertyValue,  PropertyValueParams(name, value))
    def StreamData(name:str, data:any, metadata:dict[str, any]):             return ActionItem("device", "coordinator", Actions.FromDeviceStreamData,     StreamDataParams(name, data, metadata))
    def Exit():                                                              return ActionItem("*",    "*",             Actions.Exit,               None)

class GenerateFromComm:
    def Connect():           return ActionItem("comm", "coordinator", Actions.FromCommConnect,    None)
    def Disconnect():        return ActionItem("comm", "coordinator", Actions.FromCommDisconnect, None)
    def Receive(data:bytes): return ActionItem("comm", "coordinator", Actions.FromCommReceive,    CommPayloadParams(data))
    def Exit():              return ActionItem("*",    "*",           Actions.Exit,               None)

class GenerateFromClientCoordinator:
    def Information(message:str):                                      return ActionItem("coordinator", "*",           Actions.CoordinatorInformation,            InformationParams(message))
    def ClearEnumeration():                                            return ActionItem("coordinator", "coordinator", Actions.CoordinatorClearEnumeration,       None)
    def ChangeState(state:int):                                        return ActionItem("coordinator", "coordinator", Actions.CoordinatorState,                  StateChangeParams(state))
    def SetEnumeration(enumeration:EnumerationSection):                return ActionItem("coordinator", "coordinator", Actions.CoordinatorSetEnumeration,         SetEnumerationParams(enumeration))

    def ClientStatus(state:int):                                       return ActionItem("coordinator", "client",      Actions.ToClientStatus,                    StateChangeParams(state))
    def ClientDeviceInfo(deviceInfo:DeviceInfo):                       return ActionItem("coordinator", "client",      Actions.ToClientDeviceInfo,                DeviceInfoParams(deviceInfo))
    def ClientPropertyValue(name:str, value:any):                      return ActionItem("coordinator", "client",      Actions.ToClientPropertyValue,             PropertyValueParams(name, value))
    def ClientStreamData(name:str, data:any, metadata:dict[str, any]): return ActionItem("coordinator", "client",      Actions.ToClientStreamData,                StreamDataParams(name, data, metadata))

    def CommTransmit(data:bytes):                                      return ActionItem("coordinator", "comm",        Actions.ToCommTransmit,                    CommPayloadParams(data))
    def CommConnect(connectionParams:dict[str,any]):                   return ActionItem("coordinator", "comm",        Actions.ToCommConnect,                     CommConnectParams(connectionParams))
    def CommDisconnect():                                              return ActionItem("coordinator", "comm",        Actions.ToCommDisconnect,                  None)

class GenerateFromDeviceCoordinator:
    def Information(message:str):                                      return ActionItem("coordinator", "*",           Actions.CoordinatorInformation,            InformationParams(message))
    def ChangeState(state:int):                                        return ActionItem("coordinator", "coordinator", Actions.CoordinatorState,                  StateChangeParams(state))
    def ClearEnumeration():                                            return ActionItem("coordinator", "coordinator", Actions.CoordinatorClearEnumeration,       None)
    def ResetNextElementId():                                          return ActionItem("coordinator", "coordinator", Actions.CoordinatorResetNextElementId,     None)
    def IncrementNextElementId():                                      return ActionItem("coordinator", "coordinator", Actions.CoordinatorIncrementNextElementId, None)
    def AppendEnumeration(elementDescription:ElementDescription):      return ActionItem("coordinator", "coordinator", Actions.CoordinatorAppendEnumeration,      AppendEnumerationParams(elementDescription))

    def CommTransmit(data:bytes):                                      return ActionItem("coordinator", "comm",        Actions.ToCommTransmit,                    CommPayloadParams(data))
    def CommConnect(connectionParams:dict[str,any]):                   return ActionItem("coordinator", "comm",        Actions.ToCommConnect,                     CommConnectParams(connectionParams))

    def DeviceReset():                                                 return ActionItem("coordinator", "device",      Actions.ToDeviceReset,                     None)
    def DeviceStreamData(name:str, data:any, metadata:dict[str, any]): return ActionItem("coordinator", "device",      Actions.ToDeviceStreamData,                StreamDataParams(name, data, metadata))
    def DeviceGetProperty(name:str):                                   return ActionItem("coordinator", "device",      Actions.ToDeviceGetProperty,               PropertyParam(name))
    def DeviceSetProperty(name:str, value:any):                        return ActionItem("coordinator", "device",      Actions.ToDeviceSetProperty,               PropertyValueParams(name, value))