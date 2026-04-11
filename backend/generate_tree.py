from pathlib import Path

def generate_tree(dir_path, prefix='', ignore_dirs=('.git', 'venv', '__pycache__', '.pytest_cache', '.coverage')):
    contents = list(dir_path.iterdir())
    dirs = sorted([d for d in contents if d.is_dir() and d.name not in ignore_dirs])
    files = sorted([f for f in contents if f.is_file()])
    entries = dirs + files
    tree_str = ''

    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        connector = '└── ' if is_last else '├── '
        tree_str += f'{prefix}{connector}{entry.name}\n'

        if entry.is_dir():
            extension = '    ' if is_last else '│   '
            tree_str += generate_tree(entry, prefix + extension, ignore_dirs)

    return tree_str


root = Path('.')
result = f'backend/\n' + generate_tree(root)

with open('FILE_TREE.md', 'w', encoding='utf-8') as f:
    f.write('# Project File Tree\n\n```text\n' + result + '```\n')

print("FILE_TREE.md created")