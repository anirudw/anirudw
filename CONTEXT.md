# Project Context: Dynamic CLI-Style GitHub Profile README

## 🎯 Goal
Create an automated, self-updating GitHub profile README that visually mimics a modern terminal window (CLI). The profile will display live GitHub statistics and a daily AI-generated technical insight.

## 🏗️ Architecture
- **Frontend / Visuals**: An SVG file designed to look like a macOS/Linux terminal window. It uses monospace fonts, a dark theme (`#0d1117`), and mock terminal commands (e.g., `❯ gemini --action "get-stats"`).
- **Backend / Logic**: A Python 3 script that fetches data and updates the SVG.
- **Data Sources**:
  - GitHub GraphQL API: To fetch total commits, repository count, and total stars.
  - Google Gemini API: To generate a daily short, dynamic message.
- **Automation**: GitHub Actions (runs daily via cron and on push to `main`).

## 👤 Owner Context for AI Generation
The profile belongs to a full-stack developer who builds robust web applications using Java, engineers backend systems with Python, and actively explores machine learning and artificial intelligence. The Gemini prompt should be tailored to occasionally reference these domains when generating the daily technical insight.

## 📁 Required Project Structure
```text
.
├── README.md               # Contains the <picture> or <img> tag linking to the SVG
├── templates/
│   └── cli_dark.svg        # The base SVG template with placeholder IDs
├── update_profile.py       # The main automation script
├── requirements.txt        # Python dependencies (requests, google-generativeai, lxml)
└── .github/workflows/
    └── build.yml           # GitHub Actions configuration