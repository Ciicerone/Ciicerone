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


# ============================================================================
# Likelihood Scoring Engine
# ============================================================================


class LikelihoodScorer:
    def __init__(self, mitre_engine: MITREATTACKEngine):
        self._mitre = mitre_engine

    def score(self, technique_id: str, tactic: str) -> LikelihoodScore:
        technique = self._mitre.get_technique(technique_id)
        if not technique:
            return LikelihoodScore(
                score=0.3,
                factors={},
                reasoning=f"Technique {technique_id} not found in MITRE data; defaulting to medium-low likelihood"
            )

        factors: Dict[LikelihoodFactor, float] = {}
        reasoning_parts: List[str] = []

        factor = self._score_threat_actor_usage(technique_id)
        factors[LikelihoodFactor.THREAT_ACTOR_USAGE] = factor
        if factor >= 0.7:
            reasoning_parts.append(f"Widely used by threat actors (score: {factor:.2f})")
        elif factor >= 0.4:
            reasoning_parts.append(f"Moderate threat actor adoption (score: {factor:.2f})")
        else:
            reasoning_parts.append(f"Limited threat actor usage (score: {factor:.2f})")

        factor = self._score_technique_prevalence(technique)
        factors[LikelihoodFactor.TECHNIQUE_PREVALENCE] = factor
        if factor >= 0.7:
            reasoning_parts.append(f"Highly prevalent technique (score: {factor:.2f})")
        elif factor >= 0.4:
            reasoning_parts.append(f"Moderately prevalent technique (score: {factor:.2f})")
        else:
            reasoning_parts.append(f"Less common technique (score: {factor:.2f})")

        factor = self._score_platform_relevance(technique)
        factors[LikelihoodFactor.PLATFORM_RELEVANCE] = factor
        if factor >= 0.7:
            reasoning_parts.append(f"High platform relevance (score: {factor:.2f})")
        elif factor >= 0.4:
            reasoning_parts.append(f"Moderate platform relevance (score: {factor:.2f})")
        else:
            reasoning_parts.append(f"Limited platform relevance (score: {factor:.2f})")

        factor = self._score_industry_targeting(technique_id)
        factors[LikelihoodFactor.INDUSTRY_TARGETING] = factor
        if factor >= 0.7:
            reasoning_parts.append(f"Commonly targeted industry technique (score: {factor:.2f})")
        elif factor >= 0.4:
            reasoning_parts.append(f"Occasionally targeted industry technique (score: {factor:.2f})")
        else:
            reasoning_parts.append(f"Broad or non-specific targeting (score: {factor:.2f})")

        factor = self._score_ease_of_execution(technique)
        factors[LikelihoodFactor.EASE_OF_EXECUTION] = factor
        if factor >= 0.7:
            reasoning_parts.append(f"Easy to execute — low skill barrier (score: {factor:.2f})")
        elif factor >= 0.4:
            reasoning_parts.append(f"Moderate execution complexity (score: {factor:.2f})")
        else:
            reasoning_parts.append(f"Complex execution — requires advanced skills (score: {factor:.2f})")

        weights = {
            LikelihoodFactor.THREAT_ACTOR_USAGE: 0.25,
            LikelihoodFactor.TECHNIQUE_PREVALENCE: 0.20,
            LikelihoodFactor.PLATFORM_RELEVANCE: 0.15,
            LikelihoodFactor.INDUSTRY_TARGETING: 0.15,
            LikelihoodFactor.EASE_OF_EXECUTION: 0.25,
        }

        weighted_score = sum(
            factors.get(factor, 0.0) * weight
            for factor, weight in weights.items()
        )

        return LikelihoodScore(
            score=weighted_score,
            factors=factors,
            reasoning="; ".join(reasoning_parts)
        )

    def _score_threat_actor_usage(self, technique_id: str) -> float:
        groups = self._mitre.get_groups_using_technique(technique_id)
        if not groups:
            return 0.2
        count = len(groups)
        if count >= 10:
            return 0.95
        elif count >= 5:
            return 0.80
        elif count >= 3:
            return 0.65
        elif count >= 1:
            return 0.50
        return 0.2

    def _score_technique_prevalence(self, technique: ATTACKTechnique) -> float:
        if not technique:
            return 0.3
        platforms = len(technique.platforms)
        sub_count = len(technique.sub_techniques)
        base = 0.3
        base += min(platforms * 0.08, 0.35)
        base += min(sub_count * 0.05, 0.20)
        return min(base, 0.95)

    def _score_platform_relevance(self, technique: ATTACKTechnique) -> float:
        if not technique or not technique.platforms:
            return 0.3
        common_platforms = {"windows", "linux", "macos", "cloud", "network"}
        relevant = sum(1 for p in technique.platforms if p.lower() in common_platforms)
        if not technique.platforms:
            return 0.3
        ratio = relevant / len(technique.platforms)
        return 0.3 + (ratio * 0.6)

    def _score_industry_targeting(self, technique_id: str) -> float:
        groups = self._mitre.get_groups_using_technique(technique_id)
        if not groups:
            return 0.3
        high_profile_groups = sum(1 for g in groups if g.name and len(g.aliases) > 2)
        if high_profile_groups >= 5:
            return 0.85
        elif high_profile_groups >= 3:
            return 0.70
        elif high_profile_groups >= 1:
            return 0.55
        return 0.3

    def _score_ease_of_execution(self, technique: ATTACKTechnique) -> float:
        if not technique:
            return 0.5
        low_barrier_tactics = {
            "initial-access", "execution", "persistence",
            "defense-evasion", "discovery", "collection"
        }
        has_low_barrier = any(t in low_barrier_tactics for t in technique.tactics)
        has_multi_platform = len(technique.platforms) >= 3
        has_subtechniques = len(technique.sub_techniques) > 0
        score = 0.3
        if has_low_barrier:
            score += 0.25
        if has_multi_platform:
            score += 0.20
        if has_subtechniques:
            score += 0.15
        return min(score, 0.95)


# ============================================================================
# Impact Scoring Engine
# ============================================================================


class ImpactScorer:
    HIGH_IMPACT_TACTICS = {
        "impact", "exfiltration", "credential-access",
        "lateral-movement", "privilege-escalation"
    }
    MEDIUM_IMPACT_TACTICS = {
        "persistence", "defense-evasion", "collection",
        "command-and-control"
    }

    TACTIC_IMPACT_WEIGHTS = {
        "impact": 0.95,
        "exfiltration": 0.90,
        "credential-access": 0.85,
        "lateral-movement": 0.80,
        "privilege-escalation": 0.75,
        "persistence": 0.60,
        "defense-evasion": 0.55,
        "collection": 0.50,
        "command-and-control": 0.50,
        "execution": 0.45,
        "initial-access": 0.40,
        "discovery": 0.30,
        "reconnaissance": 0.20,
        "resource-development": 0.15,
    }

    def __init__(self, mitre_engine: MITREATTACKEngine):
        self._mitre = mitre_engine

    def score(self, technique_id: str) -> ImpactScore:
        technique = self._mitre.get_technique(technique_id)
        if not technique:
            return ImpactScore(
                score=0.3,
                factors={},
                reasoning=f"Technique {technique_id} not found; defaulting to medium impact"
            )

        factors: Dict[ImpactFactor, float] = {}
        reasoning_parts: List[str] = []

        factor = self._score_data_exfiltration(technique)
        factors[ImpactFactor.DATA_EXFILTRATION] = factor
        if factor >= 0.7:
            reasoning_parts.append(f"High data exfiltration potential (score: {factor:.2f})")
        elif factor >= 0.4:
            reasoning_parts.append(f"Moderate data exfiltration potential (score: {factor:.2f})")
        else:
            reasoning_parts.append(f"Low data exfiltration potential (score: {factor:.2f})")

        factor = self._score_system_compromise(technique)
        factors[ImpactFactor.SYSTEM_COMPROMISE] = factor
        if factor >= 0.7:
            reasoning_parts.append(f"High system compromise risk (score: {factor:.2f})")
        elif factor >= 0.4:
            reasoning_parts.append(f"Moderate system compromise risk (score: {factor:.2f})")
        else:
            reasoning_parts.append(f"Low system compromise risk (score: {factor:.2f})")

        factor = self._score_credential_theft(technique)
        factors[ImpactFactor.CREDENTIAL_THEFT] = factor
        if factor >= 0.7:
            reasoning_parts.append(f"High credential theft risk (score: {factor:.2f})")
        elif factor >= 0.4:
            reasoning_parts.append(f"Moderate credential theft risk (score: {factor:.2f})")
        else:
            reasoning_parts.append(f"Low credential theft risk (score: {factor:.2f})")

        factor = self._score_lateral_movement(technique)
        factors[ImpactFactor.LATERAL_MOVEMENT] = factor
        if factor >= 0.7:
            reasoning_parts.append(f"High lateral movement potential (score: {factor:.2f})")
        elif factor >= 0.4:
            reasoning_parts.append(f"Moderate lateral movement potential (score: {factor:.2f})")
        else:
            reasoning_parts.append(f"Low lateral movement potential (score: {factor:.2f})")

        factor = self._score_business_impact(technique)
        factors[ImpactFactor.BUSINESS_IMPACT] = factor
        if factor >= 0.7:
            reasoning_parts.append(f"High business impact (score: {factor:.2f})")
        elif factor >= 0.4:
            reasoning_parts.append(f"Moderate business impact (score: {factor:.2f})")
        else:
            reasoning_parts.append(f"Low business impact (score: {factor:.2f})")

        weights = {
            ImpactFactor.DATA_EXFILTRATION: 0.20,
            ImpactFactor.SYSTEM_COMPROMISE: 0.20,
            ImpactFactor.CREDENTIAL_THEFT: 0.20,
            ImpactFactor.LATERAL_MOVEMENT: 0.15,
            ImpactFactor.BUSINESS_IMPACT: 0.25,
        }

        weighted_score = sum(
            factors.get(factor, 0.0) * weight
            for factor, weight in weights.items()
        )

        return ImpactScore(
            score=weighted_score,
            factors=factors,
            reasoning="; ".join(reasoning_parts)
        )

    def _score_data_exfiltration(self, technique: ATTACKTechnique) -> float:
        if not technique:
            return 0.3
        exfil_tactics = {"exfiltration", "collection"}
        has_exfil = any(t in exfil_tactics for t in technique.tactics)
        if has_exfil:
            return 0.85
        if "credential-access" in technique.tactics:
            return 0.70
        return 0.25

    def _score_system_compromise(self, technique: ATTACKTechnique) -> float:
        if not technique:
            return 0.3
        compromise_tactics = {"execution", "persistence", "privilege-escalation"}
        has_compromise = any(t in compromise_tactics for t in technique.tactics)
        if has_compromise and "defense-evasion" in technique.tactics:
            return 0.90
        if has_compromise:
            return 0.70
        if "initial-access" in technique.tactics:
            return 0.50
        return 0.20

    def _score_credential_theft(self, technique: ATTACKTechnique) -> float:
        if not technique:
            return 0.3
        if "credential-access" in technique.tactics:
            return 0.90
        if "initial-access" in technique.tactics:
            return 0.55
        if "lateral-movement" in technique.tactics:
            return 0.50
        return 0.20

    def _score_lateral_movement(self, technique: ATTACKTechnique) -> float:
        if not technique:
            return 0.3
        if "lateral-movement" in technique.tactics:
            return 0.85
        if "credential-access" in technique.tactics:
            return 0.60
        if "execution" in technique.tactics:
            return 0.45
        return 0.20

    def _score_business_impact(self, technique: ATTACKTechnique) -> float:
        if not technique:
            return 0.3
        score = 0.2
        for tactic in technique.tactics:
            tactic_score = self.TACTIC_IMPACT_WEIGHTS.get(tactic, 0.0)
            score = max(score, tactic_score)
        if technique.platforms:
            score += min(len(technique.platforms) * 0.03, 0.15)
        return min(score, 0.95)


# ============================================================================
# Detectability Scoring Engine
# ============================================================================


class DetectabilityScorer:
    HIGH_DETECTABILITY_TACTICS = {
        "reconnaissance", "resource-development", "initial-access",
        "execution", "discovery"
    }
    LOW_DETECTABILITY_TACTICS = {
        "defense-evasion", "persistence", "privilege-escalation",
        "credential-access", "exfiltration"
    }

    def __init__(self, mitre_engine: MITREATTACKEngine):
        self._mitre = mitre_engine

    def score(self, technique_id: str) -> DetectabilityScore:
        technique = self._mitre.get_technique(technique_id)
        if not technique:
            return DetectabilityScore(
                score=0.5,
                factors={},
                reasoning=f"Technique {technique_id} not found; defaulting to medium detectability"
            )

        factors: Dict[DetectabilityFactor, float] = {}
        reasoning_parts: List[str] = []

        factor = self._score_data_source_availability(technique)
        factors[DetectabilityFactor.DATA_SOURCE_AVAILABILITY] = factor
        if factor >= 0.7:
            reasoning_parts.append(f"Good data source coverage (score: {factor:.2f})")
        elif factor >= 0.4:
            reasoning_parts.append(f"Partial data source coverage (score: {factor:.2f})")
        else:
            reasoning_parts.append(f"Limited data source coverage (score: {factor:.2f})")

        factor = self._score_detection_complexity(technique)
        factors[DetectabilityFactor.DETECTION_COMPLEXITY] = factor
        if factor >= 0.7:
            reasoning_parts.append(f"Easy to detect (score: {factor:.2f})")
        elif factor >= 0.4:
            reasoning_parts.append(f"Moderately detectable (score: {factor:.2f})")
        else:
            reasoning_parts.append(f"Difficult to detect (score: {factor:.2f})")

        factor = self._score_signal_to_noise(technique)
        factors[DetectabilityFactor.SIGNAL_TO_NOISE_RATIO] = factor
        if factor >= 0.7:
            reasoning_parts.append(f"High signal-to-noise ratio (score: {factor:.2f})")
        elif factor >= 0.4:
            reasoning_parts.append(f"Moderate signal-to-noise ratio (score: {factor:.2f})")
        else:
            reasoning_parts.append(f"Low signal-to-noise ratio (score: {factor:.2f})")

        factor = self._score_correlation_requirement(technique)
        factors[DetectabilityFactor.CORRELATION_REQUIRED] = factor
        if factor >= 0.7:
            reasoning_parts.append(f"Single-source detection possible (score: {factor:.2f})")
        elif factor >= 0.4:
            reasoning_parts.append(f"Multi-source correlation needed (score: {factor:.2f})")
        else:
            reasoning_parts.append(f"Complex correlation required (score: {factor:.2f})")

        weights = {
            DetectabilityFactor.DATA_SOURCE_AVAILABILITY: 0.30,
            DetectabilityFactor.DETECTION_COMPLEXITY: 0.30,
            DetectabilityFactor.SIGNAL_TO_NOISE_RATIO: 0.20,
            DetectabilityFactor.CORRELATION_REQUIRED: 0.20,
        }

        weighted_score = sum(
            factors.get(factor, 0.0) * weight
            for factor, weight in weights.items()
        )

        return DetectabilityScore(
            score=weighted_score,
            factors=factors,
            reasoning="; ".join(reasoning_parts)
        )

    def _score_data_source_availability(self, technique: ATTACKTechnique) -> float:
        if not technique:
            return 0.3
        data_sources = technique.data_sources
        if not data_sources:
            return 0.2
        high_value_sources = {"process", "command", "file", "network", "module", "registry"}
        matched = sum(1 for ds in data_sources if any(hv in ds.lower() for hv in high_value_sources))
        ratio = matched / len(data_sources) if data_sources else 0
        return 0.2 + (ratio * 0.7)

    def _score_detection_complexity(self, technique: ATTACKTechnique) -> float:
        if not technique:
            return 0.5
        has_high_detect = any(t in self.HIGH_DETECTABILITY_TACTICS for t in technique.tactics)
        has_low_detect = any(t in self.LOW_DETECTABILITY_TACTICS for t in technique.tactics)
        if has_high_detect and not has_low_detect:
            return 0.80
        if has_high_detect and has_low_detect:
            return 0.50
        if has_low_detect and not has_high_detect:
            return 0.30
        return 0.50

    def _score_signal_to_noise(self, technique: ATTACKTechnique) -> float:
        if not technique:
            return 0.5
        noisy_tactics = {"discovery", "reconnaissance", "execution"}
        stealthy_tactics = {"defense-evasion", "persistence", "credential-access"}
        is_noisy = any(t in noisy_tactics for t in technique.tactics)
        is_stealthy = any(t in stealthy_tactics for t in technique.tactics)
        if is_noisy and not is_stealthy:
            return 0.75
        if is_noisy and is_stealthy:
            return 0.50
        if is_stealthy and not is_noisy:
            return 0.30
        return 0.50

    def _score_correlation_requirement(self, technique: ATTACKTechnique) -> float:
        if not technique:
            return 0.5
        data_sources = technique.data_sources
        if not data_sources:
            return 0.3
        single_source_tactics = {"reconnaissance", "discovery", "execution"}
        multi_source_tactics = {"defense-evasion", "persistence", "exfiltration"}
        has_single = any(t in single_source_tactics for t in technique.tactics)
        has_multi = any(t in multi_source_tactics for t in technique.tactics)
        if has_single and not has_multi:
            return 0.80
        if has_single and has_multi:
            return 0.55
        if has_multi and not has_single:
            return 0.30
        return 0.50

