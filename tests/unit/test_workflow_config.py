"""Unit tests for the workflow configuration system."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from ciicerone.authorization.models import (
    ApprovalChain,
    ApprovalConfig,
    ApprovalRole,
    ApprovalStep,
    OperationType,
    WorkflowConfig,
)
from ciicerone.authorization.workflow_config import (
    WorkflowConfigLoader,
    WorkflowConfigError,
    WorkflowParseError,
    WorkflowValidationError,
)


SAMPLE_CONFIG = """
version: "1.0"
metadata:
  name: test-workflows
  description: Test configuration

approval:
  default_timeout_minutes: 1440
  max_escalations: 3
  audit_enabled: true
  chains:
    - name: test-chain
      description: Test approval chain
      operation_types:
        - threat_hunt
      steps:
        - name: step-1
          description: First approval step
          required_roles:
            - team_lead
          min_approvers: 1
          timeout_minutes: 240
          require_justification: true
"""


class TestWorkflowConfigModels:
    def test_approval_step_defaults(self):
        step = ApprovalStep(name="test-step")
        assert step.name == "test-step"
        assert step.min_approvers == 1
        assert step.timeout_minutes == 240
        assert step.require_justification is True
        assert step.require_mfa is False
        assert step.allow_skip is False

    def test_approval_chain_with_steps(self):
        step = ApprovalStep(name="review", required_roles=[ApprovalRole.TEAM_LEAD])
        chain = ApprovalChain(
            name="test-chain",
            operation_types=[OperationType.THREAT_HUNT],
            steps=[step],
        )
        assert chain.name == "test-chain"
        assert len(chain.steps) == 1
        assert chain.steps[0].name == "review"

    def test_workflow_config_full(self):
        step = ApprovalStep(name="approve", required_roles=[ApprovalRole.MANAGER])
        chain = ApprovalChain(
            name="main",
            operation_types=[OperationType.INCIDENT_RESPONSE],
            steps=[step],
        )
        config = ApprovalConfig(chains=[chain])
        workflow = WorkflowConfig(approval=config)
        assert workflow.version == "1.0"
        assert len(workflow.approval.chains) == 1
        assert workflow.approval.chains[0].name == "main"

    def test_operation_type_enum_values(self):
        assert OperationType.THREAT_HUNT.value == "threat_hunt"
        assert OperationType.INCIDENT_RESPONSE.value == "incident_response"
        assert OperationType.SYSTEM_ADMIN.value == "system_admin"

    def test_approval_role_enum_values(self):
        assert ApprovalRole.TEAM_LEAD.value == "team_lead"
        assert ApprovalRole.MANAGER.value == "manager"
        assert ApprovalRole.ADMIN.value == "admin"

    def test_approval_chain_serialization(self):
        step = ApprovalStep(name="approve", required_roles=[ApprovalRole.ADMIN])
        chain = ApprovalChain(
            name="critical",
            operation_types=[OperationType.SYSTEM_ADMIN],
            steps=[step],
        )
        data = chain.model_dump()
        assert data["name"] == "critical"
        assert data["steps"][0]["name"] == "approve"
        assert data["steps"][0]["required_roles"] == ["admin"]


class TestWorkflowConfigLoader:
    def test_loads_valid_yaml(self):
        loader = WorkflowConfigLoader()
        yaml_content = """
version: "1.0"
approval:
  chains:
    - name: test
      operation_types:
        - threat_hunt
      steps:
        - name: review
          required_roles:
            - team_lead
"""
        config = loader.loads(yaml_content)
        assert config.version == "1.0"
        assert len(config.approval.chains) == 1
        assert config.approval.chains[0].name == "test"

    def test_loads_empty_content_raises_error(self):
        loader = WorkflowConfigLoader()
        with pytest.raises(WorkflowConfigError, match="Empty"):
            loader.loads("")

    def test_loads_invalid_yaml_raises_parse_error(self):
        loader = WorkflowConfigLoader()
        with pytest.raises(WorkflowParseError):
            loader.loads("{invalid: yaml: [}")

    def test_loads_missing_approval_field_raises_validation_error(self):
        loader = WorkflowConfigLoader()
        with pytest.raises(WorkflowValidationError):
            loader.loads("version: '1.0'\nmetadata: {}")

    def test_loads_invalid_operation_type_raises_validation_error(self):
        loader = WorkflowConfigLoader()
        with pytest.raises(WorkflowValidationError):
            loader.loads("""
version: "1.0"
approval:
  chains:
    - name: bad
      operation_types:
        - invalid_op
      steps:
        - name: step1
          required_roles:
            - team_lead
""")

    def test_load_from_file(self, tmp_path):
        loader = WorkflowConfigLoader()
        config_file = tmp_path / "workflows.yaml"
        config_file.write_text("""
version: "1.0"
approval:
  chains:
    - name: file-test
      operation_types:
        - vulnerability_scan
      steps:
        - name: review
          required_roles:
            - team_lead
""")
        config = loader.load(config_file)
        assert config.approval.chains[0].name == "file-test"

    def test_load_nonexistent_file_raises_error(self):
        loader = WorkflowConfigLoader()
        with pytest.raises(WorkflowConfigError, match="not found"):
            loader.load("/nonexistent/path.yaml")

    def test_load_empty_file_raises_error(self, tmp_path):
        loader = WorkflowConfigLoader()
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("")
        with pytest.raises(WorkflowConfigError, match="empty"):
            loader.load(empty_file)

    def test_load_directory_loads_all_yaml_files(self, tmp_path):
        loader = WorkflowConfigLoader(strict_mode=False)
        config_dir = tmp_path / "workflows"
        config_dir.mkdir()

        valid = config_dir / "valid.yaml"
        valid.write_text("""
version: "1.0"
approval:
  chains:
    - name: chain-1
      operation_types:
        - threat_hunt
      steps:
        - name: step1
          required_roles:
            - team_lead
""")

        configs = loader.load_directory(config_dir)
        assert len(configs) == 1
        assert configs[0].approval.chains[0].name == "chain-1"

    def test_load_directory_skips_invalid_in_non_strict_mode(self, tmp_path):
        loader = WorkflowConfigLoader(strict_mode=False)
        config_dir = tmp_path / "workflows"
        config_dir.mkdir()

        valid = config_dir / "valid.yaml"
        valid.write_text("""
version: "1.0"
approval:
  chains:
    - name: good
      operation_types:
        - threat_hunt
      steps:
        - name: step1
          required_roles:
            - team_lead
""")
        invalid = config_dir / "invalid.yaml"
        invalid.write_text("not: valid: yaml: [[[")

        configs = loader.load_directory(config_dir)
        assert len(configs) == 1
        assert configs[0].approval.chains[0].name == "good"

    def test_load_directory_strict_mode_raises_on_invalid(self, tmp_path):
        loader = WorkflowConfigLoader(strict_mode=True)
        config_dir = tmp_path / "workflows"
        config_dir.mkdir()

        invalid = config_dir / "bad.yaml"
        invalid.write_text("not: valid: yaml: [[[")

        with pytest.raises(WorkflowConfigError):
            loader.load_directory(config_dir)

    def test_loads_with_multiple_chains(self):
        loader = WorkflowConfigLoader()
        config = loader.loads("""
version: "1.0"
approval:
  chains:
    - name: hunt-chain
      operation_types:
        - threat_hunt
      steps:
        - name: lead-review
          required_roles:
            - team_lead
    - name: ir-chain
      operation_types:
        - incident_response
      steps:
        - name: soc-review
          required_roles:
            - soc_analyst
""")
        assert len(config.approval.chains) == 2
        assert config.approval.chains[0].name == "hunt-chain"
        assert config.approval.chains[1].name == "ir-chain"

    def test_chain_with_mfa_requirement(self):
        step = ApprovalStep(
            name="mfa-step",
            required_roles=[ApprovalRole.ADMIN],
            require_mfa=True,
            timeout_minutes=30,
        )
        assert step.require_mfa is True
        assert step.timeout_minutes == 30

    def test_chain_with_escalation(self):
        step1 = ApprovalStep(
            name="first",
            required_roles=[ApprovalRole.TEAM_LEAD],
            escalation_step="second",
        )
        step2 = ApprovalStep(
            name="second",
            required_roles=[ApprovalRole.MANAGER],
        )
        chain = ApprovalChain(
            name="escalation-test",
            operation_types=[OperationType.CONFIG_CHANGE],
            steps=[step1, step2],
            escalation_chain="emergency-chain",
        )
        assert chain.steps[0].escalation_step == "second"
        assert chain.escalation_chain == "emergency-chain"

    def test_require_mfa_for_operation_types(self):
        config = ApprovalConfig(
            require_mfa_for=[OperationType.SYSTEM_ADMIN, OperationType.DATA_EXPORT],
        )
        assert OperationType.SYSTEM_ADMIN in config.require_mfa_for
        assert OperationType.DATA_EXPORT in config.require_mfa_for
        assert OperationType.THREAT_HUNT not in config.require_mfa_for

    def test_notify_channels_default(self):
        config = ApprovalConfig(chains=[])
        assert "log" in config.notify_channels

    def test_workflow_config_serialization_roundtrip(self):
        step = ApprovalStep(name="roundtrip-step", required_roles=[ApprovalRole.COMPLIANCE_OFFICER])
        chain = ApprovalChain(
            name="compliance-chain",
            operation_types=[OperationType.DATA_EXPORT],
            steps=[step],
        )
        config = ApprovalConfig(chains=[chain])
        workflow = WorkflowConfig(approval=config)

        data = workflow.model_dump()
        restored = WorkflowConfig.model_validate(data)
        assert restored.approval.chains[0].name == "compliance-chain"
        assert restored.approval.chains[0].steps[0].required_roles[0] == ApprovalRole.COMPLIANCE_OFFICER

    def test_approval_step_allow_skip(self):
        step = ApprovalStep(name="optional-step", allow_skip=True, min_approvers=0)
        assert step.allow_skip is True
        assert step.min_approvers == 0

    def test_chain_parallel_approval(self):
        step1 = ApprovalStep(name="reviewer-1", required_roles=[ApprovalRole.TEAM_LEAD])
        step2 = ApprovalStep(name="reviewer-2", required_roles=[ApprovalRole.MANAGER])
        chain = ApprovalChain(
            name="parallel-test",
            operation_types=[OperationType.VULNERABILITY_SCAN],
            steps=[step1, step2],
            allow_parallel=True,
        )
        assert chain.allow_parallel is True

    def test_audit_level_default(self):
        step = ApprovalStep(name="audit-step", required_roles=[ApprovalRole.SOC_ANALYST])
        chain = ApprovalChain(
            name="audit-chain",
            operation_types=[OperationType.THREAT_HUNT],
            steps=[step],
        )
        assert chain.audit_level == "detailed"

    def test_notify_channels_config(self):
        config = ApprovalConfig(
            notify_channels=["log", "email", "slack"],
        )
        assert "email" in config.notify_channels
        assert "slack" in config.notify_channels
