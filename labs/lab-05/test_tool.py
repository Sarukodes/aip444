from tools import read_github_files

print("Testing read_github_files...\n")

content = read_github_files([
    {
        "owner": "microsoft",
        "repo": "vscode",
        "path": "package.json",
        "ref": "main"
    }
])

print(content)