"""Constitutional compliance framework for BrainForge."""

import logging
from enum import Enum
from typing import Any

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


class ConstitutionalPrinciple(str, Enum):
    """Constitutional principles from BrainForge Constitution v1.1.0."""

    STRUCTURED_DATA_FOUNDATION = "structured_data_foundation"
    AI_AGENT_INTEGRATION = "ai_agent_integration"
    VERSIONING_AUDITABILITY = "versioning_auditability"
    TEST_FIRST_DEVELOPMENT = "test_first_development"
    PROGRESSIVE_ENHANCEMENT = "progressive_enhancement"
    ROLES_PERMISSIONS = "roles_permissions"
    DATA_GOVERNANCE = "data_governance"
    ERROR_HANDLING = "error_handling"
    AI_AGENT_VERSIONING = "ai_agent_versioning"
    HUMAN_IN_THE_LOOP = "human_in_the_loop"


class ComplianceValidator:
    """Validator for constitutional compliance."""

    def __init__(self):
        self.violations: list[dict[str, Any]] = []

    def validate_structured_data(self, entity_definitions: dict[str, Any]) -> bool:
        """Validate structured data foundation principle."""
        required_fields = ['id', 'created_at', 'updated_at', 'version']

        for entity_name, entity_def in entity_definitions.items():
            for field in required_fields:
                if field not in entity_def.get('fields', {}):
                    self.violations.append({
                        'principle': ConstitutionalPrinciple.STRUCTURED_DATA_FOUNDATION,
                        'entity': entity_name,
                        'issue': f"Missing required field: {field}",
                        'severity': 'high'
                    })

        return len(self.violations) == 0

    def validate_ai_agent_integration(self, agent_definitions: dict[str, Any]) -> bool:
        """Validate AI agent integration principle."""
        required_fields = ['agent_version', 'input_parameters', 'output_note_ids', 'status']

        for agent_name, agent_def in agent_definitions.items():
            for field in required_fields:
                if field not in agent_def.get('fields', {}):
                    self.violations.append({
                        'principle': ConstitutionalPrinciple.AI_AGENT_INTEGRATION,
                        'agent': agent_name,
                        'issue': f"Missing required field: {field}",
                        'severity': 'high'
                    })

        return len(self.violations) == 0

    def validate_versioning(self, versioning_definitions: dict[str, Any]) -> bool:
        """Validate versioning and auditability principle."""
        if 'version_history' not in versioning_definitions:
            self.violations.append({
                'principle': ConstitutionalPrinciple.VERSIONING_AUDITABILITY,
                'issue': "Missing version history implementation",
                'severity': 'high'
            })

        return len(self.violations) == 0

    def get_violations(self) -> list[dict[str, Any]]:
        """Get all compliance violations."""
        return self.violations

    def clear_violations(self):
        """Clear all violations."""
        self.violations = []


class ComplianceMonitor:
    """Monitor for ongoing constitutional compliance."""

    def __init__(self):
        self.validators: list[ComplianceValidator] = []
        self.compliance_log: list[dict[str, Any]] = []

    def add_validator(self, validator: ComplianceValidator):
        """Add a compliance validator."""
        self.validators.append(validator)

    def check_compliance(self, context: dict[str, Any]) -> bool:
        """Check compliance for the given context."""
        all_valid = True

        for validator in self.validators:
            # This would be implemented with specific validation logic
            # based on the context
            violations = validator.get_violations()
            if violations:
                all_valid = False
                self.compliance_log.extend(violations)

        return all_valid

    def get_compliance_report(self) -> dict[str, Any]:
        """Generate a compliance report."""
        return {
            'total_violations': len(self.compliance_log),
            'violations_by_severity': self._group_violations_by_severity(),
            'violations_by_principle': self._group_violations_by_principle(),
            'details': self.compliance_log
        }

    def _group_violations_by_severity(self) -> dict[str, int]:
        """Group violations by severity."""
        severity_counts = {}
        for violation in self.compliance_log:
            severity = violation.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        return severity_counts

    def _group_violations_by_principle(self) -> dict[str, int]:
        """Group violations by constitutional principle."""
        principle_counts = {}
        for violation in self.compliance_log:
            principle = violation.get('principle', 'unknown')
            principle_counts[principle] = principle_counts.get(principle, 0) + 1
        return principle_counts


class RequestComplianceValidator:
    """Validator for incoming request compliance with constitutional principles."""

    def __init__(self):
        self.violations: list[dict[str, Any]] = []

    def validate_request_structure(self, request: Request, expected_methods: list[str]) -> bool:
        """Validate request structure and method compliance."""
        if request.method not in expected_methods:
            self.violations.append({
                'principle': ConstitutionalPrinciple.STRUCTURED_DATA_FOUNDATION,
                'issue': f"Invalid HTTP method: {request.method}",
                'severity': 'medium',
                'actionable': f"Use one of: {', '.join(expected_methods)}"
            })
            return False
        return True

    def validate_authentication(self, request: Request) -> bool:
        """Validate authentication compliance."""
        # Check for basic authentication headers
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            self.violations.append({
                'principle': ConstitutionalPrinciple.ROLES_PERMISSIONS,
                'issue': "Missing authentication header",
                'severity': 'high',
                'actionable': "Include valid Authorization header"
            })
            return False
        return True

    def validate_content_type(self, request: Request, expected_content_type: str = "application/json") -> bool:
        """Validate content type compliance."""
        content_type = request.headers.get('Content-Type', '')
        if not content_type.startswith(expected_content_type):
            self.violations.append({
                'principle': ConstitutionalPrinciple.STRUCTURED_DATA_FOUNDATION,
                'issue': f"Invalid content type: {content_type}",
                'severity': 'medium',
                'actionable': f"Use Content-Type: {expected_content_type}"
            })
            return False
        return True

    def get_violations(self) -> list[dict[str, Any]]:
        """Get all compliance violations."""
        return self.violations

    def clear_violations(self):
        """Clear all violations."""
        self.violations = []


class ComplianceMiddleware:
    """FastAPI middleware for constitutional compliance checking."""

    def __init__(self, app):
        self.app = app
        self.validator = RequestComplianceValidator()
        self.monitor = ComplianceMonitor()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)

            # Validate request compliance
            self.validator.validate_request_structure(request, ['GET', 'POST', 'PUT', 'DELETE'])
            self.validator.validate_content_type(request)

            violations = self.validator.get_violations()
            if violations:
                # Log violations but don't block the request (progressive enhancement)
                for violation in violations:
                    logger.warning(f"Compliance violation: {violation}")

                # Add violations to monitor
                self.monitor.compliance_log.extend(violations)

            self.validator.clear_violations()

        await self.app(scope, receive, send)


def create_compliance_exception_handler():
    """Create a compliance-aware exception handler."""

    async def compliance_exception_handler(request: Request, exc: Exception):
        """Handle exceptions with compliance context."""
        compliance_context = {
            'request_method': request.method,
            'request_path': request.url.path,
            'exception_type': type(exc).__name__,
            'exception_message': str(exc)
        }

        # Log compliance violation for errors
        if isinstance(exc, HTTPException):
            if exc.status_code >= 400:
                logger.warning(f"HTTP error compliance violation: {compliance_context}")

        # Re-raise the exception (let FastAPI handle it normally)
        raise exc

    return compliance_exception_handler
