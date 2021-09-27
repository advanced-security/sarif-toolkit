#!/usr/bin/env python3
from dataclasses import dataclass, field
from typing import Any, List, Dict, ClassVar


class BaseModel:
    __holders__: ClassVar[Dict[str, str]] = None

    def keys(self):
        returns = []

        for key in self.__annotations__.keys():
            print(f" >> {key}")
            # if self.__holders__.get(value) == key:
            #     returns.append(key)
            # else: returns.append(key)
        return returns

    def __getitem__(self, key):
        return dict(zip("abc", "one two three".split()))[key]


@dataclass
class ShortdescriptionModel(BaseModel):
    text: str = None


@dataclass
class FulldescriptionModel(BaseModel):
    text: str = None


@dataclass
class DefaultconfigurationModel(BaseModel):
    enabled: bool = None


@dataclass
class PropertiesModel(BaseModel):
    description: str = None
    id: str = None
    kind: str = None
    name: str = None


@dataclass
class NotificationsModel(BaseModel):
    id: str = None
    name: str = None
    shortDescription: ShortdescriptionModel = None
    fullDescription: FulldescriptionModel = None
    defaultConfiguration: DefaultconfigurationModel = None
    properties: PropertiesModel = None


@dataclass
class ShortdescriptionModel(BaseModel):
    text: str = None


@dataclass
class FulldescriptionModel(BaseModel):
    text: str = None


@dataclass
class DefaultconfigurationModel(BaseModel):
    enabled: bool = None
    level: str = None


@dataclass
class PropertiesModel(BaseModel):
    tags: List[str] = field(default_factory=list)
    description: str = None
    id: str = None
    kind: str = None
    name: str = None
    precision: str = None
    problem_severity: str = None
    security_severity: str = None
    sub_severity: str = None

    __holders__: ClassVar[Dict[str, str]] = {
        "problem.severity": "problem_severity",
        "security-severity": "security_severity",
        "sub-severity": "sub_severity",
    }

    def __getattr__(self, name: str):
        for key, value in self.__holders__.items():
            if key == name or name == value:
                return super().__getattribute__(self.__holders__[key])
        return super().__getattribute__(name)


@dataclass
class RulesModel(BaseModel):
    id: str = None
    name: str = None
    shortDescription: ShortdescriptionModel = None
    fullDescription: FulldescriptionModel = None
    defaultConfiguration: DefaultconfigurationModel = None
    properties: PropertiesModel = None


@dataclass
class DriverModel(BaseModel):
    name: str = None
    organization: str = None
    semanticVersion: str = None
    notifications: List[NotificationsModel] = field(default_factory=list)
    rules: List[RulesModel] = field(default_factory=list)


@dataclass
class DescriptionModel(BaseModel):
    text: str = None


@dataclass
class LocationsModel(BaseModel):
    uri: str = None
    description: DescriptionModel = None


@dataclass
class ExtensionsModel(BaseModel):
    name: str = None
    semanticVersion: str = None
    locations: List[LocationsModel] = field(default_factory=list)


@dataclass
class ToolModel(BaseModel):
    driver: DriverModel = None
    extensions: List[ExtensionsModel] = field(default_factory=list)


@dataclass
class ArtifactlocationModel(BaseModel):
    uri: str = None
    uriBaseId: str = None
    index: int = None


@dataclass
class PhysicallocationModel(BaseModel):
    artifactLocation: ArtifactlocationModel = None


@dataclass
class LocationsModel(BaseModel):
    physicalLocation: PhysicallocationModel = None


@dataclass
class MessageModel(BaseModel):
    text: str = None


@dataclass
class DescriptorModel(BaseModel):
    id: str = None
    index: int = None


@dataclass
class FormattedmessageModel(BaseModel):
    text: str = None


@dataclass
class PropertiesModel(BaseModel):
    formattedMessage: FormattedmessageModel = None
    relatedLocations: List[Any] = field(default_factory=list)


@dataclass
class ToolexecutionnotificationsModel(BaseModel):
    locations: List[LocationsModel] = field(default_factory=list)
    message: MessageModel = None
    level: str = None
    descriptor: DescriptorModel = None
    properties: PropertiesModel = None


@dataclass
class InvocationsModel(BaseModel):
    toolExecutionNotifications: List[ToolexecutionnotificationsModel] = field(
        default_factory=list
    )
    executionSuccessful: bool = None


@dataclass
class LocationModel(BaseModel):
    uri: str = None
    uriBaseId: str = None
    index: int = None


@dataclass
class ArtifactsModel(BaseModel):
    location: LocationModel = None


@dataclass
class RuleModel(BaseModel):
    id: str = None
    index: int = None


@dataclass
class MessageModel(BaseModel):
    text: str = None


@dataclass
class ArtifactlocationModel(BaseModel):
    uri: str = None
    uriBaseId: str = None
    index: int = None


@dataclass
class RegionModel(BaseModel):
    startLine: int = None
    startColumn: int = None
    endColumn: int = None


@dataclass
class PhysicallocationModel(BaseModel):
    artifactLocation: ArtifactlocationModel = None
    region: RegionModel = None


@dataclass
class LocationsModel(BaseModel):
    physicalLocation: PhysicallocationModel = None


@dataclass
class PartialfingerprintsModel(BaseModel):
    primaryLocationLineHash: str = None
    primaryLocationStartColumnFingerprint: str = None


@dataclass
class ResultsModel(BaseModel):
    ruleId: str = None
    ruleIndex: int = None
    rule: RuleModel = None
    message: MessageModel = None
    locations: List[LocationsModel] = field(default_factory=list)
    partialFingerprints: PartialfingerprintsModel = None


@dataclass
class RuleModel(BaseModel):
    id: str = None
    index: int = None


@dataclass
class MetricresultsModel(BaseModel):
    rule: RuleModel = None
    ruleId: str = None
    ruleIndex: int = None
    value: int = None


@dataclass
class PropertiesModel(BaseModel):
    metricResults: List[MetricresultsModel] = field(default_factory=list)
    semmle_formatSpecifier: str = None

    __holders__: ClassVar[Dict[str, str]] = {
        "semmle.formatSpecifier": "semmle_formatSpecifier"
    }

    def __getattr__(self, name: str):
        for key, value in self.__holders__.items():
            if key == name or name == value:
                return super().__getattribute__(self.__holders__[key])
        return super().__getattribute__(name)


@dataclass
class RunsModel(BaseModel):
    tool: ToolModel = None
    invocations: List[InvocationsModel] = field(default_factory=list)
    artifacts: List[ArtifactsModel] = field(default_factory=list)
    results: List[ResultsModel] = field(default_factory=list)
    columnKind: str = None
    properties: PropertiesModel = None


@dataclass
class SarifModel(BaseModel):
    _schema: str = None
    version: str = None
    runs: List[RunsModel] = field(default_factory=list)

    __holders__: ClassVar[Dict[str, str]] = {"$schema": "_schema"}

    def __getattr__(self, name: str):
        for key, value in self.__holders__.items():
            if key == name or name == value:
                return super().__getattribute__(self.__holders__[key])
        return super().__getattribute__(name)
