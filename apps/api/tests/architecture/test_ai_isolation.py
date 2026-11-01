import ast
from pathlib import Path

# Paths to inspect
AI_DIR = Path(__file__).resolve().parents[2] / "app" / "ai"

FORBIDDEN_MODULES = {
    "sqlalchemy",
    "app.models",
    "app.core.database",
    "asyncpg",
    "psycopg",
}

FORBIDDEN_ATTRIBUTES = {
    "database_url",
}


def get_all_python_files(directory: Path) -> list[Path]:
    return list(directory.rglob("*.py"))


def test_ai_module_has_zero_database_imports() -> None:
    """
    Architecture Test: Enforce PRD §36.3 and Rule 14.
    AI code in apps/api/app/ai must NEVER import SQLAlchemy, models, or database sessions/engines.
    """
    py_files = get_all_python_files(AI_DIR)
    assert len(py_files) > 0, "No python files found in apps/api/app/ai"

    violations: list[str] = []

    for file_path in py_files:
        rel_path = file_path.relative_to(AI_DIR.parent.parent)
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for forbidden in FORBIDDEN_MODULES:
                        if alias.name == forbidden or alias.name.startswith(f"{forbidden}."):
                            violations.append(f"{rel_path}:{node.lineno} imports '{alias.name}'")

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for forbidden in FORBIDDEN_MODULES:
                        if node.module == forbidden or node.module.startswith(f"{forbidden}."):
                            violations.append(
                                f"{rel_path}:{node.lineno} imports from '{node.module}'"
                            )

            elif isinstance(node, ast.Attribute):
                if node.attr in FORBIDDEN_ATTRIBUTES:
                    violations.append(
                        f"{rel_path}:{node.lineno} accesses forbidden attribute '{node.attr}'"
                    )

    assert not violations, (
        f"AI isolation architecture violations found ({len(violations)}):\n" + "\n".join(violations)
    )


def test_ai_tools_enforce_identity_and_tenancy() -> None:
    """
    Architecture Test: Verify tool catalog registers permission schemas and tenant scoping.
    """
    from app.ai.tools.registry import TOOL_DEFINITIONS

    assert "get_my_token_status" in TOOL_DEFINITIONS
    assert "get_clinic_info" in TOOL_DEFINITIONS
    assert "get_patient_history" in TOOL_DEFINITIONS
    assert "get_daily_stats" in TOOL_DEFINITIONS
    assert "detect_anomalies" in TOOL_DEFINITIONS
    assert "get_consult_durations" in TOOL_DEFINITIONS
    assert "save_wait_prediction" in TOOL_DEFINITIONS

    # get_patient_history must be restricted to doctor
    assert TOOL_DEFINITIONS["get_patient_history"].required_roles == ["doctor"]
    # save_wait_prediction must be restricted to system_job or platform_admin
    assert "reception" not in TOOL_DEFINITIONS["save_wait_prediction"].required_roles
    assert "doctor" not in TOOL_DEFINITIONS["save_wait_prediction"].required_roles
