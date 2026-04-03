# 🎨 HOW TO MAKE THIS REPOSITORY YOURS

## ✅ Script Validation: PASSED
All code is working and ready to use!

---

## 🚀 STEP-BY-STEP CUSTOMIZATION GUIDE

### Step 1: Customize Personal Information in SVG Files

You need to edit **BOTH** files: `dark_mode.svg` AND `light_mode.svg`

Open each file and replace these lines:

#### Line 30: Your Username
```xml
<tspan x="390" y="30">your@username</tspan>
```
**Change to:**
```xml
<tspan x="390" y="30">anirudw</tspan>
```

#### Line 50: Your Operating Systems
```xml
<tspan class="value">Windows, Linux, macOS</tspan>
```
**Change to your actual OS(es)**

#### Line 90: Your Location
```xml
<tspan class="value">Your Location</tspan>
```
**Change to your city/country**, e.g., `Bangalore, India`

#### Line 110: Your Role/Title
```xml
<tspan class="value">Software Developer</tspan>
```
**Change to your actual role**, e.g., `Full Stack Developer`, `Data Scientist`, etc.

#### Line 130: Your IDEs
```xml
<tspan class="value">VS Code, PyCharm, IntelliJ</tspan>
```
**Change to your preferred IDEs**

#### Line 170: Programming Languages
```xml
<tspan class="value">Python, JavaScript, Java</tspan>
```
**List your languages**, e.g., `Python, JavaScript, TypeScript, C++`

#### Line 190: Markup Languages
```xml
<tspan class="value">HTML, CSS, JSON, YAML</tspan>
```
**Update to your markup languages**

#### Line 210: Human Languages
```xml
<tspan class="value">English</tspan>
```
**Add your languages**, e.g., `English, Hindi, Telugu`

#### Line 250: Tech Interests
```xml
<tspan class="value">Open Source, AI, Web Dev</tspan>
```
**Update to your interests**

#### Line 270: Other Interests
```xml
<tspan class="value">Gaming, Music</tspan>
```
**Add your hobbies**

#### Line 330: Email
```xml
<tspan class="value">your.email@example.com</tspan>
```
**Change to your real email**

#### Line 350: Website (Optional)
```xml
<tspan class="value">https://yourwebsite.com</tspan>
```
**Add your website or portfolio URL** (or remove this line if you don't have one)

#### Line 370: LinkedIn
```xml
<tspan class="value">yourname</tspan>
```
**Add your LinkedIn username**

#### Line 390: Twitter/X (Optional)
```xml
<tspan class="value">@yourhandle</tspan>
```
**Add your Twitter handle** (or change to another social media)

#### Line 410: Discord (Optional)
```xml
<tspan class="value">yourname#0000</tspan>
```
**Add your Discord username** (or remove if not applicable)

---

### Step 2: Add Your ASCII Art Photo

This is the **MOST IMPORTANT** customization!

#### Where to find it:
- Lines 30-510 in both `dark_mode.svg` and `light_mode.svg`
- Look for this comment:
```html
<!-- ASCII ART SECTION -->
<!-- PLACEHOLDER: Add your personal ASCII art photo here -->
```

#### How to create ASCII art:

1. **Choose a photo** - Use a clear headshot with good contrast
2. **Go to converter** - Visit https://www.ascii-art-generator.org/
3. **Upload your photo**
4. **Settings:**
   - Width: 35-40 characters
   - Font: Use monospace
   - Contrast: Medium to High
5. **Generate and copy the ASCII art**

#### How to add it to SVG:

Replace all the `<tspan>` lines from y="30" to y="510" with your ASCII art.

**Format for each line:**
```xml
<tspan x="15" y="30">YOUR ASCII ART LINE HERE</tspan>
<tspan x="15" y="50">YOUR ASCII ART LINE HERE</tspan>
<tspan x="15" y="70">YOUR ASCII ART LINE HERE</tspan>
```

**Important:**
- Keep `x="15"` for all lines
- Keep y-spacing of 20px (30, 50, 70, 90, 110, etc.)
- You should have about 24 lines total
- Do this for BOTH dark_mode.svg and light_mode.svg

---

### Step 3: Configure GitHub Token

I noticed your workflow uses `PROFILE_README_TOKEN`. Here's how to set it up:

#### Create a Personal Access Token:

1. Go to GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click **"Generate new token"**
3. Configure:
   - **Name**: `Profile README Token`
   - **Expiration**: 1 year (or no expiration)
   - **Repository access**: All repositories
4. **Permissions** (Repository):
   - Contents: Read and Write
   - Metadata: Read (auto-granted)
5. **Permissions** (Account):
   - Followers: Read
   - Starring: Read
6. Click **"Generate token"** and **COPY IT**

#### Add Token to Repository:

1. Go to your repository: https://github.com/anirudw/anirudw
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. **Name**: `PROFILE_README_TOKEN`
5. **Value**: Paste your token
6. Click **"Add secret"**

---

### Step 4: Push Your Changes

```bash
# Stage all changes
git add .

# Commit
git commit -m "Customize GitHub profile with personal info"

# Push to GitHub
git push origin main
```

---

### Step 5: Test the Workflow

1. Go to your repository: https://github.com/anirudw/anirudw
2. Click the **"Actions"** tab
3. Find **"Update GitHub Profile Stats"** workflow
4. Click **"Run workflow"** button (top right)
5. Click the green **"Run workflow"** button in the dropdown
6. Wait 1-2 minutes for it to complete
7. Check your profile: https://github.com/anirudw

---

## 📋 QUICK CHECKLIST

- [ ] Edit `dark_mode.svg` - Update all personal information
- [ ] Edit `light_mode.svg` - Update all personal information
- [ ] Add ASCII art to `dark_mode.svg` (lines 30-510)
- [ ] Add ASCII art to `light_mode.svg` (lines 30-510)
- [ ] Create GitHub Personal Access Token
- [ ] Add token as `PROFILE_README_TOKEN` secret in repository
- [ ] Push changes to GitHub
- [ ] Run workflow manually in Actions tab
- [ ] Check your profile!

---

## 🎯 WHAT WILL AUTO-UPDATE

Once set up, these stats will update automatically every 6 hours:

- ✓ Repository count
- ✓ Stars received
- ✓ Total commits
- ✓ Follower count
- ✓ Lines of code (additions & deletions)
- ✓ Account age/uptime

---

## 💡 PRO TIPS

1. **Test Locally First** (optional):
   ```bash
   set GITHUB_USERNAME=anirudw
   set PROFILE_README_TOKEN=your_token_here
   python today.py
   ```

2. **See Changes Instantly**: After running the workflow, wait 30 seconds then refresh your profile

3. **Adjust Update Frequency**: Edit `.github/workflows/update-stats.yml` line 6:
   - `0 */6 * * *` = every 6 hours (current)
   - `0 */12 * * *` = every 12 hours
   - `0 0 * * *` = daily at midnight

4. **ASCII Art Tips**:
   - Use a photo with good lighting
   - Increase contrast for better results
   - Try different width settings (30-40 chars)
   - Preview before committing

---

## 🆘 NEED HELP?

- **Script validated**: ✅ No syntax errors, all dependencies installed
- **Workflow configured**: ✅ Ready to run once token is added
- **Documentation**: See `SETUP.md` for detailed info

**Next action**: Start with Step 1 above - edit those SVG files!
