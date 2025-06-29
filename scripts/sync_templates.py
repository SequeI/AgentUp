#!/usr/bin/env python3
"""Sync reference implementation changes to templates."""
import difflib
import re
from pathlib import Path
from typing import List, Tuple

# Mapping of source files to template files
FILE_MAPPINGS = {
    "src/agent/api.py": "src/agentup/templates/api.py.j2",
    "src/agent/handlers.py": "src/agentup/templates/handlers.py.j2",
    "src/agent/config_loader.py": "src/agentup/templates/config_loader.py.j2",
    "src/agent/middleware.py": "src/agentup/templates/middleware.py.j2",
    "src/agent/services.py": "src/agentup/templates/services.py.j2",
    "src/agent/context.py": "src/agentup/templates/context.py.j2",
    "src/agent/multimodal.py": "src/agentup/templates/multimodal.py.j2",
    "src/agent/handlers_multimodal.py": "src/agentup/templates/handlers_multimodal.py.j2",
    "src/agent/handlers_with_services.py": "src/agentup/templates/handlers_with_services.py.j2",
}

# Patterns to convert to template variables
TEMPLATE_CONVERSIONS = [
    (r'"FastAPI A2A Agent"', '"{{ project_name }}"'),
    (r"'FastAPI A2A Agent'", "'{{ project_name }}'"),
    (r'fastapi_a2a_agent', '{{ project_name_snake }}'),
    (r'FastAPIAgent', '{{ project_name_title }}'),
    (r'"A FastAPI-based A2A agent"', '"{{ description }}"'),
]


def check_sync_status() -> List[Tuple[str, str, bool]]:
    """Check which files are out of sync."""
    results = []

    for src_path, template_path in FILE_MAPPINGS.items():
        src_file = Path(src_path)
        tpl_file = Path(template_path)

        if not src_file.exists():
            results.append((src_path, template_path, False))
            continue

        if not tpl_file.exists():
            results.append((src_path, template_path, False))
            continue

        # Read and normalize content
        src_content = src_file.read_text()
        tpl_content = tpl_file.read_text()

        # Apply template conversions to source for comparison
        normalized_src = src_content
        for pattern, replacement in TEMPLATE_CONVERSIONS:
            normalized_src = re.sub(pattern, replacement, normalized_src)

        # Remove conditional blocks for comparison
        tpl_normalized = re.sub(r'\{\{.*?if.*?\}\}.*?\{\{.*?endif.*?\}\}', '', tpl_content, flags=re.DOTALL)

        # Check if substantially different
        similarity = difflib.SequenceMatcher(None, normalized_src, tpl_normalized).ratio()
        in_sync = similarity > 0.95  # 95% similar

        results.append((src_path, template_path, in_sync))

    return results


def show_diff(src_path: str, template_path: str):
    """Show differences between source and template."""
    src_content = Path(src_path).read_text().splitlines()
    tpl_content = Path(template_path).read_text().splitlines()

    diff = difflib.unified_diff(
        tpl_content,
        src_content,
        fromfile=f"{template_path} (template)",
        tofile=f"{src_path} (source)",
        lineterm=""
    )

    print("\n".join(diff))


def update_template(src_path: str, template_path: str):
    """Update template from source file."""
    src_content = Path(src_path).read_text()

    # Apply template conversions
    for pattern, replacement in TEMPLATE_CONVERSIONS:
        src_content = re.sub(pattern, replacement, src_content)

    # Preserve conditional blocks from existing template if it exists
    tpl_file = Path(template_path)
    if tpl_file.exists():
        existing = tpl_file.read_text()
        # TODO: Implement smarter merging of conditionals when needed

    # Write updated template
    tpl_file.parent.mkdir(parents=True, exist_ok=True)
    tpl_file.write_text(src_content)
    print(f"✅ Updated {template_path}")


def main():
    """Main sync workflow."""
    print("🔍 Checking template sync status...\n")

    results = check_sync_status()
    out_of_sync = [(s, t) for s, t, sync in results if not sync]

    if not out_of_sync:
        print("✅ All templates are in sync!")
        return

    print(f"⚠️  {len(out_of_sync)} files out of sync:\n")
    for src, tpl in out_of_sync:
        print(f"  - {src} → {tpl}")

    print("\nOptions:")
    print("1. Show differences")
    print("2. Update all templates")
    print("3. Update specific template")
    print("4. Exit")

    choice = input("\nChoice: ")

    if choice == "1":
        for src, tpl in out_of_sync:
            print(f"\n{'='*60}")
            print(f"Differences: {src}")
            print('='*60)
            show_diff(src, tpl)

    elif choice == "2":
        confirm = input("\n⚠️  Update all templates? (y/N): ")
        if confirm.lower() == 'y':
            for src, tpl in out_of_sync:
                update_template(src, tpl)

    elif choice == "3":
        for i, (src, tpl) in enumerate(out_of_sync):
            print(f"{i+1}. {src}")
        idx = int(input("\nSelect file: ")) - 1
        if 0 <= idx < len(out_of_sync):
            src, tpl = out_of_sync[idx]
            update_template(src, tpl)


if __name__ == "__main__":
    main()