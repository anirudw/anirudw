import os
import hashlib
import re
import xml.etree.ElementTree as ET

import requests

GITHUB_TOKEN = (
  os.environ.get("GITHUB_TOKEN")
  or os.environ.get("PROFILE_UPDATE")
  or os.environ.get("PROFILE_README_TOKEN")
)
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "anirudw")

GRAPHQL_URL = "https://api.github.com/graphql"

# CHANGED: Added 'languages' to the repository nodes in the GraphQL query
QUERY = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      totalCommitContributions
    }
    repositories(first: 100, orderBy: {field: STARGAZERS, direction: DESC}) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
            }
          }
        }
      }
    }
  }
}
"""


def get_github_stats():
  if not GITHUB_TOKEN:
    raise RuntimeError("Missing GitHub token. Set GITHUB_TOKEN, PROFILE_UPDATE, or PROFILE_README_TOKEN.")

  headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
  data = {"query": QUERY, "variables": {"username": GITHUB_USERNAME}}
  response = requests.post(GRAPHQL_URL, json=data, headers=headers, timeout=30)
  response.raise_for_status()
  json_data = response.json()

  user_data = json_data["data"]["user"]
  commits = user_data["contributionsCollection"]["totalCommitContributions"]
  repos = user_data["repositories"]["totalCount"]
  stars = sum(r["stargazerCount"] for r in user_data["repositories"]["nodes"])

  # CHANGED: Process the language edges to aggregate sizes and calculate top 5 percentages
  lang_counts = {}
  for repo in user_data["repositories"]["nodes"]:
      if repo.get("languages") and repo["languages"].get("edges"):
          for edge in repo["languages"]["edges"]:
               name = edge["node"]["name"]
               lang_counts[name] = lang_counts.get(name, 0) + edge["size"]
               
  total_size = sum(lang_counts.values())
  top_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)[:5]
  
  languages = []
  if total_size > 0:
      languages = [{"name": n, "percent": (s / total_size) * 100} for n, s in top_langs]

  # CHANGED: Return both stats and languages
  return {"commits": commits, "repos": repos, "stars": stars}, languages


# CHANGED: Rewritten to use standard library xml.etree.ElementTree instead of lxml
def update_svg(svg_path, stats, languages):
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    # Build a lookup map of elements by ID for fast access without XPath
    elem_map = {elem.get("id"): elem for elem in root.iter() if elem.get("id")}
    
    commits_elem = elem_map.get("commits")
    if commits_elem is not None:
        commits_elem.text = str(stats["commits"])
        
    repos_elem = elem_map.get("repos")
    if repos_elem is not None:
        repos_elem.text = str(stats["repos"])
        
    stars_elem = elem_map.get("stars")
    if stars_elem is not None:
        stars_elem.text = str(stats["stars"])
        
    # Map the 5 languages to the corresponding SVG IDs
    for i, lang in enumerate(languages):
        name_elem = elem_map.get(f"lang_name_{i}")
        pct_elem = elem_map.get(f"lang_pct_{i}")
        bar_elem = elem_map.get(f"lang_bar_{i}")
        
        if name_elem is not None:
            name_elem.text = lang['name']
        if pct_elem is not None:
            pct_elem.text = f"{lang['percent']:.1f}%"
        if bar_elem is not None:
            # Multiplies by 2 because your max width for the bar in the SVG is 200px
            bar_elem.set("width", str(int(lang["percent"] * 2)))
    
    tree.write(svg_path, encoding="utf-8", xml_declaration=True)


def calculate_file_hash(filepath):
    if not os.path.exists(filepath):
        return ""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()[:8]


def update_readme_version(svg_hash):
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        return
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace v=... with new svg_hash for both light and dark SVGs
    new_content = re.sub(r'(cli_(?:dark|light)\.svg\?raw=1&amp;v=)[^"\s>]+', r'\g<1>' + svg_hash, content)
    new_content = re.sub(r'(cli_(?:dark|light)\.svg\?raw=1&v=)[^"\s>]+', r'\g<1>' + svg_hash, new_content)
    
    if new_content != content:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"README.md cache-buster updated to v={svg_hash}")


def main():
    # CHANGED: Unpack the new languages return variable
    stats, languages = get_github_stats()
    print(f"Stats: {stats}")
    print(f"Languages: {languages}")

    # CHANGED: Update both dark and light SVGs
    update_svg("templates/cli_dark.svg", stats, languages)
    update_svg("templates/cli_light.svg", stats, languages)
    print("SVGs updated successfully!")

    # CHANGED: Calculate hash of updated dark SVG to use as a cache buster
    svg_hash = calculate_file_hash("templates/cli_dark.svg")
    if svg_hash:
        update_readme_version(svg_hash)


if __name__ == "__main__":
    main()