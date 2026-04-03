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
        new_text = f"{new_text:,}"
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
    
    print('\n[OK] SVG files updated successfully!')
    print(f'\nTotal GitHub GraphQL API calls: {sum(QUERY_COUNT.values())}')
    for funct_name, count in QUERY_COUNT.items():
        if count > 0:
            print(f'\n   {funct_name}: {count}')
