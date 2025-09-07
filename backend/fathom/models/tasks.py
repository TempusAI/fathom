from typing import List, Optional
from pydantic import BaseModel


class TaskDefinitionId(BaseModel):
    scope: str
    code: str


class TaskDefinitionVersion(BaseModel):
    asAtModified: str


class TaskVersion(BaseModel):
    asAtCreated: str
    userIdCreated: str
    requestIdCreated: str
    asAtModified: str
    userIdModified: str
    requestIdModified: str
    asAtVersionNumber: int


class TaskField(BaseModel):
    name: str
    value: Optional[str] = None


class TaskReference(BaseModel):
    id: str
    taskDefinitionId: TaskDefinitionId
    taskDefinitionVersion: TaskDefinitionVersion
    taskDefinitionDisplayName: str
    state: str


class WorkflowTask(BaseModel):
    id: str
    taskDefinitionId: TaskDefinitionId
    taskDefinitionVersion: TaskDefinitionVersion
    taskDefinitionDisplayName: str
    state: str
    ultimateParentTask: Optional[TaskReference] = None
    parentTask: Optional[TaskReference] = None
    childTasks: List[TaskReference] = []
    correlationIds: List[str] = []
    version: TaskVersion
    terminalState: bool
    asAtLastTransition: str
    fields: List[TaskField] = []
    stackingKey: Optional[str] = None
    actionLogIdCreated: Optional[str] = None
    actionLogIdModified: Optional[str] = None
    actionLogIdSubmitted: Optional[str] = None


class TaskListResponse(BaseModel):
    values: List[WorkflowTask]
    href: str
    links: List[dict] = []
    nextPage: Optional[str] = None
    previousPage: Optional[str] = None


class TaskFilter(BaseModel):
    dateFrom: Optional[str] = None
    dateTo: Optional[str] = None
    searchQuery: Optional[str] = None
    states: Optional[List[str]] = None
    correlationIds: Optional[List[str]] = None
