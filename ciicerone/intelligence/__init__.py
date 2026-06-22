"""Ciicerone Intelligence Module.

Real-time OSINT and reconnaissance capabilities for enhanced threat simulation.
This module provides internet-connected intelligence gathering for realistic,
up-to-date attack scenarios based on live target information.
"""

from .models import (
    IntelligenceProfile,
    CompanyIntelligence,
    SocialMediaIntelligence,
    ThreatIntelligence,
    OSINTResult,
    IntelligenceSource,
    ConfidenceLevel
)

from .services import (
    OSINTService,
    LinkedInIntelligence,
    CompanyProfileService,
    SocialMediaMonitor,
    ThreatIntelligenceService,
    DomainAnalysisService
)

from .integrations import (
    IntelligenceEngine,
    LLMIntelligenceIntegrator,
    RealTimeReconnaissanceService
)

# MITRE ATT&CK Full Coverage (Issue #42)
from .mitre_attack import (
    MITREATTACKEngine,
    ATTACKMatrix,
    ATTACKDomain,
    ATTACKTechnique,
    ATTACKSubTechnique,
    ATTACKMitigation,
    ATTACKGroup,
    ATTACKSoftware,
    ATTACKProcedure,
    ATTACKDetection,
    ATTACKDataSource,
    ATTACKCampaign,
    ENTERPRISE_TACTICS,
    TACTIC_DESCRIPTIONS,
    PLATFORMS,
    create_mitre_attack_engine,
)

# Threat Hunting & CVE Intelligence
from .threat_hunting import (
    ThreatHuntingService,
    get_threat_hunting_service,
    CVEInfo,
    CVESeverity,
    CVEResult,
    ExploitAvailability,
    ExploitIntelligence,
    HuntingHypothesis,
    HuntingHypothesisStatus,
    HuntingSession,
    HuntingSessionStatus,
    ThreatHuntType,
    KEVEntry,
)

# Threat Hunting Frameworks (PEAK, OTHF, TaHiTI, HMM, MITRE ATT&CK)
from .hunting_frameworks import (
    HuntingFramework,
    PEAKPhase,
    PEAKHuntCycle,
    PEAKPhaseData,
    TaHiTIStage,
    TaHiTIHuntProcess,
    OTHFPlaybook,
    OTHFPlaybookStatus,
    HMMLevel,
    HMMAssessment,
    HuntingLifecycle,
    HuntingLifecyclePhase,
    TTPCategory,
    TTPHuntProfile,
    ComplianceFramework,
    ComplianceViolationType,
    ComplianceHuntProfile,
    ComplianceFinding,
    IOCType,
    IOCEntry,
    IOCHuntProfile,
    IOCFinding,
)

__all__ = [
    # Models
    "IntelligenceProfile",
    "CompanyIntelligence",
    "SocialMediaIntelligence",
    "ThreatIntelligence",
    "OSINTResult",
    "IntelligenceSource",
    "ConfidenceLevel",

    # Services
    "OSINTService",
    "LinkedInIntelligence",
    "CompanyProfileService",
    "SocialMediaMonitor",
    "ThreatIntelligenceService",
    "DomainAnalysisService",

    # Integrations
    "IntelligenceEngine",
    "LLMIntelligenceIntegrator",
    "RealTimeReconnaissanceService",

    # MITRE ATT&CK Full Coverage (Issue #42)
    "MITREATTACKEngine",
    "ATTACKMatrix",
    "ATTACKDomain",
    "ATTACKTechnique",
    "ATTACKSubTechnique",
    "ATTACKMitigation",
    "ATTACKGroup",
    "ATTACKSoftware",
    "ATTACKProcedure",
    "ATTACKDetection",
    "ATTACKDataSource",
    "ATTACKCampaign",
    "ENTERPRISE_TACTICS",
    "TACTIC_DESCRIPTIONS",
    "PLATFORMS",
    "create_mitre_attack_engine",

    # Threat Hunting & CVE Intelligence
    "ThreatHuntingService",
    "get_threat_hunting_service",
    "CVEInfo",
    "CVESeverity",
    "CVEResult",
    "ExploitAvailability",
    "ExploitIntelligence",
    "HuntingHypothesis",
    "HuntingHypothesisStatus",
    "HuntingSession",
    "HuntingSessionStatus",
    "ThreatHuntType",
    "KEVEntry",

    # Threat Hunting Frameworks
    "HuntingFramework",
    "PEAKPhase",
    "PEAKHuntCycle",
    "PEAKPhaseData",
    "TaHiTIStage",
    "TaHiTIHuntProcess",
    "OTHFPlaybook",
    "OTHFPlaybookStatus",
    "HMMLevel",
    "HMMAssessment",
    "HuntingLifecycle",
    "HuntingLifecyclePhase",
    "TTPCategory",
    "TTPHuntProfile",
    "ComplianceFramework",
    "ComplianceViolationType",
    "ComplianceHuntProfile",
    "ComplianceFinding",
    "IOCType",
    "IOCEntry",
    "IOCHuntProfile",
    "IOCFinding",
]
