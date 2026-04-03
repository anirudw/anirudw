#!/usr/bin/env python3
"""
GitHub Profile Statistics Generator
Fetches GitHub statistics and updates SVG profile images
Inspired by Andrew6rant's implementation (https://github.com/Andrew6rant/Andrew6rant)
"""

import datetime
from dateutil import relativedelta
import requests
import os
from lxml import etree
import time
import hashlib

# GitHub API Configuration
# Set these via environment variables or GitHub Actions secrets
HEADERS = {'authorization': 'token ' + os.environ.get('PROFILE_README_TOKEN', os.environ.get('GITHUB_TOKEN', 'YOUR_TOKEN_HERE'))}
USER_NAME = os.environ.get('GITHUB_USERNAME', 'anirudw')
QUERY_COUNT = {
    'user_getter': 0,
    'follower_getter': 0,
    'graph_repos_stars': 0,
    'recursive_loc': 0,
    'graph_commits': 0,
    'loc_query': 0
}


def daily_readme(birthday):
    """
    Calculate coding age (time since account creation or custom date)
    Returns: 'XX years, XX months, XX days'
    """
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    return '{} {}, {} {}, {} {}{}'.format(
        diff.years, 'year' + format_plural(diff.years),
        diff.months, 'month' + format_plural(diff.months),
        diff.days, 'day' + format_plural(diff.days),
        ' 🎂' if (diff.months == 0 and diff.days == 0) else ''
    )


def format_plural(unit):
    """Returns 's' for plural, empty string for singular"""
    return 's' if unit != 1 else ''


def simple_request(func_name, query, variables):
    """Execute GraphQL request with error handling"""
    request = requests.post(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': variables},
        headers=HEADERS
    )
    if request.status_code == 200:
        return request
    raise Exception(func_name, 'failed with status', request.status_code, request.text, QUERY_COUNT)


def graph_commits(start_date, end_date):
    """Get total commit count using GitHub GraphQL API"""
    query_count('graph_commits')
    query = '''
    query($start_date: DateTime!, $end_date: DateTime!, $login: String!) {
        user(login: $login) {
            contributionsCollection(from: $start_date, to: $end_date) {
                contributionCalendar {
                    totalContributions
                }
            }
        }
    }'''
    variables = {'start_date': start_date, 'end_date': end_date, 'login': USER_NAME}
    request = simple_request(graph_commits.__name__, query, variables)
    return int(request.json()['data']['user']['contributionsCollection']['contributionCalendar']['totalContributions'])


def graph_repos_stars(count_type, owner_affiliation, cursor=None):
    """Get repository count, stars, or other repository statistics"""
    query_count('graph_repos_stars')
    query = '''
    query ($owner_affiliation: [RepositoryAffiliation], $login: String!, $cursor: String) {
        user(login: $login) {
            repositories(first: 100, after: $cursor, ownerAffiliations: $owner_affiliation) {
                totalCount
                edges {
                    node {
                        ... on Repository {
                            nameWithOwner
                            stargazers {
                                totalCount
                            }
                        }
                    }
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }'''
    variables = {'owner_affiliation': owner_affiliation, 'login': USER_NAME, 'cursor': cursor}
    request = simple_request(graph_repos_stars.__name__, query, variables)
    
    if request.status_code == 200:
        if count_type == 'repos':
            return request.json()['data']['user']['repositories']['totalCount']
        elif count_type == 'stars':
            return stars_counter(request.json()['data']['user']['repositories']['edges'])


def recursive_loc(owner, repo_name, data, cache_comment, addition_total=0, deletion_total=0, my_commits=0, cursor=None):
    """Recursively fetch commit data for LOC calculation (100 commits at a time)"""
    query_count('recursive_loc')
    query = '''
    query ($repo_name: String!, $owner: String!, $cursor: String) {
        repository(name: $repo_name, owner: $owner) {
            defaultBranchRef {
                target {
                    ... on Commit {
                        history(first: 100, after: $cursor) {
                            totalCount
                            edges {
                                node {
                                    ... on Commit {
                                        committedDate
                                    }
                                    author {
                                        user {
                                            id
                                        }
                                    }
                                    deletions
                                    additions
                                }
                            }
                            pageInfo {
                                endCursor
                                hasNextPage
                            }
                        }
                    }
                }
            }
        }
    }'''
    variables = {'repo_name': repo_name, 'owner': owner, 'cursor': cursor}
    request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables': variables}, headers=HEADERS)
    
    if request.status_code == 200:
        if request.json()['data']['repository']['defaultBranchRef'] is not None:
            return loc_counter_one_repo(owner, repo_name, data, cache_comment,
                                       request.json()['data']['repository']['defaultBranchRef']['target']['history'],
                                       addition_total, deletion_total, my_commits)
        else:
            return 0, 0, 0
    
    force_close_file(data, cache_comment)
    if request.status_code == 403:
        raise Exception('API rate limit hit!')
    raise Exception('recursive_loc() failed:', request.status_code, request.text)


def loc_counter_one_repo(owner, repo_name, data, cache_comment, history, addition_total, deletion_total, my_commits):
    """Count lines of code from commit history for repos where I'm the author"""
    for node in history['edges']:
        if node['node']['author']['user'] == OWNER_ID:
            my_commits += 1
            addition_total += node['node']['additions']
            deletion_total += node['node']['deletions']
    
    if not history['edges'] or not history['pageInfo']['hasNextPage']:
        return addition_total, deletion_total, my_commits
    else:
        return recursive_loc(owner, repo_name, data, cache_comment, addition_total, deletion_total, my_commits, history['pageInfo']['endCursor'])


def loc_query(owner_affiliation, comment_size=0, force_cache=False, cursor=None, edges=[]):
    """Query all repositories and calculate total lines of code"""
    query_count('loc_query')
    query = '''
    query ($owner_affiliation: [RepositoryAffiliation], $login: String!, $cursor: String) {
        user(login: $login) {
            repositories(first: 60, after: $cursor, ownerAffiliations: $owner_affiliation) {
                edges {
                    node {
                        ... on Repository {
                            nameWithOwner
                            defaultBranchRef {
                                target {
                                    ... on Commit {
                                        history {
                                            totalCount
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }'''
    variables = {'owner_affiliation': owner_affiliation, 'login': USER_NAME, 'cursor': cursor}
    request = simple_request(loc_query.__name__, query, variables)
    
    if request.json()['data']['user']['repositories']['pageInfo']['hasNextPage']:
        edges += request.json()['data']['user']['repositories']['edges']
        return loc_query(owner_affiliation, comment_size, force_cache, 
                        request.json()['data']['user']['repositories']['pageInfo']['endCursor'], edges)
    else:
        return cache_builder(edges + request.json()['data']['user']['repositories']['edges'], 
                           comment_size, force_cache)


def cache_builder(edges, comment_size, force_cache, loc_add=0, loc_del=0):
    """Build and manage cache for LOC calculations to avoid API rate limits"""
    cached = True
    filename = 'cache/' + hashlib.sha256(USER_NAME.encode('utf-8')).hexdigest() + '.txt'
    
    try:
        with open(filename, 'r') as f:
            data = f.readlines()
    except FileNotFoundError:
        data = []
        if comment_size > 0:
            for _ in range(comment_size):
                data.append('This line is a comment block. Write whatever you want here.\n')
        with open(filename, 'w') as f:
            f.writelines(data)
    
    if len(data) - comment_size != len(edges) or force_cache:
        cached = False
        flush_cache(edges, filename, comment_size)
        with open(filename, 'r') as f:
            data = f.readlines()
    
    cache_comment = data[:comment_size]
    data = data[comment_size:]
    
    for index in range(len(edges)):
        repo_hash, commit_count, *__ = data[index].split()
        if repo_hash == hashlib.sha256(edges[index]['node']['nameWithOwner'].encode('utf-8')).hexdigest():
            try:
                if int(commit_count) != edges[index]['node']['defaultBranchRef']['target']['history']['totalCount']:
                    owner, repo_name = edges[index]['node']['nameWithOwner'].split('/')
                    loc = recursive_loc(owner, repo_name, data, cache_comment)
                    data[index] = f"{repo_hash} {edges[index]['node']['defaultBranchRef']['target']['history']['totalCount']} {loc[2]} {loc[0]} {loc[1]}\n"
            except (TypeError, AttributeError):
                data[index] = f"{repo_hash} 0 0 0 0\n"
    
    with open(filename, 'w') as f:
        f.writelines(cache_comment)
        f.writelines(data)
    
    for line in data:
        loc = line.split()
        loc_add += int(loc[3])
        loc_del += int(loc[4])
    
    return [loc_add, loc_del, loc_add - loc_del, cached]


def flush_cache(edges, filename, comment_size):
    """Wipe and rebuild cache when repository count changes"""
    with open(filename, 'r') as f:
        data = []
        if comment_size > 0:
            data = f.readlines()[:comment_size]
    
    with open(filename, 'w') as f:
        f.writelines(data)
        for node in edges:
            f.write(hashlib.sha256(node['node']['nameWithOwner'].encode('utf-8')).hexdigest() + ' 0 0 0 0\n')


def force_close_file(data, cache_comment):
    """Save cache file before crash to preserve partial data"""
    filename = 'cache/' + hashlib.sha256(USER_NAME.encode('utf-8')).hexdigest() + '.txt'
    with open(filename, 'w') as f:
        f.writelines(cache_comment)
        f.writelines(data)
    print(f'Error while writing cache. Partial data saved to: {filename}')


def stars_counter(data):
    """Count total stars across all repositories"""
    total_stars = 0
    for node in data:
        total_stars += node['node']['stargazers']['totalCount']
    return total_stars


def commit_counter(comment_size):
    """Count total commits from cache file"""
    total_commits = 0
    filename = 'cache/' + hashlib.sha256(USER_NAME.encode('utf-8')).hexdigest() + '.txt'
    with open(filename, 'r') as f:
        data = f.readlines()
    
    data = data[comment_size:]
    for line in data:
        total_commits += int(line.split()[2])
    
    return total_commits


def user_getter(username):
    """Get user ID and account creation date"""
    query_count('user_getter')
    query = '''
    query($login: String!) {
        user(login: $login) {
            id
            createdAt
        }
    }'''
    variables = {'login': username}
    request = simple_request(user_getter.__name__, query, variables)
    return {'id': request.json()['data']['user']['id']}, request.json()['data']['user']['createdAt']


def follower_getter(username):
    """Get follower count"""
    query_count('follower_getter')
    query = '''
    query($login: String!) {
        user(login: $login) {
            followers {
                totalCount
            }
        }
    }'''
    request = simple_request(follower_getter.__name__, query, {'login': username})
    return int(request.json()['data']['user']['followers']['totalCount'])


def query_count(funct_id):
    """Track GraphQL API call count"""
    global QUERY_COUNT
    QUERY_COUNT[funct_id] += 1


def perf_counter(funct, *args):
    """Measure function execution time"""
    start = time.perf_counter()
    funct_return = funct(*args)
    return funct_return, time.perf_counter() - start


def formatter(query_type, difference, funct_return=False, whitespace=0):
    """Print formatted execution time"""
    print('{:<23}'.format('   ' + query_type + ':'), sep='', end='')
    if difference > 1:
        print('{:>12}'.format('%.4f' % difference + ' s '))
    else:
        print('{:>12}'.format('%.4f' % (difference * 1000) + ' ms'))
    
    if whitespace:
        return f"{'{:,}'.format(funct_return): <{whitespace}}"
    return funct_return


def svg_overwrite(filename, age_data, commit_data, star_data, repo_data, contrib_data, follower_data, loc_data):
    """Update SVG files with current statistics"""
    tree = etree.parse(filename)
    root = tree.getroot()
    
    justify_format(root, 'commit_data', commit_data, 22)
    justify_format(root, 'star_data', star_data, 14)
    justify_format(root, 'repo_data', repo_data, 6)
    justify_format(root, 'contrib_data', contrib_data)
    justify_format(root, 'follower_data', follower_data, 10)
    justify_format(root, 'loc_data', loc_data[2], 9)
    justify_format(root, 'loc_add', loc_data[0])
    justify_format(root, 'loc_del', loc_data[1], 7)
    justify_format(root, 'age_data', age_data)
    
    tree.write(filename, encoding='utf-8', xml_declaration=True)


def justify_format(root, element_id, new_text, length=0):
    """Format and justify text in SVG elements with dots"""
    if isinstance(new_text, int):
        new_text = f"{'{:,}'.format(new_text)}"
    new_text = str(new_text)
    
    find_and_replace(root, element_id, new_text)
    
    just_len = max(0, length - len(new_text))
    if just_len <= 2:
        dot_map = {0: '', 1: ' ', 2: '. '}
        dot_string = dot_map[just_len]
    else:
        dot_string = ' ' + ('.' * just_len) + ' '
    
    find_and_replace(root, f"{element_id}_dots", dot_string)


def find_and_replace(root, element_id, new_text):
    """Find SVG element by ID and replace its text"""
    element = root.find(f".//*[@id='{element_id}']")
    if element is not None:
        element.text = new_text


if __name__ == '__main__':
    """
    Main execution: Fetch GitHub stats and update SVG profile images
    """
    print('Calculating GitHub statistics...')
    print('Execution times:')
    
    # Get user data and account creation date
    user_data, user_time = perf_counter(user_getter, USER_NAME)
    OWNER_ID, acc_date = user_data
    formatter('account data', user_time)
    
    # Calculate account age (you can customize this to your birthdate or keep it as account age)
    acc_datetime = datetime.datetime.strptime(acc_date, '%Y-%m-%dT%H:%M:%SZ')
    age_data, age_time = perf_counter(daily_readme, acc_datetime)
    formatter('age calculation', age_time)
    
    # Get lines of code statistics (with caching)
    total_loc, loc_time = perf_counter(loc_query, ['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER'], 0)
    formatter('LOC (cached)' if total_loc[-1] else 'LOC (no cache)', loc_time)
    
    # Get commit count
    commit_data, commit_time = perf_counter(commit_counter, 0)
    formatter('commits', commit_time)
    
    # Get stars, repos, and contributions
    star_data, star_time = perf_counter(graph_repos_stars, 'stars', ['OWNER'])
    formatter('stars', star_time)
    
    repo_data, repo_time = perf_counter(graph_repos_stars, 'repos', ['OWNER'])
    formatter('repositories', repo_time)
    
    contrib_data, contrib_time = perf_counter(graph_repos_stars, 'repos', ['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER'])
    formatter('contributions', contrib_time)
    
    # Get follower count
    follower_data, follower_time = perf_counter(follower_getter, USER_NAME)
    formatter('followers', follower_time)
    
    # Format LOC data
    for index in range(len(total_loc) - 1):
        total_loc[index] = '{:,}'.format(total_loc[index])
    
    # Update both SVG files
    svg_overwrite('dark_mode.svg', age_data, commit_data, star_data, repo_data, 
                 contrib_data, follower_data, total_loc[:-1])
    svg_overwrite('light_mode.svg', age_data, commit_data, star_data, repo_data, 
                 contrib_data, follower_data, total_loc[:-1])
    
    print('\n✓ SVG files updated successfully!')
    print(f'\nTotal GitHub GraphQL API calls: {sum(QUERY_COUNT.values())}')
    for funct_name, count in QUERY_COUNT.items():
        if count > 0:
            print(f'   {funct_name}: {count}')
    
    def calculate_coding_age(self):
        """
        Calculate coding age from birthdate in Andrew's format
        
        Returns:
            str: Formatted age string like "22 years, 5 months, 29 days"
        """
        if not self.birthdate:
            return None
        
        now = datetime.now()
        delta = relativedelta(now, self.birthdate)
        
        # Format with proper pluralization
        def pluralize(num, unit):
            return f"{num} {unit}{'s' if num != 1 else ''}"
        
        age_str = f"{pluralize(delta.years, 'year')}, {pluralize(delta.months, 'month')}, {pluralize(delta.days, 'day')}"
        
        # Add birthday cake if it's their birthday
        if delta.months == 0 and delta.days == 0:
            age_str += " 🎂"
        
        return age_str
    
    def get_repo_count_and_stars(self, owner_affiliation=['OWNER']):
        """
        Get repository count and total stars using pagination
        
        Args:
            owner_affiliation: List of repository affiliations
            
        Returns:
            tuple: (repo_count, total_stars)
        """
        query = """
        query($login: String!, $owner_affiliation: [RepositoryAffiliation], $cursor: String) {
            user(login: $login) {
                repositories(first: 100, after: $cursor, ownerAffiliations: $owner_affiliation) {
                    totalCount
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                    edges {
                        node {
                            stargazerCount
                        }
                    }
                }
            }
        }
        """
        
        total_stars = 0
        repo_count = 0
        cursor = None
        
        while True:
            variables = {
                "login": self.username,
                "owner_affiliation": owner_affiliation,
                "cursor": cursor
            }
            
            response = requests.post(
                self.api_url,
                json={"query": query, "variables": variables},
                headers=self.headers
            )
            
            if response.status_code != 200:
                break
            
            data = response.json()["data"]["user"]["repositories"]
            
            if repo_count == 0:
                repo_count = data["totalCount"]
            
            for edge in data["edges"]:
                total_stars += edge["node"]["stargazerCount"]
            
            if not data["pageInfo"]["hasNextPage"]:
                break
            
            cursor = data["pageInfo"]["endCursor"]
        
        return repo_count, total_stars
    
    def fetch_repo_commits(self, owner, repo_name, cursor=None):
        """
        Fetch commit history for a repository using GraphQL
        Returns additions, deletions, and commit count for this user
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            cursor: Pagination cursor
            
        Returns:
            tuple: (additions, deletions, commit_count)
        """
        query = """
        query($owner: String!, $repo_name: String!, $cursor: String) {
            repository(owner: $owner, name: $repo_name) {
                defaultBranchRef {
                    target {
                        ... on Commit {
                            history(first: 100, after: $cursor) {
                                totalCount
                                pageInfo {
                                    hasNextPage
                                    endCursor
                                }
                                edges {
                                    node {
                                        author {
                                            user {
                                                id
                                            }
                                        }
                                        additions
                                        deletions
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {"owner": owner, "repo_name": repo_name, "cursor": cursor}
        response = requests.post(
            self.api_url,
            json={"query": query, "variables": variables},
            headers=self.headers
        )
        
        if response.status_code != 200:
            return 0, 0, 0
        
        data = response.json()
        
        # Check if repo exists and has commits
        if (not data.get("data") or 
            not data["data"].get("repository") or 
            not data["data"]["repository"].get("defaultBranchRef")):
            return 0, 0, 0
        
        history = data["data"]["repository"]["defaultBranchRef"]["target"]["history"]
        
        additions = 0
        deletions = 0
        commits = 0
        
        # Count only commits by this user
        for edge in history["edges"]:
            if edge["node"]["author"]["user"] == self.owner_id:
                additions += edge["node"]["additions"]
                deletions += edge["node"]["deletions"]
                commits += 1
        
        # Recursively fetch more if there are more pages
        if history["pageInfo"]["hasNextPage"]:
            add_more, del_more, comm_more = self.fetch_repo_commits(
                owner, repo_name, history["pageInfo"]["endCursor"]
            )
            additions += add_more
            deletions += del_more
            commits += comm_more
        
        return additions, deletions, commits
    
    def load_loc_cache(self, comment_lines=0):
        """
        Load LOC cache from file (Andrew's format)
        Format: repo_hash commit_count my_commits additions deletions
        
        Args:
            comment_lines: Number of comment lines at start of file
            
        Returns:
            list: Lines from cache file
        """
        # Ensure cache directory exists
        os.makedirs('cache', exist_ok=True)
        
        if not os.path.exists(self.cache_file):
            # Create empty cache file with comments
            with open(self.cache_file, 'w') as f:
                for _ in range(comment_lines):
                    f.write('# Cache file for GitHub statistics\n')
            return []
        
        try:
            with open(self.cache_file, 'r') as f:
                lines = f.readlines()
                return lines[comment_lines:]  # Skip comment lines
        except:
            return []
    
    def save_loc_cache(self, cache_lines, comment_lines=0):
        """
        Save LOC cache to file
        
        Args:
            cache_lines: List of cache data lines
            comment_lines: Number of comment lines to preserve
        """
        with open(self.cache_file, 'w') as f:
            # Write comment header
            for _ in range(comment_lines):
                f.write('# Cache file for GitHub statistics\n')
            # Write cache data
            f.writelines(cache_lines)
    
    def get_all_repos_for_loc(self, owner_affiliation=['OWNER'], cursor=None, edges=[]):
        """
        Get all repositories with commit counts for LOC calculation
        
        Args:
            owner_affiliation: Repository affiliations to include
            cursor: Pagination cursor
            edges: Accumulated edges from pagination
            
        Returns:
            list: Repository data edges
        """
        query = """
        query($login: String!, $owner_affiliation: [RepositoryAffiliation], $cursor: String) {
            user(login: $login) {
                repositories(first: 60, after: $cursor, ownerAffiliations: $owner_affiliation) {
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                    edges {
                        node {
                            nameWithOwner
                            defaultBranchRef {
                                target {
                                    ... on Commit {
                                        history {
                                            totalCount
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "login": self.username,
            "owner_affiliation": owner_affiliation,
            "cursor": cursor
        }
        
        response = requests.post(
            self.api_url,
            json={"query": query, "variables": variables},
            headers=self.headers
        )
        
        if response.status_code != 200:
            return edges
        
        data = response.json()["data"]["user"]["repositories"]
        edges += data["edges"]
        
        if data["pageInfo"]["hasNextPage"]:
            return self.get_all_repos_for_loc(
                owner_affiliation,
                data["pageInfo"]["endCursor"],
                edges
            )
        
        return edges
    
    def calculate_total_loc(self, owner_affiliation=['OWNER'], comment_lines=1, force_refresh=False):
        """
        Calculate total lines of code with caching (Andrew's method)
        
        Args:
            owner_affiliation: Repository affiliations
            comment_lines: Number of comment lines in cache
            force_refresh: Force recalculation
            
        Returns:
            dict: LOC statistics (additions, deletions, net, commits, cached)
        """
        print("Fetching repository list...")
        edges = self.get_all_repos_for_loc(owner_affiliation)
        
        # Load cache
        cache_lines = [] if force_refresh else self.load_loc_cache(comment_lines)
        
        # Build cache dictionary from lines
        cache_dict = {}
        for line in cache_lines:
            parts = line.strip().split()
            if len(parts) >= 5:
                cache_dict[parts[0]] = {
                    'commit_count': int(parts[1]),
                    'my_commits': int(parts[2]),
                    'additions': int(parts[3]),
                    'deletions': int(parts[4])
                }
        
        total_add = 0
        total_del = 0
        total_commits = 0
        new_cache_lines = []
        cached = True
        
        for edge in edges:
            repo_name = edge["node"]["nameWithOwner"]
            repo_hash = hashlib.sha256(repo_name.encode('utf-8')).hexdigest()
            
            # Check if repo has commits
            if not edge["node"].get("defaultBranchRef"):
                new_cache_lines.append(f"{repo_hash} 0 0 0 0\n")
                continue
            
            current_commit_count = edge["node"]["defaultBranchRef"]["target"]["history"]["totalCount"]
            
            # Check cache
            if repo_hash in cache_dict and cache_dict[repo_hash]['commit_count'] == current_commit_count:
                # Use cached data
                data = cache_dict[repo_hash]
                total_add += data['additions']
                total_del += data['deletions']
                total_commits += data['my_commits']
                new_cache_lines.append(
                    f"{repo_hash} {data['commit_count']} {data['my_commits']} "
                    f"{data['additions']} {data['deletions']}\n"
                )
                print(f"  ✓ {repo_name} (cached)")
            else:
                # Recalculate
                cached = False
                print(f"  → {repo_name} (fetching...)")
                owner, repo = repo_name.split('/')
                additions, deletions, commits = self.fetch_repo_commits(owner, repo)
                
                total_add += additions
                total_del += deletions
                total_commits += commits
                
                new_cache_lines.append(
                    f"{repo_hash} {current_commit_count} {commits} {additions} {deletions}\n"
                )
                
                # Small delay to avoid rate limits
                time.sleep(0.3)
        
        # Save updated cache
        self.save_loc_cache(new_cache_lines, comment_lines)
        
        return {
            'additions': total_add,
            'deletions': total_del,
            'net': total_add - total_del,
            'commits': total_commits,
            'cached': cached
        }
    
    def justify_format(self, root, element_id, new_text, dot_length=0):
        """
        Updates text and adjusts dot justification (Andrew's method)
        
        Args:
            root: SVG root element
            element_id: ID of element to update
            new_text: New text value
            dot_length: Expected length for justification
        """
        # Format numbers with commas
        if isinstance(new_text, int):
            new_text = f"{new_text:,}"
        new_text = str(new_text)
        
        # Find and update the element
        element = root.find(f".//*[@id='{element_id}']")
        if element is not None:
            element.text = new_text
        
        # Update dots for justification
        if dot_length > 0:
            just_len = max(0, dot_length - len(new_text))
            if just_len <= 2:
                dot_map = {0: '', 1: ' ', 2: '. '}
                dot_string = dot_map[just_len]
            else:
                dot_string = ' ' + ('.' * just_len) + ' '
            
            dot_element = root.find(f".//*[@id='{element_id}_dots']")
            if dot_element is not None:
                dot_element.text = dot_string
    
    def update_svg(self, svg_file, stats):
        """
        Update SVG file with statistics using lxml (Andrew's format)
        
        Args:
            svg_file: Path to SVG file
            stats: Dictionary containing statistics to update
        """
        if not os.path.exists(svg_file):
            print(f"SVG file not found: {svg_file}")
            return
        
        # Parse SVG
        tree = etree.parse(svg_file)
        root = tree.getroot()
        
        # Update each stat with justification
        if 'age' in stats:
            self.justify_format(root, 'age_data', stats['age'], 0)
        if 'commits' in stats:
            self.justify_format(root, 'commit_data', stats['commits'], 22)
        if 'stars' in stats:
            self.justify_format(root, 'star_data', stats['stars'], 14)
        if 'repos' in stats:
            self.justify_format(root, 'repo_data', stats['repos'], 6)
        if 'contributed_repos' in stats:
            self.justify_format(root, 'contrib_data', stats['contributed_repos'], 0)
        if 'followers' in stats:
            self.justify_format(root, 'follower_data', stats['followers'], 10)
        if 'loc_net' in stats:
            self.justify_format(root, 'loc_data', stats['loc_net'], 9)
        if 'loc_add' in stats:
            self.justify_format(root, 'loc_add', stats['loc_add'], 0)
        if 'loc_del' in stats:
            self.justify_format(root, 'loc_del', stats['loc_del'], 7)
        
        # Write back
        tree.write(svg_file, encoding='utf-8', xml_declaration=True)
        print(f"✓ Updated {svg_file}")


def perf_counter(func, *args):
    """Calculate execution time of a function"""
    start = time.perf_counter()
    result = func(*args)
    elapsed = time.perf_counter() - start
    return result, elapsed


def print_perf(label, elapsed, value=None):
    """Print performance timing"""
    time_str = f"{elapsed:.4f} s" if elapsed > 1 else f"{elapsed * 1000:.4f} ms"
    print(f"   {label:<22} {time_str:>12}", end="")
    if value is not None:
        print(f" → {value}")
    else:
        print()


def main():
    """Main execution function"""
    print('Calculating GitHub statistics...')
    print('Execution times:')
    
    # Get user data and account creation date
    user_data, user_time = perf_counter(user_getter, USER_NAME)
    global OWNER_ID
    OWNER_ID, acc_date = user_data
    formatter('account data', user_time)
    
    # Calculate account age (you can customize this to your birthdate or keep it as account age)
    acc_datetime = datetime.datetime.strptime(acc_date, '%Y-%m-%dT%H:%M:%SZ')
    age_data, age_time = perf_counter(daily_readme, acc_datetime)
    formatter('age calculation', age_time)
    
    # Get lines of code statistics (with caching)
    total_loc, loc_time = perf_counter(loc_query, ['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER'], 0)
    formatter('LOC (cached)' if total_loc[-1] else 'LOC (no cache)', loc_time)
    
    # Get commit count
    commit_data, commit_time = perf_counter(commit_counter, 0)
    formatter('commits', commit_time)
    
    # Get stars, repos, and contributions
    star_data, star_time = perf_counter(graph_repos_stars, 'stars', ['OWNER'])
    formatter('stars', star_time)
    
    repo_data, repo_time = perf_counter(graph_repos_stars, 'repos', ['OWNER'])
    formatter('repositories', repo_time)
    
    contrib_data, contrib_time = perf_counter(graph_repos_stars, 'repos', ['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER'])
    formatter('contributions', contrib_time)
    
    # Get follower count
    follower_data, follower_time = perf_counter(follower_getter, USER_NAME)
    formatter('followers', follower_time)
    
    # Format LOC data
    for index in range(len(total_loc) - 1):
        total_loc[index] = '{:,}'.format(total_loc[index])
    
    # Update both SVG files
    svg_overwrite('dark_mode.svg', age_data, commit_data, star_data, repo_data, 
                 contrib_data, follower_data, total_loc[:-1])
    svg_overwrite('light_mode.svg', age_data, commit_data, star_data, repo_data, 
                 contrib_data, follower_data, total_loc[:-1])
    
    print('\n✓ SVG files updated successfully!')
    print(f'\nTotal GitHub GraphQL API calls: {sum(QUERY_COUNT.values())}')
    for funct_name, count in QUERY_COUNT.items():
        if count > 0:
            print(f'   {funct_name}: {count}')


if __name__ == "__main__":
    main()
