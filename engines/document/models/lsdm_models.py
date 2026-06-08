from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from .base import BaseDocument
from .media_types import MediaType
from .standard import DocumentStandard


class LogSource(str, Enum):
    XES = "xes"
    SYSLOG = "syslog"
    CEF = "cef"
    ES_BULK = "es_bulk"


class SyslogFacility(str, Enum):
    KERN = "kern"
    USER = "user"
    MAIL = "mail"
    DAEMON = "daemon"
    AUTH = "auth"
    SYSLOG = "syslog"
    LPR = "lpr"
    NEWS = "news"
    UUCP = "uucp"
    CRON = "cron"
    AUTHPRIV = "authpriv"
    FTP = "ftp"
    LOCAL0 = "local0"
    LOCAL1 = "local1"
    LOCAL2 = "local2"
    LOCAL3 = "local3"
    LOCAL4 = "local4"
    LOCAL5 = "local5"
    LOCAL6 = "local6"
    LOCAL7 = "local7"


class SyslogSeverity(str, Enum):
    EMERG = "emerg"
    ALERT = "alert"
    CRIT = "crit"
    ERR = "err"
    WARNING = "warning"
    NOTICE = "notice"
    INFO = "info"
    DEBUG = "debug"


class CefSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class EsBulkAction(str, Enum):
    INDEX = "index"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class LogAttribute(BaseModel):
    key: str
    value: str = ""
    type: str | None = None


class XesExtension(BaseModel):
    name: str
    prefix: str = ""
    uri: str = ""


class XesClassifier(BaseModel):
    name: str
    keys: list[str] = Field(default_factory=list)


class XesTrace(BaseModel):
    id: str | None = None
    attributes: list[LogAttribute] = Field(default_factory=list)
    events: list[LogAttribute] = Field(default_factory=list)


class SyslogStructuredData(BaseModel):
    sd_id: str
    parameters: dict[str, str] = Field(default_factory=dict)


class EsBulkActionMeta(BaseModel):
    action: EsBulkAction = EsBulkAction.INDEX
    index: str = ""
    doc_id: str | None = None


class LogEvent(BaseModel):
    id: str | None = None
    timestamp: datetime | None = None
    source: LogSource = LogSource.XES
    attributes: list[LogAttribute] = Field(default_factory=list)
    raw: str | None = None

    syslog_facility: SyslogFacility | None = None
    syslog_severity: SyslogSeverity | None = None
    syslog_hostname: str | None = None
    syslog_app_name: str | None = None
    syslog_proc_id: str | None = None
    syslog_msg_id: str | None = None
    syslog_message: str | None = None
    syslog_structured_data: list[SyslogStructuredData] = Field(default_factory=list)

    cef_device_vendor: str | None = None
    cef_device_product: str | None = None
    cef_device_version: str | None = None
    cef_signature_id: str | None = None
    cef_name: str | None = None
    cef_severity: CefSeverity = CefSeverity.UNKNOWN
    cef_extensions: dict[str, str] = Field(default_factory=dict)

    es_action_meta: EsBulkActionMeta | None = None
    es_source: dict[str, Any] = Field(default_factory=dict)


class EventLogDocument(BaseDocument):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )

    kind: DocumentStandard = Field(default=DocumentStandard.LSDM)
    title: str = ""
    document_id: str = ""
    source: LogSource = LogSource.XES
    events: list[LogEvent] = Field(default_factory=list)
    traces: list[XesTrace] = Field(default_factory=list)
    extensions: list[XesExtension] = Field(default_factory=list)
    classifiers: list[XesClassifier] = Field(default_factory=list)
    attributes: list[LogAttribute] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
