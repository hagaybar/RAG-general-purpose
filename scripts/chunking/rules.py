import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List  # Added List and Optional


@dataclass
class ChunkRule:
    split_strategy: str
    min_tokens: int | None = None
    max_tokens: int | None = None
    overlap: int | None = None  # Ensuring type hint is consistent
    notes: Optional[str] = None
    # Keep for compatibility if some rules still use it
    min_chunk_size: Optional[int] = None


_rules_data = None
_rules_file_path = (
    Path(__file__).parent.parent.parent / "configs" / "chunk_rules.yaml"
)


def _load_rules_if_needed():
    """Loads rules from YAML if not already loaded."""
    global _rules_data
    if _rules_data is None:
        # Primary path based on script location
        path_to_try = _rules_file_path
        if not path_to_try.exists():
            # Fallback path relative to a potential 'app' root
            # if running from a different working directory.
            path_to_try = Path("configs") / "chunk_rules.yaml"
            if not path_to_try.exists():
                raise FileNotFoundError(
                    f"Rules file not found at {_rules_file_path} or {path_to_try}"
                )
        with open(path_to_try, 'r') as f:
            _rules_data = yaml.safe_load(f)


def get_rule(doc_type: str) -> ChunkRule:
    """
    Retrieves the chunking rule for a given document type.

    Args:
        doc_type: The type of the document (e.g., 'email', 'pdf').

    Returns:
        A ChunkRule object for the specified type.

    Raises:
        KeyError: If the document type is not found and no default.
        FileNotFoundError: If the rules YAML file is not found.
    """
    _load_rules_if_needed()
    assert _rules_data is not None, "Rules data should be loaded"

    rule_dict = _rules_data.get(doc_type)
    if not rule_dict:
        # Fallback to a default rule if specific doc_type not found
        default_rule_dict = _rules_data.get("default")
        if not default_rule_dict:
            raise KeyError(
                f"Document type '{doc_type}' not found and no 'default' "
                "rule defined in chunking rules."
            )
        rule_dict = default_rule_dict
        # Optionally, add a note that default rule is being used
        # notes = rule_dict.get('notes', '')
        # rule_dict['notes'] = f"{notes} (Using default for {doc_type})".strip()

    # Handle potential 'min_chunk_size' for backward compatibility,
    # though 'token_bounds' is preferred.
    # This logic can be expanded if direct conversion is needed here.
    # For now, ChunkRule dataclass handles optionality.

    return ChunkRule(**rule_dict)


def get_all_rules() -> dict[str, ChunkRule]:
    """
    Retrieves all chunking rules.

    Returns:
        A dictionary mapping document types to ChunkRule objects.

    Raises:
        FileNotFoundError: If the rules YAML file is not found.
    """
    _load_rules_if_needed()
    assert _rules_data is not None, "Rules data should be loaded"

    all_chunk_rules = {}
    for doc_type, rule_dict in _rules_data.items():
        all_chunk_rules[doc_type] = ChunkRule(**rule_dict)
    return all_chunk_rules


def get_all_doc_types() -> list[str]:
    """
    Retrieves all document types defined in the chunking rules.

    Returns:
        A list of document type strings.

    Raises:
        FileNotFoundError: If the rules YAML file is not found.
    """
    rules = get_all_rules()
    return list(rules.keys())

