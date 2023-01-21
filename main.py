#!/usr/bin/env python3
import requests
import json
import os
import sys
import click
import time
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Check if the user is valid


def check_usr_valid(username):
    response = requests.get('https://api.github.com/users/' + username)
    if (response.status_code == 200):
        return True
    elif (response.status_code == 404):
        return False
    return None

# Get the user's repos


def get_repos(username, max_repos):
    repsonse = requests.get(
        'https://api.github.com/users/' + username + '/repos?per_page='+str(max_repos))
    if (repsonse.status_code == 200):
        return repsonse.json()
    return None

# Check if repo is a fork


def check_fork(repo):
    if (repo['fork'] == True):
        return True
    return False

# Download the repos


def download_repos(username, exclude, max_repos):
    try:
        os.system("rm -rf /tmp/" + username)
    except:
        pass
    try:
        if (check_usr_valid(username) == True):
            repos = get_repos(username, max_repos)
            if (repos == None):
                return False
            cwd = os.getcwd()
            os.mkdir("/tmp/" + username)
            os.chdir("/tmp/" + username)
            for repo in repos:
                if (not check_fork(repo)) and (not (repo['clone_url'] in exclude)):
                    os.system('git clone --depth 1 ' +
                              repo['clone_url'] + ' 2> /dev/null')
            os.chdir(cwd)
    except Exception as e:
        print(e)
        os.system("rm -rf /tmp/" + username)
        return False
    return True

# Parse languages in the repos


def parse_lines(username):
    languages = os.popen('cloc --json /tmp/' + username)
    languages = json.loads(languages.read())
    del languages['header']
    del languages['SUM']
    return languages

# Calculate the percentage of each language


def language_percentage(languages):
    langsum = sum([l['code'] for l in languages.values()])
    percentages = {}
    for language in languages:
        percentages[language] = 100*languages[language]['code'] / langsum
    return percentages

# Calculate the number of repos per language


def count_lang_repos(username):
    repo_language_counts = dict()
    for repo in os.listdir('/tmp/'+username+'/'):
        if not os.path.isdir('/tmp/'+username+'/'+repo):
            continue
        repo_languages = os.popen(
            'cloc /tmp/' + username + '/' + repo + ' --json')
        repo_languages = json.loads(repo_languages.read())
        del repo_languages['header']
        del repo_languages['SUM']
        cwd = os.getcwd()
        os.chdir('/tmp/' + username + '/' + repo)
        os.chdir(cwd)
        for language in repo_languages:
            if language not in repo_language_counts:
                repo_language_counts[language] = 1
            else:
                repo_language_counts[language] += 1
    return repo_language_counts


@click.command()
@click.option('--username', prompt='github username', 
	help='The github username for which you want to analyze language use.')
@click.option('--max_repos', default=100, help='The max number of repos to analyze. (default: 100)')
def main(username, max_repos):
    excluded_languages = ['C', 'D', 'Assembly',
                          'Scheme', 'lex', 'Expected', 'C/C++ Header']
    excluded_repos = []
    # start a timer
    start = time.time()
    download_repos(username, excluded_repos, max_repos)
    print("Downloaded repos in " + str(time.time() - start) + " seconds")
    start = time.time()
    lines = parse_lines(username)
    print("Parsed lines in " + str(time.time() - start) + " seconds")
    start = time.time()
    percentages = language_percentage(lines)
    print("Calculated percentages in " + str(time.time() - start) + " seconds")
    start = time.time()
    repos_per_language = count_lang_repos(username)
    print("Counted repos in " + str(time.time() - start) + " seconds")

    start = time.time()
    os.system("rm -rf /tmp/" + username)
    print("Deleted repos in " + str(time.time() - start) + " seconds")

    languages = dict()
    for language in percentages:
        if language in excluded_languages:
            continue
        languages[language] = {
            'files': lines[language]['nFiles'],
            'lines': lines[language]['code'],
            'percentage': percentages[language],
            'repos': repos_per_language[language],
            'name': language}
    print("Built data dict in " + str(time.time() - start) + " seconds")
    # print(languages)

    start = time.time()
    df = pd.DataFrame(languages).transpose()
    print("Built dataframe in " + str(time.time() - start) + " seconds")
    # print(df)

    # use the scatterplot function to build the bubble map
    start = time.time()
    sns.scatterplot(
        data=df,
        x="files",
        y="repos",
        size="lines",
        legend=False,
        sizes=(20, 2000))
    print("Built bubble map in " + str(time.time() - start) + " seconds")

    start = time.time()
    plt.xscale('log')
    plt.yscale('log')
    for i in range(df.shape[0]):
        plt.text(
			# add space using the log function to label the bubbles
            x=df.files[i]+(df.files[i]*0.1),
            y=df.repos[i]+(df.repos[i]*0.1),
            s=df.name[i],
            fontdict=dict(
                color='white',
                size=9),
            bbox=dict(
                facecolor='black',
                alpha=0.6))

    print("Built graph in " + str(time.time() - start) + " seconds")
    print("Total time: " + str(time.time() - total_start) + " seconds")
    # show the graph
    plt.show()


total_start = time.time()
main()
