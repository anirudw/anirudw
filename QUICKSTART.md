# Quick Start Guide

Welcome to your revamped GitHub profile! Here's what you need to do next:

## ✅ What's Been Done

1. ✓ **Python Script (`today.py`)**: Completely rewritten to fetch GitHub stats via GraphQL API
2. ✓ **Dark Mode SVG (`dark_mode.svg`)**: Created with ASCII art placeholder and stats sections
3. ✓ **Light Mode SVG (`light_mode.svg`)**: Created with light theme colors
4. ✓ **README.md**: Updated to display theme-aware profile images
5. ✓ **GitHub Actions**: Workflow configured to auto-update every 6 hours
6. ✓ **Cache System**: Set up to prevent API rate limiting
7. ✓ **Documentation**: Complete setup guide in `SETUP.md`

## 🎨 Immediate Next Steps

### 1. Customize Your Personal Information

Open both `dark_mode.svg` and `light_mode.svg` and replace:

- **Line ~30**: `your@username` → Your actual username
- **Line ~50**: `Windows, Linux, macOS` → Your OS(es)
- **Line ~70**: `0 years, 0 months, 0 days` → Will auto-update
- **Line ~90**: `Your Location` → Your city/country
- **Line ~110**: `Software Developer` → Your role
- **Line ~130**: `VS Code, PyCharm, IntelliJ` → Your IDEs
- **Line ~170**: `Python, JavaScript, Java` → Your languages
- **Line ~330**: `your.email@example.com` → Your email
- **Line ~350**: `https://yourwebsite.com` → Your website
- **Line ~370-410**: Your social media handles

### 2. Add Your ASCII Art Photo

**Important**: This is where you'll add your personal touch!

The ASCII art section is in lines ~30-510 of both SVG files. It's clearly marked with:
```
<!-- ASCII ART SECTION -->
<!-- PLACEHOLDER: Add your personal ASCII art photo here -->
```

**Steps:**
1. Go to https://www.ascii-art-generator.org/
2. Upload your photo
3. Settings: ~35 characters wide, high contrast
4. Copy the ASCII art
5. Replace the placeholder lines in both SVG files
6. Keep the format: `<tspan x="15" y="30">YOUR LINE HERE</tspan>`

### 3. Configure GitHub Token

The workflow uses the default `GITHUB_TOKEN` which works for public repositories.

**If you need access to private repos:**
1. Create a Personal Access Token (instructions in `SETUP.md`)
2. Add it as a repository secret named `PERSONAL_ACCESS_TOKEN`
3. The workflow is already configured to use it!

### 4. Test It Out

```bash
# Install dependencies (if testing locally)
pip install requests python-dateutil lxml

# Set your username in the environment
# Windows:
set GITHUB_USERNAME=anirudw
set GITHUB_TOKEN=your_token_here

# Run the script
python today.py
```

### 5. Push to GitHub

```bash
git add .
git commit -m "Revamp GitHub profile with dynamic stats"
git push origin main
```

### 6. Trigger the Workflow

1. Go to your repository on GitHub
2. Click the "Actions" tab
3. Select "Update GitHub Profile Stats"
4. Click "Run workflow"
5. Wait for it to complete
6. Check your profile! 🎉

## 📝 Important Notes

- **ASCII Art**: The placeholder is intentionally visible so you remember to add your own!
- **Statistics**: Will be zero until the workflow runs for the first time
- **Updates**: Happens automatically every 6 hours after setup
- **Customization**: See `SETUP.md` for detailed customization options

## 🐛 Troubleshooting

If stats don't update:
1. Check the Actions tab for errors
2. Verify your token permissions
3. Make sure `GITHUB_USERNAME` environment variable is set correctly
4. Look at `SETUP.md` troubleshooting section

## 🎯 Design Philosophy

This follows Andrew6rant's aesthetic:
- Terminal/console-style design
- Monospace font (Consolas)
- System-like information display
- Dynamic statistics that update automatically
- Theme-aware (dark/light mode support)

## 📚 Full Documentation

For complete details, see:
- `SETUP.md` - Comprehensive setup guide
- `today.py` - The Python script with inline comments
- `.github/workflows/update-stats.yml` - GitHub Actions configuration

---

**Ready to make it yours!** Start by customizing the SVG files and adding your ASCII art photo. 🚀
