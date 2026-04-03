# GitHub Profile Repository Setup Guide

This repository creates a dynamic GitHub profile with automatically updated statistics, inspired by [Andrew6rant's implementation](https://github.com/Andrew6rant/Andrew6rant).

## Features

- **Dynamic GitHub Statistics**: Automatically fetches and displays:
  - Repository count (owned and contributed)
  - Total stars across repositories
  - Commit count
  - Follower count
  - Lines of code (additions and deletions)
  - Account age/uptime

- **Theme Support**: Separate light and dark mode SVGs that adapt to GitHub's theme
- **ASCII Art Section**: Placeholder for your personal ASCII art photo
- **Automated Updates**: GitHub Actions workflow updates stats every 6 hours
- **Smart Caching**: Prevents API rate limiting with intelligent caching mechanism

## Setup Instructions

### 1. Personal Access Token

The script uses GitHub's GraphQL API and requires a Personal Access Token (PAT) with appropriate permissions.

#### Creating a Fine-Grained PAT (Recommended):

1. Go to GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click "Generate new token"
3. Configure the token:
   - **Token name**: `GitHub Profile Stats`
   - **Expiration**: Choose your preferred duration (or no expiration)
   - **Repository access**: Choose "All repositories" or select specific ones
   
4. Under **Repository permissions**, grant:
   - `Contents`: Read access (to read repository data)
   - `Metadata`: Read access (automatically granted)
   
5. Under **Account permissions**, grant:
   - `Followers`: Read access
   - `Starring`: Read access

6. Generate and copy the token

#### For Classic PAT:

If using a classic token, you need these scopes:
- `repo` (Full control of private repositories)
- `read:user` (Read user profile data)

### 2. Configure GitHub Actions

The repository is already set up with a GitHub Actions workflow. No additional secrets are needed as it uses the default `GITHUB_TOKEN` provided by GitHub Actions.

**Note**: The default `GITHUB_TOKEN` has read access to your repositories. If you need access to private repositories or want more control, create a PAT and add it as a secret:

1. Go to your repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `PERSONAL_ACCESS_TOKEN`
4. Value: Paste your Personal Access Token
5. Update `.github/workflows/update-stats.yml` to use `${{ secrets.PERSONAL_ACCESS_TOKEN }}` instead of `${{ secrets.GITHUB_TOKEN }}`

### 3. Customize Your Profile

#### Update Personal Information

Edit both `dark_mode.svg` and `light_mode.svg` to update:

- **Username** (line ~30): Change `your@username` to your GitHub username
- **OS** (line ~50): Your operating systems
- **Location** (line ~90): Your location
- **Role** (line ~110): Your job title/role
- **IDE** (line ~130): Your favorite IDEs
- **Languages** (lines ~170-210): Programming languages you use
- **Interests** (lines ~250-270): Your technical interests
- **Contact Info** (lines ~330-410): Email, website, social media handles

#### Add Your ASCII Art Photo

The SVG files have a clearly marked placeholder section for your ASCII art photo (lines ~30-510).

**To add your photo:**

1. Convert your photo to ASCII art using online tools:
   - https://www.ascii-art-generator.org/
   - https://asciiart.club/
   - https://www.text-image.com/convert/ascii.html

2. Use these settings for best results:
   - Width: ~35-40 characters
   - Font: Use a monospace font
   - Contrast: Medium to high

3. Replace the placeholder `<tspan>` lines in both SVG files with your ASCII art
   - Keep the format: `<tspan x="15" y="XX">YOUR ASCII ART LINE</tspan>`
   - Maintain Y spacing of 20px between lines (y="30", y="50", y="70", etc.)

### 4. Run the Script

#### Locally (Optional):

```bash
# Install dependencies
pip install requests python-dateutil lxml

# Set environment variables
export GITHUB_USERNAME="your-username"
export GITHUB_TOKEN="your-personal-access-token"

# Run the script
python today.py
```

#### Via GitHub Actions:

The workflow runs automatically:
- Every 6 hours (via cron schedule)
- When you push to the main branch
- Manually via the "Actions" tab → "Update GitHub Profile Stats" → "Run workflow"

### 5. Verify the Setup

1. Push your changes to GitHub
2. Go to the "Actions" tab in your repository
3. Manually trigger the "Update GitHub Profile Stats" workflow
4. Wait for it to complete
5. Check your profile to see the updated README with your stats!

## File Structure

```
anirudw/
├── .github/
│   └── workflows/
│       └── update-stats.yml    # GitHub Actions workflow
├── cache/
│   ├── .gitkeep                # Keeps cache directory in git
│   └── *.txt                   # Cache files (git-ignored)
├── dark_mode.svg               # Dark theme profile image
├── light_mode.svg              # Light theme profile image
├── today.py                    # Statistics fetcher script
├── README.md                   # Your profile page
└── SETUP.md                    # This file
```

## Customization Tips

1. **Change Update Frequency**: Edit the cron schedule in `.github/workflows/update-stats.yml`
   - `'0 */6 * * *'` = every 6 hours
   - `'0 */12 * * *'` = every 12 hours
   - `'0 0 * * *'` = daily at midnight

2. **Adjust Colors**: Modify the CSS classes in the SVG files:
   - `.key`: Field names (e.g., "Repos", "Commits")
   - `.value`: Field values
   - `.addColor`: LOC additions (green)
   - `.delColor`: LOC deletions (red)
   - `.cc`: Comment color (gray)

3. **Change Dimensions**: The SVGs are 985x530px. If you want different sizes:
   - Update `width` and `height` attributes in the `<svg>` tag
   - Adjust text positions (`x` and `y` coordinates)

## Troubleshooting

### Stats Not Updating

- Check the Actions tab for error messages
- Verify your Personal Access Token hasn't expired
- Ensure the token has the correct permissions

### API Rate Limiting

- The caching mechanism should prevent this
- If it occurs, increase the time between updates
- Check if you have other apps using your API quota

### SVG Not Displaying

- Ensure the image URLs in README.md match your username
- Check that the SVG files are committed to the main branch
- Wait a few minutes for GitHub's CDN to update

## Credits

This implementation is inspired by [Andrew6rant's GitHub profile](https://github.com/Andrew6rant/Andrew6rant). Thanks for the awesome design!

## License

Feel free to fork and customize this for your own profile!
