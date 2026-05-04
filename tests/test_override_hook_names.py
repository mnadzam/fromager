"""Verify that hook name constants stay in sync with actual usage.

Uses Python's Abstract Syntax Tree (AST) module to parse source files and
find every string literal passed to hook-dispatch functions, then checks
that the declared constants match.
"""

import ast
import pathlib

from fromager.hooks import GLOBAL_HOOK_NAMES
from fromager.overrides import OVERRIDE_HOOK_NAMES

SRC_DIR = pathlib.Path(__file__).parent.parent / "src" / "fromager"


def _called_function_name(node: ast.Call) -> str | None:
    """Return the simple name of the called function, or None."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _collect_string_arg(
    source_files: list[pathlib.Path],
    func_names: set[str],
    arg_index: int,
) -> set[str]:
    """Find every string literal passed at ``arg_index`` to calls of ``func_names``.

    Scans the AST of each file for calls like ``func("hook_name", ...)``
    and returns the set of string values found at the given position.
    """
    found: set[str] = set()
    for path in source_files:
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if _called_function_name(node) not in func_names:
                continue
            if len(node.args) <= arg_index:
                continue
            arg = node.args[arg_index]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                found.add(arg.value)
    return found


def test_override_hook_names_match_usage() -> None:
    """OVERRIDE_HOOK_NAMES must list every hook passed to
    find_override_method / find_and_invoke across the source tree."""
    source_files = [
        p
        for p in SRC_DIR.rglob("*.py")
        if p.name != "overrides.py"  # skip the forwarding call (uses a variable)
    ]
    used = _collect_string_arg(
        source_files,
        {"find_and_invoke", "find_override_method"},
        arg_index=1,
    )
    registered = set(OVERRIDE_HOOK_NAMES)
    missing = used - registered
    extra = registered - used
    assert not missing, (
        f"Hooks used in source but missing from OVERRIDE_HOOK_NAMES: {missing}"
    )
    assert not extra, f"Hooks in OVERRIDE_HOOK_NAMES but not used in source: {extra}"


def test_global_hook_names_match_usage() -> None:
    """GLOBAL_HOOK_NAMES must list every hook passed to _get_hooks in hooks.py."""
    used = _collect_string_arg(
        [SRC_DIR / "hooks.py"],
        {"_get_hooks"},
        arg_index=0,
    )
    registered = set(GLOBAL_HOOK_NAMES)
    missing = used - registered
    extra = registered - used
    assert not missing, (
        f"Hooks used in hooks.py but missing from GLOBAL_HOOK_NAMES: {missing}"
    )
    assert not extra, f"Hooks in GLOBAL_HOOK_NAMES but not used in hooks.py: {extra}"
