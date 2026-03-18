# GitHub Setup Instructions

**How to Create Repository and Connect to Remote**

---

## Step 1: Create GitHub Repository

1. Go to [GitHub New Repository](https://github.com/new)
2. Fill in the details:
   - **Repository name:** `agentic-day4-multi-agent`
   - **Description:** Multi-agent AI systems for complex task orchestration
   - **Public/Private:** Public (or Private if preferred)
   - **Initialize with:** Skip (we already have initial commit)

3. Click **Create repository**

---

## Step 2: Connect Local Repository to Remote

After creating the GitHub repository, run these commands:

```bash
# Navigate to project directory
cd /Volumes/Learning/Bootcamp_Agentic_AI/agentic-day4-multi-agent

# Add remote origin (replace USERNAME with your GitHub username)
git remote add origin https://github.com/USERNAME/agentic-day4-multi-agent.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

**Example:**
```bash
git remote add origin https://github.com/sunipa21/agentic-day4-multi-agent.git
git branch -M main
git push -u origin main
```

---

## Step 3: Create GitHub Project

### Option A: Table View (Recommended for Multi-Agent)

1. Go to your repository: `https://github.com/USERNAME/agentic-day4-multi-agent`
2. Click **Projects** tab (top navigation)
3. Click **New Project** button
4. Choose **Table** view
5. Name: `Multi-Agent Development`
6. Description: "Track development of multi-agent system components"
7. Click **Create project**

### Option B: Board View

1. Same steps as above
2. At step 4, choose **Board** instead of Table
3. Create columns for:
   - 📋 Backlog
   - 🔨 In Progress
   - 🧪 Testing
   - ✅ Done

---

## Step 4: Add Issues to Project

### Create Issues:

1. Go to **Issues** tab
2. Click **New issue** for each component:

```markdown
Title: Implement Agent Base Class
Description: Create foundational Agent class with LLM integration, tool access, state management
Labels: enhancement, phase-1
Assignee: yourself

---

Title: Build Orchestrator Framework
Description: Multi-agent coordination, task routing, communication
Labels: enhancement, phase-2

---

Title: Create Memory System
Description: Shared state, conversation history, knowledge base
Labels: enhancement, phase-3

---

Title: Implement Tool Registry
Description: Tool definitions, execution, error handling
Labels: enhancement, phase-4

---

Title: Add Monitoring & Observability
Description: Logging, metrics, health checks
Labels: enhancement, phase-5

---

Title: Write Comprehensive Tests
Description: 30+ tests covering all components
Labels: testing

---

Title: Write Documentation
Description: Architecture guide, API docs, examples
Labels: documentation
```

### Add Issues to Project:

1. Click each issue
2. Click **Projects** (right sidebar)
3. Select your project
4. Add to appropriate column

---

## Step 5: Verify Setup

Run these commands to verify:

```bash
# Check remote
git remote -v
# Should show:
# origin  https://github.com/USERNAME/agentic-day4-multi-agent.git (fetch)
# origin  https://github.com/USERNAME/agentic-day4-multi-agent.git (push)

# Check branch
git branch -a
# Should show:
# * main
#   remotes/origin/main

# Check log
git log --oneline
# Should show:
# 6fedadc Initial commit: Multi-agent system skeleton and project structure
```

---

## Step 6: Workflow Going Forward

For each phase of development:

### Before Starting Work
```bash
git pull origin main
```

### During Development
```bash
# Make changes
git add .
git commit -m "Feature: [component] - [description]"
git push origin main
```

### Update Project Tracking
1. Move issue from "In Progress" to "Testing"
2. Add comments with progress
3. Link PR if applicable

---

## Commands Cheat Sheet

```bash
# Initial setup (one time)
git remote add origin https://github.com/USERNAME/agentic-day4-multi-agent.git
git branch -M main
git push -u origin main

# Regular workflow
git pull origin main                    # Get latest
git add .                               # Stage changes
git commit -m "Description"             # Commit
git push origin main                    # Push to GitHub

# View status
git status                              # Current changes
git log --oneline -5                    # Last 5 commits
git remote -v                           # Remote URLs
```

---

## GitHub Project Features to Use

### ✨ Features
- **Automation:** Set rules to auto-move issues
- **Templates:** Create issue templates for consistency
- **Milestones:** Group issues by phase (Phase 1-6)
- **Labels:** Organize by type (enhancement, bug, documentation, testing)
- **Assignees:** Assign issues to yourself
- **Due dates:** Set deadlines for phases

### 📊 View Your Project
- **Table view:** See all issues at once
- **Board view:** Kanban-style workflow
- **Roadmap view:** Timeline of phases

---

## Resources

- [GitHub Project Docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [GitHub Issues](https://docs.github.com/en/issues)
- [Git Basics](https://git-scm.com/book/en/v2/Getting-Started-Git-Basics)

---

**Your Repository:** `https://github.com/USERNAME/agentic-day4-multi-agent`

Replace `USERNAME` with your actual GitHub username in all URLs.
