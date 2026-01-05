# Deploy to GitHub
$RepoUrl = "https://github.com/wjabrac/XMNX.git"

Write-Host "Preparing to push to $RepoUrl..."

# 1. Ensure clean state
git add -A
git commit -m "fix: Resolve SyntaxError in Coordinator"

# 2. Setup Remote
$remotes = git remote
if ($remotes -contains "origin") {
    git remote set-url origin $RepoUrl
} else {
    git remote add origin $RepoUrl
}

# 3. Rename branch to main
git branch -M main

# 4. Push
Write-Host "Pushing to GitHub..."
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully pushed to GitHub!"
} else {
    Write-Host "Push failed. Please ensure the repository 'XMNX' exists in account 'wjabrac'."
}
