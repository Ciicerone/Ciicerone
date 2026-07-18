"""Hypothesis Validation Pipeline for Blue Team threat hunting.

Scores hunting hypotheses by likelihood, impact, and detectability
to prioritize the most promising leads for investigation.

Issue: Hypothesis validation pipeline (scores by likelihood, impact, detectability)
Owner: David Onoja (@ocheme1107)
Track: Blue Team / Detection Engineering
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from .mitre_attack import (
    MITREATTACKEngine,
    ATTACKTechnique,
    ATTACKGroup,
    ATTACKMatrix,
    ENTERPRISE_TACTICS,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Enums & Constants
# ============================================================================


class HypothesisStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    IN_PROGRESS = "in_progress"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    INCONCLUSIVE = "inconclusive"


class LikelihoodFactor(str, Enum):
    THREAT_ACTOR_USAGE = "threat_actor_usage"
    TECHNIQUE_PREVALENCE = "technique_prevalence"
    HISTORICAL_INCIDENTS = "historical_incidents"
    CURRENT_THREAT_LANDSCAPE = "current_threat_landscape"
    PLATFORM_RELEVANCE = "platform_relevance"
    INDUSTRY_TARGETING = "industry_targeting"
    RECENT_CAMPAIGNS = "recent_campaigns"
    TOOL_AVAILABILITY = "tool_availability"
    PUBLIC_EXPLOITS = "public_exploits"
    EASE_OF_EXECUTION = "ease_of_execution"


class ImpactFactor(str, Enum):
    DATA_EXFILTRATION = "data_exfiltration"
    SYSTEM_COMPROMISE = "system_compromise"
    CREDENTIAL_THEFT = "credential_theft"
    LATERAL_MOVEMENT = "lateral_movement"
    PERSISTENCE = "persistence"
    DEFENSE_EVASION = "defense_evasion"
    BUSINESS_IMPACT = "business_impact"
    REGULATORY_VIOLATION = "regulatory_violation"
    REPUTATIONAL_DAMAGE = "reputational_damage"
    FINANCIAL_LOSS = "financial_loss"


class DetectabilityFactor(str, Enum):
    DATA_SOURCE_AVAILABILITY = "data_source_availability"
    DETECTION_RULE_COVERAGE = "detection_rule_coverage"
    SIGNAL_TO_NOISE_RATIO = "signal_to_noise_ratio"
    DETECTION_COMPLEXITY = "detection_complexity"
    FALSE_POSITIVE_RATE = "false_positive_rate"
    REQUIRED_TOOLING = "required_tooling"
    ANALYST_SKILL_LEVEL = "analyst_skill_level"
    CORRELATION_REQUIRED = "correlation_required"


class HypothesisSource(str, Enum):
    MITRE_TECHNIQUE = "mitre_technique"
    THREAT_INTEL = "threat_intel"
    HISTORICAL_INCIDENT = "historical_incident"
    USER_BEHAVIOR_ANALYTICS = "user_behavior_analytics"
    NETWORK_ANOMALY = "network_anomaly"
    THREAT_HUNTING = "threat_hunting"
    INTELLIGENCE_FEED = "intelligence_feed"
    MANUAL = "manual"


class ValidationStatus(str, Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    ESCALATED = "escalated"


# ============================================================================
# Scoring Models
# ============================================================================


@dataclass
class LikelihoodScore:
    score: float
    factors: Dict[LikelihoodFactor, float]
    reasoning: str

    def __post_init__(self):
        self.score = max(0.0, min(1.0, self.score))


@dataclass
class ImpactScore:
    score: float
    factors: Dict[ImpactFactor, float]
    reasoning: str

    def __post_init__(self):
        self.score = max(0.0, min(1.0, self.score))


@dataclass
class DetectabilityScore:
    score: float
    factors: Dict[DetectabilityFactor, float]
    reasoning: str

    def __post_init__(self):
        self.score = max(0.0, min(1.0, self.score))


@dataclass
class HypothesisValidationResult:
    hypothesis_id: str
    technique_id: str
    technique_name: str
    tactic: str
    description: str
    likelihood: LikelihoodScore
    impact: ImpactScore
    detectability: DetectabilityScore
    overall_score: float
    priority: str
    recommendation: str
    supporting_evidence: List[str]
    related_groups: List[str]
    related_software: List[str]
    mitre_mitigations: List[str]
    status: ValidationStatus
    validated_at: datetime
    source: HypothesisSource
    ttl_hours: int

    @property
    def risk_score(self) -> float:
        return self.likelihood.score * self.impact.score

    @property
    def hunt_priority(self) -> float:
        return self.overall_score * (1 - self.detectability.score)

    @property
    def summary(self) -> str:
        return (
            f"[{self.priority}] {self.technique_id} - {self.technique_name} "
            f"(L:{self.likelihood.score:.2f} I:{self.impact.score:.2f} "
            f"D:{self.detectability.score:.2f} | Overall: {self.overall_score:.2f})"
        )


