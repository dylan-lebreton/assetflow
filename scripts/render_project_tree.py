from treeproject import build_tree_and_contents

res = build_tree_and_contents(
    root=r"..",
    tree_follow_symlinks=False,
    tree_exclude=[
        "__pycache__",
        "LICENSE",
        "*.lock",
        ".git",
        ".idea",
        ".venv",
        ".cache",
        ".gitignore",
        ".pytest_cache",
    ],
    content_exclude=[
        "__pycache__",
        "LICENSE",
        "*.lock",
        ".gitignore",
        ".git",
        ".idea",
        ".venv",
        ".cache",
        ".gitignore",
        ".pytest_cache",
    ],
    content_include=[".py", ".toml"],
    content_ignore_file_type_error=False,
    encoding="utf-8"
)

print(res)
