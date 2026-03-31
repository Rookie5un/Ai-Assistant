from pydantic import BaseModel


class MetricItem(BaseModel):
    label: str
    value: str
    detail: str


class ActivityItem(BaseModel):
    label: str
    detail: str
    timestamp: str


class DashboardOverview(BaseModel):
    metrics: list[MetricItem]
    active_assistants: list[str]
    pending_documents: list[str]
    activity: list[ActivityItem]

