#!/usr/bin/env python3
"""
Security Validator - Validates code for security vulnerabilities and best practices.

Part of the Quality tools (validators/security_validator.py)

This security_validator.py provides:

1. Hardcoded Secret Detection - Passwords, API keys, tokens, private keys, connection strings
2. High-Entropy String Detection - Identifies potential secrets using Shannon entropy
3. SQL Injection Detection - Identifies unsafe query construction patterns
4. Command Injection Detection - Detects shell=True and unsafe subprocess calls
5. Code Injection Detection - Flags eval/exec usage
6. Weak Cryptography Detection - MD5, SHA1, weak random generators
7. Path Traversal Detection - Identifies unsafe file path handling
8. XXE Vulnerability Detection - Flags unsafe XML parsing
9. Unsafe Deserialization - Detects pickle usage
10. Insecure SSL Detection - Flags disabled certificate verification
11. Dependency Vulnerability Scanning - Integrates with pip-audit and safety
12. CWE Mapping - Maps issues to Common Weakness Enumeration IDs
13. Risk Scoring - Calculates overall security score and risk level
14. Remediation Guidance - Provides specific fix recommendations
15. False Positive Suppression - Supports # nosec comments and ignore patterns

The security validator helps identify and remediate security vulnerabilities before they reach production.
"""

import ast
import re
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

from ...shared.logger import get_logger
from ...shared.state_manager import StateManager

logger = get_logger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================

class SecuritySeverity(str, Enum):
    """Severity of security issue."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(str, Enum):
    """Type of security vulnerability."""
    # Injection
    SQL_INJECTION = "sql_injection"
    COMMAND_INJECTION = "command_injection"
    CODE_INJECTION = "code_injection"
    LDAP_INJECTION = "ldap_injection"
    XPath_INJECTION = "xpath_injection"
    NOSQL_INJECTION = "nosql_injection"
    
    # Hardcoded Secrets
    HARDCODED_PASSWORD = "hardcoded_password"
    HARDCODED_API_KEY = "hardcoded_api_key"
    HARDCODED_TOKEN = "hardcoded_token"
    HARDCODED_SECRET = "hardcoded_secret"
    HARDCODED_CREDENTIALS = "hardcoded_credentials"
    HARDCODED_PRIVATE_KEY = "hardcoded_private_key"
    
    # Cryptography
    WEAK_HASH = "weak_hash"
    WEAK_CIPHER = "weak_cipher"
    WEAK_RANDOM = "weak_random"
    INSECURE_SSL = "insecure_ssl"
    HARDCODED_SALT = "hardcoded_salt"
    MISSING_ENCRYPTION = "missing_encryption"
    
    # Authentication/Authorization
    MISSING_AUTH = "missing_auth"
    WEAK_AUTH = "weak_auth"
    INSECURE_SESSION = "insecure_session"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    MISSING_CSRF = "missing_csrf"
    OPEN_REDIRECT = "open_redirect"
    
    # Input Validation
    MISSING_VALIDATION = "missing_validation"
    XSS = "xss"
    XXE = "xxe"
    PATH_TRAVERSAL = "path_traversal"
    UNSAFE_DESERIALIZATION = "unsafe_deserialization"
    UNVALIDATED_REDIRECT = "unvalidated_redirect"
    
    # File/Resource
    INSECURE_FILE_PERMISSIONS = "insecure_file_permissions"
    TEMP_FILE_RACE = "temp_file_race"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    INFORMATION_EXPOSURE = "information_exposure"
    
    # Dependencies
    VULNERABLE_DEPENDENCY = "vulnerable_dependency"
    OUTDATED_DEPENDENCY = "outdated_dependency"
    UNPINNED_DEPENDENCY = "unpinned_dependency"
    
    # Configuration
    DEBUG_ENABLED = "debug_enabled"
    INSECURE_CONFIG = "insecure_config"
    DEFAULT_CREDENTIALS = "default_credentials"
    
    # Logging
    SENSITIVE_LOG = "sensitive_log"
    MISSING_AUDIT_LOG = "missing_audit_log"


class SecurityCategory(str, Enum):
    """Category of security issue."""
    INJECTION = "injection"
    SECRETS = "secrets"
    CRYPTOGRAPHY = "cryptography"
    AUTH = "authentication"
    INPUT_VALIDATION = "input_validation"
    FILE = "file"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    LOGGING = "logging"
    GENERAL = "general"


class Confidence(str, Enum):
    """Confidence level of detection."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class SecurityIssue:
    """A single security issue."""
    vulnerability_type: VulnerabilityType
    category: SecurityCategory
    severity: SecuritySeverity
    confidence: Confidence
    file_path: str
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    description: str = ""
    code_snippet: Optional[str] = None
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None
    remediation: Optional[str] = None
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecretFinding:
    """A detected hardcoded secret."""
    secret_type: str
    value_hash: str
    file_path: str
    line_number: int
    line_content: str
    confidence: Confidence
    entropy: float = 0.0


@dataclass
class DependencyVulnerability:
    """A vulnerable dependency."""
    package_name: str
    version: str
    vulnerability_id: str
    severity: SecuritySeverity
    description: str
    fixed_version: Optional[str] = None
    cve_id: Optional[str] = None
    references: List[str] = field(default_factory=list)


@dataclass
class SecurityReport:
    """Complete security validation report."""
    validated_at: datetime = field(default_factory=datetime.now)
    project_name: str = ""
    
    # Statistics
    total_files: int = 0
    files_with_issues: int = 0
    total_issues: int = 0
    
    # Issues by severity
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    
    # Issues by category
    issues_by_category: Dict[str, int] = field(default_factory=dict)
    issues_by_type: Dict[str, int] = field(default_factory=dict)
    
    # Detailed findings
    issues: List[SecurityIssue] = field(default_factory=list)
    secrets_found: List[SecretFinding] = field(default_factory=list)
    vulnerable_dependencies: List[DependencyVulnerability] = field(default_factory=list)
    
    # Validation
    is_valid: bool = True
    overall_score: float = 0.0
    grade: str = "A"
    risk_level: str = "low"
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityValidatorConfig:
    """Configuration for security validator."""
    project_root: Path
    
    # Secret detection
    detect_secrets: bool = True
    secret_patterns: Dict[str, re.Pattern] = field(default_factory=dict)
    min_entropy_threshold: float = 4.0
    entropy_window: int = 64
    
    # Vulnerability scanning
    scan_dependencies: bool = True
    use_bandit: bool = True
    use_safety: bool = True
    use_pip_audit: bool = True
    
    # Rules to enable/disable
    enabled_checks: Set[VulnerabilityType] = field(default_factory=lambda: set(VulnerabilityType))
    disabled_checks: Set[VulnerabilityType] = field(default_factory=set)
    
    # Severity thresholds
    fail_on_critical: bool = True
    fail_on_high: bool = True
    fail_on_medium: bool = False
    max_critical: int = 0
    max_high: int = 5
    max_medium: int = 20
    
    # Ignore patterns
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "__pycache__", "*.pyc", ".git", ".venv", "venv", "dist", "build",
        ".pytest_cache", ".mypy_cache", ".ruff_cache"
    ])
    ignore_paths: List[str] = field(default_factory=list)
    allow_test_secrets: bool = True
    
    # False positive suppression
    suppress_comment: str = "nosec"
    ignore_secrets: Set[str] = field(default_factory=set)  # Hashes to ignore
    
    # Reporting
    generate_report: bool = True
    output_format: str = "markdown"
    redact_secrets: bool = True
    include_remediation: bool = True


# ============================================================
# SECRET DETECTOR
# ============================================================

class SecretDetector:
    """Detect hardcoded secrets in source code."""
    
    # Common secret patterns
    SECRET_PATTERNS = {
        'aws_access_key': r'AKIA[0-9A-Z]{16}',
        'aws_secret_key': r'[0-9a-zA-Z/+]{40}',
        'github_token': r'gh[pousr]_[0-9a-zA-Z]{36}',
        'github_pat': r'github_pat_[0-9a-zA-Z]{22}_[0-9a-zA-Z]{59}',
        'google_api_key': r'AIza[0-9A-Za-z\\-_]{35}',
        'google_oauth': r'[0-9]+-[0-9A-Za-z_]{32}\\.apps\\.googleusercontent\\.com',
        'slack_token': r'xox[baprs]-[0-9]{12}-[0-9]{12}-[0-9a-zA-Z]{24}',
        'jwt_token': r'eyJ[a-zA-Z0-9_-]*\\.eyJ[a-zA-Z0-9_-]*\\.[a-zA-Z0-9_-]*',
        'private_key': r'-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----',
        'api_key': r'(?i)(api[_-]?key|apikey)[\s]*[=:][\s]*[\'"]?([0-9a-zA-Z]{32,})',
        'password': r'(?i)(password|passwd|pwd)[\s]*[=:][\s]*[\'"]([^\'"]{8,})[\'"]',
        'secret': r'(?i)(secret|token)[\s]*[=:][\s]*[\'"]?([0-9a-zA-Z]{16,})',
        'connection_string': r'(?i)(mongodb|postgresql|mysql|redis)://[^/\s]+',
        'basic_auth': r'https?://[^:]+:[^@]+@',
    }
    
    # High entropy patterns (base64-like strings)
    HIGH_ENTROPY_PATTERN = re.compile(r'[A-Za-z0-9+/]{20,}={0,2}')
    
    def __init__(self, config: SecurityValidatorConfig):
        self.config = config
        self._compile_patterns()
        self.findings: List[SecretFinding] = []
    
    def _compile_patterns(self):
        """Compile regex patterns."""
        self.compiled_patterns = {}
        for name, pattern in {**self.SECRET_PATTERNS, **self.config.secret_patterns}.items():
            try:
                self.compiled_patterns[name] = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            except re.error:
                logger.warning(f"Invalid regex pattern for {name}: {pattern}")
    
    def scan_file(self, file_path: Path) -> List[SecretFinding]:
        """Scan a file for secrets."""
        self.findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                # Check if line should be ignored
                if self._should_ignore_line(line):
                    continue
                
                # Check patterns
                for name, pattern in self.compiled_patterns.items():
                    for match in pattern.finditer(line):
                        secret_value = match.group(0)
                        value_hash = hashlib.sha256(secret_value.encode()).hexdigest()
                        
                        if value_hash in self.config.ignore_secrets:
                            continue
                        
                        finding = SecretFinding(
                            secret_type=name,
                            value_hash=value_hash,
                            file_path=str(file_path),
                            line_number=i,
                            line_content=line.strip(),
                            confidence=Confidence.HIGH,
                            entropy=self._calculate_entropy(secret_value)
                        )
                        self.findings.append(finding)
                
                # Check high entropy strings
                if self.config.min_entropy_threshold > 0:
                    for match in self.HIGH_ENTROPY_PATTERN.finditer(line):
                        secret_value = match.group(0)
                        entropy = self._calculate_entropy(secret_value)
                        
                        if entropy >= self.config.min_entropy_threshold:
                            value_hash = hashlib.sha256(secret_value.encode()).hexdigest()
                            
                            if value_hash in self.config.ignore_secrets:
                                continue
                            
                            finding = SecretFinding(
                                secret_type="high_entropy",
                                value_hash=value_hash,
                                file_path=str(file_path),
                                line_number=i,
                                line_content=line.strip(),
                                confidence=Confidence.MEDIUM if entropy < 5 else Confidence.HIGH,
                                entropy=entropy
                            )
                            self.findings.append(finding)
            
        except Exception as e:
            logger.warning(f"Failed to scan {file_path} for secrets: {e}")
        
        return self.findings
    
    def _should_ignore_line(self, line: str) -> bool:
        """Check if line should be ignored."""
        if self.config.allow_test_secrets:
            if 'test' in line.lower() or 'example' in line.lower() or 'mock' in line.lower():
                return True
        
        if self.config.suppress_comment and self.config.suppress_comment in line:
            return True
        
        return False
    
    def _calculate_entropy(self, data: str) -> float:
        """Calculate Shannon entropy of a string."""
        if not data:
            return 0.0
        
        import math
        entropy = 0.0
        char_counts = defaultdict(int)
        
        for char in data:
            char_counts[char] += 1
        
        length = len(data)
        for count in char_counts.values():
            probability = count / length
            entropy -= probability * math.log2(probability)
        
        return entropy


# ============================================================
# AST SECURITY VISITOR
# ============================================================

class SecurityVisitor(ast.NodeVisitor):
    """AST visitor for security vulnerability detection."""
    
    def __init__(self, config: SecurityValidatorConfig, file_path: str):
        self.config = config
        self.file_path = file_path
        self.issues: List[SecurityIssue] = []
        self.current_function: Optional[str] = None
        self.imports: Set[str] = set()
        self.variable_types: Dict[str, str] = {}
    
    def visit_Import(self, node: ast.Import):
        """Visit import."""
        for alias in node.names:
            self.imports.add(alias.name)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from import."""
        if node.module:
            self.imports.add(node.module)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        prev_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = prev_function
    
    def visit_Call(self, node: ast.Call):
        """Visit function call for security issues."""
        func_name = self._get_func_name(node)
        
        # SQL Injection
        if self._is_sql_injection_risk(node, func_name):
            self._add_issue(
                VulnerabilityType.SQL_INJECTION,
                SecurityCategory.INJECTION,
                SecuritySeverity.CRITICAL,
                Confidence.HIGH,
                node.lineno,
                "Potential SQL injection vulnerability. Use parameterized queries.",
                "Use placeholders and parameterized queries instead of string formatting.",
                "CWE-89"
            )
        
        # Command Injection
        if self._is_command_injection_risk(node, func_name):
            self._add_issue(
                VulnerabilityType.COMMAND_INJECTION,
                SecurityCategory.INJECTION,
                SecuritySeverity.CRITICAL,
                Confidence.HIGH,
                node.lineno,
                "Potential command injection vulnerability. Avoid shell=True.",
                "Use subprocess.run with list arguments and shell=False.",
                "CWE-78"
            )
        
        # Code Injection
        if self._is_code_injection_risk(node, func_name):
            self._add_issue(
                VulnerabilityType.CODE_INJECTION,
                SecurityCategory.INJECTION,
                SecuritySeverity.CRITICAL,
                Confidence.HIGH,
                node.lineno,
                "Potential code injection via eval/exec.",
                "Never use eval/exec with user input. Use safe alternatives.",
                "CWE-95"
            )
        
        # Weak Hash
        if self._is_weak_hash(node, func_name):
            self._add_issue(
                VulnerabilityType.WEAK_HASH,
                SecurityCategory.CRYPTOGRAPHY,
                SecuritySeverity.HIGH,
                Confidence.HIGH,
                node.lineno,
                f"Weak hashing algorithm '{func_name}' detected.",
                "Use SHA-256 or stronger from hashlib. For passwords, use bcrypt, scrypt, or argon2.",
                "CWE-328"
            )
        
        # Weak Random
        if self._is_weak_random(node, func_name):
            self._add_issue(
                VulnerabilityType.WEAK_RANDOM,
                SecurityCategory.CRYPTOGRAPHY,
                SecuritySeverity.HIGH,
                Confidence.HIGH,
                node.lineno,
                "Weak random number generator detected.",
                "Use secrets module or os.urandom() for cryptographic purposes.",
                "CWE-330"
            )
        
        # Path Traversal
        if self._is_path_traversal_risk(node, func_name):
            self._add_issue(
                VulnerabilityType.PATH_TRAVERSAL,
                SecurityCategory.INPUT_VALIDATION,
                SecuritySeverity.HIGH,
                Confidence.MEDIUM,
                node.lineno,
                "Potential path traversal vulnerability.",
                "Use os.path.abspath and validate paths are within intended directory.",
                "CWE-22"
            )
        
        # Unsafe Deserialization
        if self._is_unsafe_deserialization(node, func_name):
            self._add_issue(
                VulnerabilityType.UNSAFE_DESERIALIZATION,
                SecurityCategory.INPUT_VALIDATION,
                SecuritySeverity.CRITICAL,
                Confidence.HIGH,
                node.lineno,
                f"Unsafe deserialization using '{func_name}'.",
                "Never unpickle untrusted data. Use JSON or other safe formats.",
                "CWE-502"
            )
        
        # XXE Vulnerability
        if self._is_xxe_risk(node, func_name):
            self._add_issue(
                VulnerabilityType.XXE,
                SecurityCategory.INPUT_VALIDATION,
                SecuritySeverity.HIGH,
                Confidence.MEDIUM,
                node.lineno,
                "Potential XXE vulnerability in XML parsing.",
                "Use defusedxml library or disable external entity resolution.",
                "CWE-611"
            )
        
        # Insecure SSL
        if self._is_insecure_ssl(node, func_name):
            self._add_issue(
                VulnerabilityType.INSECURE_SSL,
                SecurityCategory.CRYPTOGRAPHY,
                SecuritySeverity.HIGH,
                Confidence.HIGH,
                node.lineno,
                "SSL certificate verification is disabled.",
                "Always enable SSL verification in production.",
                "CWE-295"
            )
        
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Visit assignment for hardcoded secrets."""
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            value = node.value.value
            
            # Check for secret-like variable names
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if self._is_secret_variable(target.id):
                        if len(value) > 8:  # Avoid false positives
                            self._add_issue(
                                VulnerabilityType.HARDCODED_SECRET,
                                SecurityCategory.SECRETS,
                                SecuritySeverity.CRITICAL,
                                Confidence.HIGH,
                                node.lineno,
                                f"Hardcoded secret in variable '{target.id}'.",
                                "Use environment variables or a secure secrets manager.",
                                "CWE-798"
                            )
        
        self.generic_visit(node)
    
    def visit_Constant(self, node: ast.Constant):
        """Visit constant for sensitive data."""
        if isinstance(node.value, str):
            # Check for debug flag
            if 'DEBUG' in node.value and 'True' in node.value:
                self._add_issue(
                    VulnerabilityType.DEBUG_ENABLED,
                    SecurityCategory.CONFIGURATION,
                    SecuritySeverity.MEDIUM,
                    Confidence.MEDIUM,
                    node.lineno,
                    "Debug mode appears to be enabled.",
                    "Ensure DEBUG=False in production environments.",
                    "CWE-489"
                )
        
        self.generic_visit(node)
    
    def _get_func_name(self, node: ast.Call) -> Optional[str]:
        """Get function name from call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None
    
    def _is_sql_injection_risk(self, node: ast.Call, func_name: Optional[str]) -> bool:
        """Check for SQL injection risk."""
        if not func_name:
            return False
        
        sql_funcs = {'execute', 'executemany', 'raw', 'sql'}
        if func_name not in sql_funcs:
            return False
        
        # Check for string formatting in query
        for arg in node.args:
            if isinstance(arg, (ast.BinOp, ast.JoinedStr)):
                return True
            if isinstance(arg, ast.Call) and self._get_func_name(arg) == 'format':
                return True
        
        return False
    
    def _is_command_injection_risk(self, node: ast.Call, func_name: Optional[str]) -> bool:
        """Check for command injection risk."""
        if func_name in ('system', 'popen', 'call', 'check_call', 'check_output', 'run'):
            for kw in node.keywords:
                if kw.arg == 'shell' and self._is_truthy(kw.value):
                    return True
            
            # Check if first argument is a string with potential injection
            if node.args:
                arg = node.args[0]
                if isinstance(arg, (ast.BinOp, ast.JoinedStr)):
                    return True
                if isinstance(arg, ast.Call) and self._get_func_name(arg) == 'format':
                    return True
        
        return False
    
    def _is_code_injection_risk(self, node: ast.Call, func_name: Optional[str]) -> bool:
        """Check for code injection risk."""
        return func_name in ('eval', 'exec', 'compile')
    
    def _is_weak_hash(self, node: ast.Call, func_name: Optional[str]) -> bool:
        """Check for weak hashing algorithms."""
        weak_hashes = {'md5', 'sha1'}
        
        if func_name in weak_hashes:
            return True
        
        if func_name == 'new':
            for arg in node.args:
                if isinstance(arg, ast.Constant) and arg.value in weak_hashes:
                    return True
        
        return False
    
    def _is_weak_random(self, node: ast.Call, func_name: Optional[str]) -> bool:
        """Check for weak random number generation."""
        weak_random = {'random', 'randint', 'randrange', 'choice', 'shuffle'}
        return func_name in weak_random and 'secrets' not in self.imports
    
    def _is_path_traversal_risk(self, node: ast.Call, func_name: Optional[str]) -> bool:
        """Check for path traversal risk."""
        path_funcs = {'open', 'read', 'write', 'delete', 'remove', 'rmdir', 'mkdir'}
        
        if func_name not in path_funcs:
            return False
        
        for arg in node.args[:1]:  # First argument is usually path
            if isinstance(arg, (ast.BinOp, ast.JoinedStr)):
                return True
            if isinstance(arg, ast.Call) and self._get_func_name(arg) == 'format':
                return True
            if isinstance(arg, ast.Name):  # User input
                return True
        
        return False
    
    def _is_unsafe_deserialization(self, node: ast.Call, func_name: Optional[str]) -> bool:
        """Check for unsafe deserialization."""
        unsafe_funcs = {'load', 'loads', 'Unpickler'}
        
        if func_name not in unsafe_funcs:
            return False
        
        # Check if it's pickle
        if isinstance(node.func, ast.Attribute):
            if node.func.value.id == 'pickle' if hasattr(node.func.value, 'id') else False:
                return True
        
        return False
    
    def _is_xxe_risk(self, node: ast.Call, func_name: Optional[str]) -> bool:
        """Check for XXE vulnerability."""
        if func_name in ('parse', 'parseString', 'fromstring'):
            # Check if it's an XML parser without XXE protection
            return 'defusedxml' not in self.imports and 'lxml' in str(node)
        
        return False
    
    def _is_insecure_ssl(self, node: ast.Call, func_name: Optional[str]) -> bool:
        """Check for insecure SSL configuration."""
        if func_name in ('get', 'post', 'put', 'delete', 'patch', 'request'):
            for kw in node.keywords:
                if kw.arg == 'verify' and isinstance(kw.value, ast.Constant):
                    if kw.value.value is False:
                        return True
        
        return False
    
    def _is_secret_variable(self, name: str) -> bool:
        """Check if variable name suggests it contains a secret."""
        secret_patterns = re.compile(
            r'(?i)(password|passwd|pwd|secret|token|api[_-]?key|apikey|auth|credential|private[_-]?key)',
            re.IGNORECASE
        )
        return bool(secret_patterns.search(name))
    
    def _is_truthy(self, node: ast.AST) -> bool:
        """Check if AST node evaluates to True."""
        if isinstance(node, ast.Constant):
            return bool(node.value)
        if isinstance(node, ast.NameConstant):
            return node.value is True
        return False
    
    def _add_issue(self, vuln_type: VulnerabilityType, category: SecurityCategory,
                   severity: SecuritySeverity, confidence: Confidence,
                   line_number: int, description: str, remediation: str,
                   cwe_id: Optional[str] = None):
        """Add a security issue."""
        if vuln_type in self.config.disabled_checks:
            return
        
        self.issues.append(SecurityIssue(
            vulnerability_type=vuln_type,
            category=category,
            severity=severity,
            confidence=confidence,
            file_path=self.file_path,
            line_number=line_number,
            function_name=self.current_function,
            description=description,
            remediation=remediation,
            cwe_id=cwe_id
        ))


# ============================================================
# DEPENDENCY SCANNER
# ============================================================

class DependencyScanner:
    """Scan dependencies for known vulnerabilities."""
    
    def __init__(self, config: SecurityValidatorConfig):
        self.config = config
        self.vulnerabilities: List[DependencyVulnerability] = []
    
    def scan(self) -> List[DependencyVulnerability]:
        """Scan dependencies using available tools."""
        if self.config.use_pip_audit:
            self._scan_pip_audit()
        
        if self.config.use_safety:
            self._scan_safety()
        
        return self.vulnerabilities
    
    def _scan_pip_audit(self):
        """Scan using pip-audit."""
        try:
            result = subprocess.run(
                ['pip-audit', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.config.project_root
            )
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                for vuln in data.get('vulnerabilities', []):
                    self.vulnerabilities.append(DependencyVulnerability(
                        package_name=vuln.get('name', 'unknown'),
                        version=vuln.get('version', 'unknown'),
                        vulnerability_id=vuln.get('id', ''),
                        severity=self._map_severity(vuln.get('severity', 'medium')),
                        description=vuln.get('description', ''),
                        fixed_version=vuln.get('fixed_versions', [None])[0],
                        cve_id=vuln.get('cve'),
                        references=vuln.get('references', [])
                    ))
                    
        except FileNotFoundError:
            logger.warning("pip-audit not found. Install with: pip install pip-audit")
        except Exception as e:
            logger.warning(f"pip-audit scan failed: {e}")
    
    def _scan_safety(self):
        """Scan using safety."""
        try:
            result = subprocess.run(
                ['safety', 'check', '--json'],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.config.project_root
            )
            
            if result.stdout:
                import json
                data = json.loads(result.stdout)
                
                for vuln in data.get('vulnerabilities', []):
                    self.vulnerabilities.append(DependencyVulnerability(
                        package_name=vuln.get('package_name', 'unknown'),
                        version=vuln.get('analyzed_version', 'unknown'),
                        vulnerability_id=vuln.get('vulnerability_id', ''),
                        severity=self._map_severity(vuln.get('severity', 'medium')),
                        description=vuln.get('advisory', ''),
                        fixed_version=vuln.get('fixed_version'),
                        cve_id=vuln.get('cve'),
                        references=vuln.get('more_info_url', [])
                    ))
                    
        except FileNotFoundError:
            logger.warning("safety not found. Install with: pip install safety")
        except Exception as e:
            logger.warning(f"safety scan failed: {e}")
    
    def _map_severity(self, severity: str) -> SecuritySeverity:
        """Map severity string to SecuritySeverity."""
        severity_lower = severity.lower()
        if severity_lower in ('critical', 'high'):
            return SecuritySeverity.HIGH
        elif severity_lower == 'medium':
            return SecuritySeverity.MEDIUM
        elif severity_lower == 'low':
            return SecuritySeverity.LOW
        return SecuritySeverity.MEDIUM


# ============================================================
# MAIN SECURITY VALIDATOR
# ============================================================

class SecurityValidator:
    """
    Validates code for security vulnerabilities and best practices.
    
    Features:
    - Hardcoded secret detection (passwords, API keys, tokens)
    - SQL/Command/Code injection detection
    - Weak cryptography detection (MD5, SHA1, weak random)
    - Path traversal and XXE detection
    - Unsafe deserialization detection
    - Dependency vulnerability scanning (pip-audit, safety)
    - Security scoring and risk assessment
    - CWE mapping and remediation guidance
    - Comprehensive reporting
    """
    
    def __init__(self, config: SecurityValidatorConfig):
        self.config = config
        self.secret_detector = SecretDetector(config)
        self.dependency_scanner = DependencyScanner(config)
        self.state = StateManager(config.project_root / ".ai_state" / "security_validator.json")
        
        logger.info("SecurityValidator initialized")
    
    def validate(self) -> SecurityReport:
        """Run complete security validation."""
        logger.info("Starting security validation...")
        
        report = SecurityReport(
            project_name=self.config.project_root.name
        )
        
        # Find Python files
        python_files = list(self.config.project_root.rglob("*.py"))
        report.total_files = len(python_files)
        
        files_with_issues = set()
        
        for file_path in python_files:
            if self._should_ignore(file_path):
                continue
            
            try:
                # Detect secrets
                if self.config.detect_secrets:
                    secrets = self.secret_detector.scan_file(file_path)
                    report.secrets_found.extend(secrets)
                    if secrets:
                        files_with_issues.add(str(file_path))
                
                # AST-based vulnerability detection
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                visitor = SecurityVisitor(self.config, str(file_path))
                visitor.visit(tree)
                
                for issue in visitor.issues:
                    report.issues.append(issue)
                    files_with_issues.add(str(file_path))
                    
                    # Update statistics
                    self._update_severity_stats(report, issue.severity)
                    report.issues_by_category[issue.category.value] = \
                        report.issues_by_category.get(issue.category.value, 0) + 1
                    report.issues_by_type[issue.vulnerability_type.value] = \
                        report.issues_by_type.get(issue.vulnerability_type.value, 0) + 1
                
            except Exception as e:
                logger.warning(f"Failed to validate {file_path}: {e}")
        
        report.files_with_issues = len(files_with_issues)
        report.total_issues = len(report.issues) + len(report.secrets_found)
        
        # Add secret issues to main issues list
        for secret in report.secrets_found:
            issue = SecurityIssue(
                vulnerability_type=VulnerabilityType.HARDCODED_SECRET,
                category=SecurityCategory.SECRETS,
                severity=SecuritySeverity.CRITICAL if secret.confidence == Confidence.HIGH else SecuritySeverity.HIGH,
                confidence=secret.confidence,
                file_path=secret.file_path,
                line_number=secret.line_number,
                description=f"Hardcoded {secret.secret_type} detected",
                remediation="Use environment variables or a secure secrets manager",
                cwe_id="CWE-798",
                metadata={'entropy': secret.entropy}
            )
            report.issues.append(issue)
            self._update_severity_stats(report, issue.severity)
        
        # Scan dependencies
        if self.config.scan_dependencies:
            vulns = self.dependency_scanner.scan()
            report.vulnerable_dependencies = vulns
            
            for vuln in vulns:
                report.total_issues += 1
                self._update_severity_stats(report, vuln.severity)
        
        # Calculate overall score and risk level
        report.overall_score = self._calculate_overall_score(report)
        report.grade = self._calculate_grade(report.overall_score)
        report.risk_level = self._calculate_risk_level(report)
        
        # Determine validity
        report.is_valid = self._determine_validity(report)
        
        # Generate summary and recommendations
        report.summary = self._generate_summary(report)
        report.recommendations = self._generate_recommendations(report)
        
        # Save report
        self._save_report(report)
        
        logger.info(f"Security validation complete: {report.total_issues} issues found")
        
        return report
    
    def _update_severity_stats(self, report: SecurityReport, severity: SecuritySeverity):
        """Update severity statistics."""
        if severity == SecuritySeverity.CRITICAL:
            report.critical_issues += 1
        elif severity == SecuritySeverity.HIGH:
            report.high_issues += 1
        elif severity == SecuritySeverity.MEDIUM:
            report.medium_issues += 1
        elif severity == SecuritySeverity.LOW:
            report.low_issues += 1
    
    def _should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        path_str = str(file_path)
        
        for ignore_path in self.config.ignore_paths:
            if ignore_path in path_str:
                return True
        
        for pattern in self.config.ignore_patterns:
            if pattern.replace('*', '') in path_str:
                return True
        
        return False
    
    def _calculate_overall_score(self, report: SecurityReport) -> float:
        """Calculate overall security score."""
        score = 100.0
        
        # Deduct for issues by severity
        severity_deductions = {
            SecuritySeverity.CRITICAL: 25,
            SecuritySeverity.HIGH: 10,
            SecuritySeverity.MEDIUM: 5,
            SecuritySeverity.LOW: 2
        }
        
        for issue in report.issues:
            score -= severity_deductions.get(issue.severity, 5) * (0.5 if issue.confidence == Confidence.LOW else 1.0)
        
        for vuln in report.vulnerable_dependencies:
            score -= severity_deductions.get(vuln.severity, 5)
        
        return max(0, min(100, score))
    
    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from score."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _calculate_risk_level(self, report: SecurityReport) -> str:
        """Calculate overall risk level."""
        if report.critical_issues > 0:
            return "critical"
        elif report.high_issues > 2:
            return "high"
        elif report.high_issues > 0 or report.medium_issues > 5:
            return "medium"
        elif report.medium_issues > 0 or report.low_issues > 10:
            return "low"
        else:
            return "minimal"
    
    def _determine_validity(self, report: SecurityReport) -> bool:
        """Determine if validation passes."""
        if self.config.fail_on_critical and report.critical_issues > self.config.max_critical:
            return False
        if self.config.fail_on_high and report.high_issues > self.config.max_high:
            return False
        if self.config.fail_on_medium and report.medium_issues > self.config.max_medium:
            return False
        return True
    
    def _generate_summary(self, report: SecurityReport) -> str:
        """Generate validation summary."""
        if report.is_valid:
            return f"✅ Security validation passed. Score: {report.overall_score:.1f} (Grade: {report.grade}, Risk: {report.risk_level})"
        else:
            return f"❌ Security issues found: {report.critical_issues} critical, {report.high_issues} high"
    
    def _generate_recommendations(self, report: SecurityReport) -> List[str]:
        """Generate recommendations."""
        recommendations = []
        
        if report.critical_issues > 0:
            recommendations.append(f"Address {report.critical_issues} critical security issues immediately")
        
        if report.high_issues > 0:
            recommendations.append(f"Fix {report.high_issues} high severity issues")
        
        if report.secrets_found:
            recommendations.append(f"Remove {len(report.secrets_found)} hardcoded secrets and use environment variables")
        
        if report.vulnerable_dependencies:
            recommendations.append(f"Update {len(report.vulnerable_dependencies)} vulnerable dependencies")
        
        # Most common vulnerability type
        if report.issues_by_type:
            top_type = sorted(report.issues_by_type.items(), key=lambda x: x[1], reverse=True)[0]
            recommendations.append(f"Focus on fixing {top_type[0]} vulnerabilities ({top_type[1]} occurrences)")
        
        return recommendations[:5]
    
    def _save_report(self, report: SecurityReport):
        """Save report to state."""
        reports = self.state.get('reports', [])
        
        report_data = {
            'timestamp': report.validated_at.isoformat(),
            'project': report.project_name,
            'is_valid': report.is_valid,
            'score': report.overall_score,
            'grade': report.grade,
            'risk_level': report.risk_level,
            'critical': report.critical_issues,
            'high': report.high_issues,
            'medium': report.medium_issues,
            'low': report.low_issues,
            'secrets': len(report.secrets_found),
            'vulnerable_deps': len(report.vulnerable_dependencies)
        }
        
        if not self.config.redact_secrets:
            report_data['secrets_details'] = [
                {'type': s.secret_type, 'file': s.file_path, 'line': s.line_number}
                for s in report.secrets_found
            ]
        
        reports.append(report_data)
        
        if len(reports) > 50:
            reports = reports[-50:]
        
        self.state.set('reports', reports)
        self.state.save()
    
    def export_report(self, report: SecurityReport,
                      output_path: Optional[Path] = None,
                      format: str = 'markdown') -> str:
        """Export security report."""
        
        if format == 'json':
            import json
            data = {
                'validated_at': report.validated_at.isoformat(),
                'project': report.project_name,
                'is_valid': report.is_valid,
                'score': report.overall_score,
                'grade': report.grade,
                'risk_level': report.risk_level,
                'summary': report.summary,
                'statistics': {
                    'total_files': report.total_files,
                    'files_with_issues': report.files_with_issues,
                    'total_issues': report.total_issues,
                    'critical': report.critical_issues,
                    'high': report.high_issues,
                    'medium': report.medium_issues,
                    'low': report.low_issues
                },
                'issues_by_category': report.issues_by_category,
                'issues_by_type': report.issues_by_type,
                'issues': [
                    {
                        'type': i.vulnerability_type.value,
                        'category': i.category.value,
                        'severity': i.severity.value,
                        'confidence': i.confidence.value,
                        'file': i.file_path,
                        'line': i.line_number,
                        'function': i.function_name,
                        'description': i.description,
                        'remediation': i.remediation,
                        'cwe': i.cwe_id
                    }
                    for i in report.issues[:100]
                ],
                'vulnerable_dependencies': [
                    {
                        'package': v.package_name,
                        'version': v.version,
                        'vulnerability_id': v.vulnerability_id,
                        'severity': v.severity.value,
                        'fixed_version': v.fixed_version
                    }
                    for v in report.vulnerable_dependencies
                ],
                'recommendations': report.recommendations
            }
            
            if not self.config.redact_secrets:
                data['secrets_found'] = [
                    {
                        'type': s.secret_type,
                        'file': s.file_path,
                        'line': s.line_number,
                        'confidence': s.confidence.value
                    }
                    for s in report.secrets_found
                ]
            
            return json.dumps(data, indent=2)
        
        else:  # markdown
            lines = [
                f"# Security Validation Report",
                "",
                f"**Project:** {report.project_name}",
                f"**Validated:** {report.validated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Score:** {report.overall_score:.1f} (Grade: {report.grade})",
                f"**Risk Level:** {report.risk_level.upper()}",
                f"**Status:** {report.summary}",
                "",
                "## Summary",
                "",
                f"| Severity | Count |",
                f"|----------|-------|",
                f"| 🔴 Critical | {report.critical_issues} |",
                f"| 🟠 High | {report.high_issues} |",
                f"| 🟡 Medium | {report.medium_issues} |",
                f"| 🔵 Low | {report.low_issues} |",
                f"| **Total** | {report.total_issues} |",
                "",
                f"- **Files Analyzed:** {report.total_files}",
                f"- **Files with Issues:** {report.files_with_issues}",
                f"- **Hardcoded Secrets:** {len(report.secrets_found)}",
                f"- **Vulnerable Dependencies:** {len(report.vulnerable_dependencies)}",
                "",
            ]
            
            if report.issues:
                # Group by severity
                for severity in [SecuritySeverity.CRITICAL, SecuritySeverity.HIGH, SecuritySeverity.MEDIUM]:
                    severity_issues = [i for i in report.issues if i.severity == severity]
                    if severity_issues:
                        emoji = "🔴" if severity == SecuritySeverity.CRITICAL else "🟠" if severity == SecuritySeverity.HIGH else "🟡"
                        lines.extend([
                            f"## {emoji} {severity.value.upper()} Severity Issues",
                            "",
                            "| Type | File | Line | Description | Remediation |",
                            "|------|------|------|-------------|-------------|",
                        ])
                        for issue in severity_issues[:15]:
                            file_name = Path(issue.file_path).name
                            lines.append(f"| {issue.vulnerability_type.value} | {file_name}:{issue.line_number} | {issue.line_number} | {issue.description[:50]} | {issue.remediation[:50] if issue.remediation else '-'} |")
                        lines.append("")
            
            if report.vulnerable_dependencies:
                lines.extend([
                    "## 📦 Vulnerable Dependencies",
                    "",
                    "| Package | Version | Vulnerability | Severity | Fixed Version |",
                    "|---------|---------|---------------|----------|---------------|",
                ])
                for vuln in report.vulnerable_dependencies[:20]:
                    lines.append(f"| {vuln.package_name} | {vuln.version} | {vuln.vulnerability_id} | {vuln.severity.value} | {vuln.fixed_version or 'N/A'} |")
                lines.append("")
            
            if report.issues_by_category:
                lines.extend([
                    "## Categories",
                    "",
                    "| Category | Count |",
                    "|----------|-------|",
                ])
                for category, count in sorted(report.issues_by_category.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"| {category} | {count} |")
                lines.append("")
            
            if report.recommendations:
                lines.extend([
                    "## Recommendations",
                    "",
                ])
                for rec in report.recommendations:
                    lines.append(f"- {rec}")
                lines.append("")
            
            content = '\n'.join(lines)
        
        if output_path:
            output_path.write_text(content)
        
        return content
    
    def close(self):
        """Clean up resources."""
        self.state.save()
        logger.info("SecurityValidator closed")


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main():
    """CLI entry point for security validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate code for security vulnerabilities")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", "-o", type=Path, help="Output report path")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--no-secrets", action="store_true", help="Disable secret detection")
    parser.add_argument("--no-deps", action="store_true", help="Disable dependency scanning")
    parser.add_argument("--fail-on-medium", action="store_true", help="Fail on medium severity issues")
    parser.add_argument("--redact-secrets", action="store_true", default=True)
    parser.add_argument("--max-critical", type=int, default=0)
    parser.add_argument("--max-high", type=int, default=5)
    
    args = parser.parse_args()
    
    config = SecurityValidatorConfig(
        project_root=args.project_root,
        detect_secrets=not args.no_secrets,
        scan_dependencies=not args.no_deps,
        fail_on_medium=args.fail_on_medium,
        redact_secrets=args.redact_secrets,
        max_critical=args.max_critical,
        max_high=args.max_high
    )
    
    validator = SecurityValidator(config)
    
    report = validator.validate()
    
    output = validator.export_report(report, args.output, args.format)
    
    if not args.output:
        print(output)
    else:
        print(f"Report saved to {args.output}")
    
    print(f"\n{report.summary}")
    
    if config.fail_on_critical and not report.is_valid:
        exit(1)
    
    validator.close()


if __name__ == "__main__":
    main()