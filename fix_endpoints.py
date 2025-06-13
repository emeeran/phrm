#!/usr/bin/env python3
"""
Script to fix all endpoint references in templates to use the correct nested blueprint structure.
"""

import re
from pathlib import Path

# Mapping of old endpoint patterns to new ones
ENDPOINT_MAPPINGS = {
    # Health Records routes
    r"url_for\('records\.list_records'": "url_for('records.health_records_routes.list_records'",
    r"url_for\('records\.create_record'": "url_for('records.health_records_routes.create_record'",
    r"url_for\('records\.view_record'": "url_for('records.health_records_routes.view_record'",
    r"url_for\('records\.edit_record'": "url_for('records.health_records_routes.edit_record'",
    r"url_for\('records\.delete_record'": "url_for('records.health_records_routes.delete_record'",
    # Family Member routes
    r"url_for\('records\.list_family'": "url_for('records.family_member_routes.list_family'",
    r"url_for\('records\.add_family_member'": "url_for('records.family_member_routes.add_family_member'",
    r"url_for\('records\.edit_family_member'": "url_for('records.family_member_routes.edit_family_member'",
    r"url_for\('records\.view_family_member'": "url_for('records.family_member_routes.view_family_member'",
    r"url_for\('records\.delete_family_member'": "url_for('records.family_member_routes.delete_family_member'",
    # File routes
    r"url_for\('records\.serve_upload'": "url_for('records.file_routes.serve_upload'",
}


def fix_file(file_path):
    """Fix endpoint references in a single file."""
    print(f"Processing {file_path}")

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Apply all replacements
    for old_pattern, new_pattern in ENDPOINT_MAPPINGS.items():
        content = re.sub(old_pattern, new_pattern, content)

    # Write back if changed
    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ Updated {file_path}")
        return True
    else:
        print(f"  - No changes needed in {file_path}")
        return False


def main():
    """Main function to fix all endpoint references."""
    print("Fixing endpoint references in templates...")

    # Find all HTML template files
    template_dir = Path("app/templates")
    html_files = list(template_dir.rglob("*.html"))

    total_fixed = 0

    for html_file in html_files:
        if fix_file(html_file):
            total_fixed += 1

    print(f"\nCompleted! Fixed {total_fixed} files.")


if __name__ == "__main__":
    main()
