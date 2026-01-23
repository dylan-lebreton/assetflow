from treeproject import build_tree_and_contents

res = build_tree_and_contents(
    root=r"..",
    tree_follow_symlinks=False,
    tree_exclude=[
        "__pycache__",
        "*.lock",
        ".git",
        ".idea",
        ".venv",
        ".cache",
        ".gitignore",
        ".pytest_cache",
        "*tests",
        "render_project_tree.py",
    ],
    content_exclude=[
        "__pycache__",
        "*.lock",
        ".gitignore",
        ".git",
        ".idea",
        ".venv",
        ".cache",
        ".gitignore",
        ".pytest_cache",
        "*tests",
        "render_project_tree.py",
    ],
    content_include=[
        ".py",
        ".toml",
        ".html",
        ".css",
        ".js",
        ".md"
    ],
    content_ignore_file_type_error=False,
    encoding="utf-8"
)

print(res)
