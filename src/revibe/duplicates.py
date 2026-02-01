"""Duplicate file detection for Revibe."""

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple

from revibe.analyzer import FileAnalysis
from revibe.metrics import DuplicateGroup


def compute_file_hash(path: Path) -> str:
    """Compute MD5 hash of file contents."""
    try:
        content = path.read_bytes()
        return hashlib.md5(content).hexdigest()
    except OSError:
        return ""


def find_exact_duplicates(analyses: List[FileAnalysis]) -> List[DuplicateGroup]:
    """
    Find files that are exact copies (same content hash).

    Args:
        analyses: List of FileAnalysis objects

    Returns:
        List of DuplicateGroup for exact duplicates
    """
    hash_to_files: Dict[str, List[str]] = defaultdict(list)

    for analysis in analyses:
        file_hash = compute_file_hash(analysis.source_file.path)
        if file_hash:
            hash_to_files[file_hash].append(analysis.source_file.relative_path)

    # Filter to groups with more than one file
    duplicates = []
    for file_hash, files in hash_to_files.items():
        if len(files) > 1:
            duplicates.append(DuplicateGroup(
                files=sorted(files),
                is_exact=True,
                similarity=1.0,
            ))

    return duplicates


def calculate_similarity(analysis1: FileAnalysis, analysis2: FileAnalysis) -> float:
    """
    Calculate similarity between two files based on:
    - Line count similarity
    - Shared function names
    - Shared class names

    Returns a score from 0.0 to 1.0.
    """
    # Line count similarity (up to 0.3)
    lines1 = analysis1.code_lines
    lines2 = analysis2.code_lines

    if lines1 == 0 and lines2 == 0:
        line_sim = 1.0
    elif lines1 == 0 or lines2 == 0:
        line_sim = 0.0
    else:
        line_sim = min(lines1, lines2) / max(lines1, lines2)

    # Function name overlap (up to 0.5)
    funcs1 = set(f.name for f in analysis1.functions)
    funcs2 = set(f.name for f in analysis2.functions)

    if not funcs1 and not funcs2:
        func_sim = 0.0
    elif not funcs1 or not funcs2:
        func_sim = 0.0
    else:
        shared_funcs = funcs1 & funcs2
        all_funcs = funcs1 | funcs2
        func_sim = len(shared_funcs) / len(all_funcs)

    # Class name overlap (up to 0.2)
    classes1 = set(c.name for c in analysis1.classes)
    classes2 = set(c.name for c in analysis2.classes)

    if not classes1 and not classes2:
        class_sim = 0.0
    elif not classes1 or not classes2:
        class_sim = 0.0
    else:
        shared_classes = classes1 & classes2
        all_classes = classes1 | classes2
        class_sim = len(shared_classes) / len(all_classes)

    # Weighted combination
    similarity = (line_sim * 0.3) + (func_sim * 0.5) + (class_sim * 0.2)

    return similarity


def find_near_duplicates(
    analyses: List[FileAnalysis],
    threshold: float = 0.5,
) -> List[DuplicateGroup]:
    """
    Find files that are near-duplicates (similar structure).

    Args:
        analyses: List of FileAnalysis objects
        threshold: Minimum similarity score to consider as near-duplicate

    Returns:
        List of DuplicateGroup for near-duplicates
    """
    # Skip very small files
    valid_analyses = [a for a in analyses if a.code_lines >= 10]

    if len(valid_analyses) < 2:
        return []

    # Group by language for comparison
    by_language: Dict[str, List[FileAnalysis]] = defaultdict(list)
    for analysis in valid_analyses:
        by_language[analysis.source_file.language].append(analysis)

    near_duplicates = []
    processed: Set[Tuple[str, str]] = set()

    for language, lang_analyses in by_language.items():
        if len(lang_analyses) < 2:
            continue

        for i, analysis1 in enumerate(lang_analyses):
            for analysis2 in lang_analyses[i + 1:]:
                path1 = analysis1.source_file.relative_path
                path2 = analysis2.source_file.relative_path

                pair = tuple(sorted([path1, path2]))
                if pair in processed:
                    continue
                processed.add(pair)

                similarity = calculate_similarity(analysis1, analysis2)

                if similarity >= threshold:
                    near_duplicates.append(DuplicateGroup(
                        files=[path1, path2],
                        is_exact=False,
                        similarity=similarity,
                    ))

    # Sort by similarity (highest first)
    near_duplicates.sort(key=lambda g: g.similarity, reverse=True)

    return near_duplicates


def find_all_duplicates(
    analyses: List[FileAnalysis],
    near_duplicate_threshold: float = 0.5,
) -> List[DuplicateGroup]:
    """
    Find all duplicate files (exact and near-duplicates).

    Args:
        analyses: List of FileAnalysis objects
        near_duplicate_threshold: Minimum similarity for near-duplicates

    Returns:
        Combined list of DuplicateGroup objects
    """
    exact = find_exact_duplicates(analyses)
    near = find_near_duplicates(analyses, near_duplicate_threshold)

    # Remove near-duplicates that are also exact duplicates
    exact_file_sets = [frozenset(g.files) for g in exact]
    filtered_near = [
        g for g in near
        if frozenset(g.files) not in exact_file_sets
    ]

    # Combine with exact duplicates first
    return exact + filtered_near


def format_duplicate_report(groups: List[DuplicateGroup]) -> str:
    """Format duplicate groups for display."""
    if not groups:
        return "No duplicate files detected."

    lines = []

    exact_groups = [g for g in groups if g.is_exact]
    near_groups = [g for g in groups if not g.is_exact]

    if exact_groups:
        lines.append(f"Exact Duplicates ({len(exact_groups)} groups):")
        for i, group in enumerate(exact_groups, 1):
            lines.append(f"  Group {i}:")
            for f in group.files:
                lines.append(f"    - {f}")

    if near_groups:
        lines.append(f"\nNear Duplicates ({len(near_groups)} pairs):")
        for group in near_groups[:10]:  # Limit output
            lines.append(
                f"  {group.files[0]} <-> {group.files[1]} ({group.similarity:.0%} similar)"
            )

    return "\n".join(lines)
