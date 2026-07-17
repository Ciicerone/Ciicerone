from __future__ import annotations

import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class OperationType(str, Enum):
    THREAT_HUNT = "threat_hunt"
    INCIDENT_RESPONSE = "incident_response"
    ORCHESTRATION = "orchestration"
    SYSTEM_ADMIN = "system_admin"
    PENETRATION_TEST = "penetration_test"
    VULNERABILITY_SCAN = "vulnerability_scan"
    DATA_EXPORT = "data_export"
    CONFIG_CHANGE = "config_change"
    USER_ESCALATION = "user_escalation"
    CUSTOM = "custom"


class ApprovalRole(str, Enum):
    TEAM_LEAD = "team_lead"
    MANAGER = "manager"
    ADMIN = "admin"
    SOC_ANALYST = "soc_analyst"
    THREAT_HUNTER = "threat_hunter"
    COMPLIANCE_OFFICER = "compliance_officer"
    CUSTOM = "custom"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ApprovalDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"
    DEFER = "defer"


class ApprovalStep(BaseModel):
    name: str
    description: str = ""
    required_roles: list[ApprovalRole] = Field(default_factory=list)
    min_approvers: int = 1
    timeout_minutes: int = 240
    escalation_step: Optional[str] = None
    allow_skip: bool = False
    require_justification: bool = True
    require_mfa: bool = False
    notify_on_approval: list[str] = Field(default_factory=list)
    notify_on_rejection: list[str] = Field(default_factory=list)


class ApprovalChain(BaseModel):
    name: str
    description: str = ""
    operation_types: list[OperationType] = Field(default_factory=list)
    steps: list[ApprovalStep] = Field(default_factory=list)
    timeout_minutes: int = 1440
    escalation_chain: Optional[str] = None
    require_all_steps: bool = True
    allow_parallel: bool = False
    max_escalations: int = 3
    audit_level: str = "detailed"


class ApprovalConfig(BaseModel):
    chains: list[ApprovalChain] = Field(default_factory=list)
    default_timeout_minutes: int = 1440
    max_escalations: int = 3
    audit_enabled: bool = True
    require_mfa_for: list[OperationType] = Field(default_factory=list)
    notify_channels: list[str] = Field(default_factory=lambda: ["log"])


class WorkflowConfig(BaseModel):
    version: str = "1.0"
    metadata: dict[str, Any] = Field(default_factory=dict)
    approval: ApprovalConfig
