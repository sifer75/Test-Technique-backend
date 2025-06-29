from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import List

class LogLevel(str, Enum):
    fatal = "fatal"
    error = "error"
    warn = "warn"
    info = "info"
    debug = "debug"
    empty = ""

class LogService(str, Enum):
    auth = "auth"
    payment = "payment"
    notifications = "notifications"
    empty = ""

class LogEntry(BaseModel):
    level: LogLevel
    message: str
    service: LogService

class LogEntryResponse(LogEntry):
    id: str
    message: str
    level: str
    service: str
    timestamp: str

class SearchLogResult(BaseModel):
    id: str
    message: str
    level: str
    service: str
    timestamp: str

class SearchLogResponse(BaseModel):
    total: int
    page: int
    size: int
    results: List[SearchLogResult]