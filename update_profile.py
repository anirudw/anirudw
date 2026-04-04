import os

import requests
from lxml import etree

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


# CHANGED: Added 'languages' parameter
def update_svg(stats, languages):
    svg_path = "templates/cli_dark.svg"
    tree = etree.parse(svg_path)
    root = tree.getroot()
    
    for elem in root.iter():
        if elem.get("id") == "commits":
            elem.text = str(stats["commits"])
        elif elem.get("id") == "repos":
            elem.text = str(stats["repos"])
        elif elem.get("id") == "stars":
            elem.text = str(stats["stars"])
            
    # CHANGED: Added logic to map the 5 languages to the corresponding SVG IDs
    for i, lang in enumerate(languages):
        name_elem = root.find(f".//*[@id='lang_name_{i}']")
        pct_elem = root.find(f".//*[@id='lang_pct_{i}']")
        bar_elem = root.find(f".//*[@id='lang_bar_{i}']")
        
        if name_elem is not None:
            name_elem.text = lang['name']
        if pct_elem is not None:
            pct_elem.text = f"{lang['percent']:.1f}%"
        if bar_elem is not None:
            # Multiplies by 2 because your max width for the bar in the SVG is 200px
            bar_elem.set("width", str(int(lang["percent"] * 2)))
    
    with open(svg_path, "wb") as f:
        f.write(etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding="UTF-8"))


def main():
    # CHANGED: Unpack the new languages return variable
    stats, languages = get_github_stats()
    print(f"Stats: {stats}")
    print(f"Languages: {languages}")

    # CHANGED: Pass languages into the update_svg function
    update_svg(stats, languages)
    print("SVG updated successfully!")


if __name__ == "__main__":
    main()