# Git Essentials

## Setup
```bash
git init                              # Initialize new repo
git clone <url>                       # Clone existing repo
```

## Daily Commands
```bash
git status                            # Check file status
git add .                             # Stage all changes
git add <file>                        # Stage specific file
git commit -m "message"               # Commit with message
git push                              # Push to remote
git pull                              # Pull latest changes
```

## Branches
```bash
git checkout -b <branch-name>         # Create and switch to new branch
git checkout <branch-name>            # Switch to existing branch
git branch                            # List branches
git merge <branch-name>               # Merge branch into current
```

## Common Workflows

### New Project
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <url>
git push -u origin main
```

### Existing Project
```bash
git clone <url>
git checkout -b dev/your-name
# Make changes
git add .
git commit -m "Your changes"
git push -u origin dev/your-name
```

## UV Package Manager

### Virtual Environment
```bash
uv venv                               # Create virtual environment
uv venv .venv                         # Create .venv directory
source .venv/bin/activate             # Activate (Linux/Mac)
.venv\Scripts\activate                # Activate (Windows)
deactivate                            # Deactivate environment
```

### Package Management
```bash
uv sync                               # Install dependencies from pyproject.toml
uv add <package>                      # Add package to project
uv remove <package>                   # Remove package
```

## Useful Commands
```bash
git log --oneline                     # View commit history
git diff                              # See changes
git reset HEAD~1                      # Undo last commit
```
