from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import ValidationError
from yaml.constructor import ConstructorError
from yaml.parser import ParserError
from yaml.scanner import ScannerError

from ciicerone.authorization.models import WorkflowConfig


logger = logging.getLogger(__name__)


class WorkflowConfigError(Exception):
    pass


class WorkflowParseError(WorkflowConfigError):
    pass


class WorkflowValidationError(WorkflowConfigError):
    def __init__(self, message: str, errors: Optional[list[dict[str, Any]]] = None):
        super().__init__(message)
        self.errors = errors or []


class WorkflowConfigLoader:
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode

    def _load_yaml(self, content: str) -> dict[str, Any]:
        try:
            data = yaml.safe_load(content)
        except (ParserError, ScannerError) as e:
            raise WorkflowParseError(f"YAML syntax error: {e}")
        except ConstructorError as e:
            raise WorkflowParseError(f"YAML construction error: {e}")
        if not isinstance(data, dict):
            raise WorkflowParseError("YAML root must be a mapping")
        return data

    def validate(self, data: dict[str, Any]) -> WorkflowConfig:
        try:
            return WorkflowConfig.model_validate(data)
        except ValidationError as e:
            errors = []
            for err in e.errors():
                location = " -> ".join(str(loc) for loc in err["loc"])
                errors.append({"location": location, "message": err["msg"], "type": err["type"]})
            raise WorkflowValidationError(
                f"Workflow config validation failed with {len(errors)} error(s)",
                errors,
            )

    def load(self, path: str | Path) -> WorkflowConfig:
        path = Path(path)
        if not path.exists():
            raise WorkflowConfigError(f"Workflow config not found: {path}")
        if not path.is_file():
            raise WorkflowConfigError(f"Path is not a file: {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if not content.strip():
                raise WorkflowConfigError(f"Workflow config file is empty: {path}")
            data = self._load_yaml(content)
            return self.validate(data)
        except PermissionError:
            raise WorkflowConfigError(f"Permission denied: {path}")
        except OSError as e:
            raise WorkflowConfigError(f"Error reading {path}: {e}")

    def loads(self, content: str) -> WorkflowConfig:
        if not content.strip():
            raise WorkflowConfigError("Empty workflow configuration content")
        data = self._load_yaml(content)
        return self.validate(data)

    def load_directory(self, directory: str | Path) -> list[WorkflowConfig]:
        directory = Path(directory)
        if not directory.exists():
            raise WorkflowConfigError(f"Directory not found: {directory}")
        if not directory.is_dir():
            raise WorkflowConfigError(f"Path is not a directory: {directory}")

        configs: list[WorkflowConfig] = []
        for yaml_file in sorted(directory.rglob("*.yaml")) + sorted(directory.rglob("*.yml")):
            try:
                configs.append(self.load(yaml_file))
                logger.info(f"Loaded workflow config: {yaml_file}")
            except WorkflowConfigError as e:
                logger.error(f"Failed to load {yaml_file}: {e}")
                if self.strict_mode:
                    raise
        return configs
