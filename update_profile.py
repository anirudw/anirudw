import os
import re
import requests
from lxml import etree

GITHUB_TOKEN = os.environ.get("CLI_PROFILE_UPDATER")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "anirudw")
GEMINI_MODEL = "gemini-2.0-flash"

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


def get_gemini_insight():
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        prompt = """You are a technical insight generator for a developer's GitHub profile README.
The developer is a full-stack developer who builds robust web applications using Java, engineers backend systems with Python, and actively explores machine learning and artificial intelligence.

Generate a single, concise, inspiring technical insight or tip (max 100 characters) that relates to one of these domains: Java, Python, full-stack development, or AI/ML. Make it practical and valuable. No quotes, no markdown. Just the text.

Example: "Python's @cache decorator can cut API call latency by 80% in production services"
Example: "Combine Spring Boot with React for building scalable enterprise-grade applications"

Generate one fresh insight now:"""
        
        response = model.generate_content(prompt)
        insight = response.text.strip()
        if len(insight) > 100:
            insight = insight[:97] + "..."
        return insight
    except Exception as e:
        return "Error generating insight"


def update_svg(stats, insight):
    svg_path = "templates/cli_dark.svg"
    tree = etree.parse(svg_path)
    root = tree.getroot()
    
    ns = {"svg": "http://www.w3.org/2000/svg"}
    
    for elem in root.iter():
        if elem.get("id") == "commits":
            elem.text = str(stats["commits"])
        elif elem.get("id") == "repos":
            elem.text = str(stats["repos"])
        elif elem.get("id") == "stars":
            elem.text = str(stats["stars"])
        elif elem.get("id") == "insight":
            elem.text = insight
    
    with open(svg_path, "wb") as f:
        f.write(etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding="UTF-8"))


def main():
    stats = get_github_stats()
    print(f"Stats: {stats}")
    
    insight = get_gemini_insight()
    print(f"Insight: {insight}")
    
    update_svg(stats, insight)
    print("SVG updated successfully!")


if __name__ == "__main__":
    main()
