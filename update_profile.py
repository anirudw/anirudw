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

  return {"commits": commits, "repos": repos, "stars": stars}


def update_svg(stats):
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
    
    with open(svg_path, "wb") as f:
        f.write(etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding="UTF-8"))


def main():
    stats = get_github_stats()
    print(f"Stats: {stats}")

    update_svg(stats)
    print("SVG updated successfully!")


if __name__ == "__main__":
    main()
