#!/usr/bin/env python3
import requests
import json
import os
import click
from typing import Any, Callable
from dataclasses import dataclass
import time
import tempfile
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import re

def run_in_dir(directory: str, command: str) -> None:
    cwd = os.getcwd()
    os.chdir(directory)
    os.system(command)
    os.chdir(cwd)

def timed_function(title: str, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    start = time.time()
    ret = func(*args, **kwargs)
    print(f"{title} {time.time() - start} seconds.")
    return ret

# Check if the user is valid
def check_usr_valid(username: str) -> bool | None:
    api_url = f"https://api.github.com/users/{username}"
    response = requests.get(api_url)
    if (response.status_code == 200):
        return True
    elif (response.status_code == 404):
        return False
    return None

# Get the user's repos
def get_repos(username: str, max_repos: int) -> list[dict[str, Any]] | None:
    api_url = f"https://api.github.com/users/{username}"
    repsonse = requests.get(f"{api_url}/repos?per_page={max_repos}")
    if (repsonse.status_code == 200):
        return repsonse.json()
    return None

# Check if repo is a fork
def check_fork(repo: dict[str, Any]) -> bool:
    if (repo.get('fork') == True):
        return True
    return False


@dataclass
class DowloadConfig:
    tmp_dir: str
    username: str
    exclude: list[str]
    max_repos: int
    exclude_forks: bool
    do_print: bool

# Download the repos
def download_repos(config: DowloadConfig) -> bool:
    try:
        if (check_usr_valid(config.username) == False):
            if config.do_print:
                print(f"User {config.username} not found.")
            return False

        repos = get_repos(config.username, config.max_repos)
        if (repos == None):
            if config.do_print:
                print(f"Failed to get repo names for {config.username}.")
            return False

        if config.do_print:
            print(f"Found {len(repos)} repos.")
        for repo in repos:
            if repo['clone_url'] in config.exclude:
                continue
            if check_fork(repo) and config.exclude_forks:
                continue
            if config.do_print:
                print(f"Cloning {repo.get('name')}...")
            run_in_dir(config.tmp_dir, f"git clone --depth 1 {repo['clone_url']} 2> /dev/null")

    except Exception as e:
        print(e)
        return False
    return True

# Parse languages in the repos
def parse_lines(tmp_dir: str) -> dict[str, Any]:
    languages = os.popen(f"cloc --json {tmp_dir}")
    languages = json.loads(languages.read())
    del languages['header']
    del languages['SUM']
    return languages

# Calculate the percentage of each language
def language_percentage(languages: dict[str, Any]) -> dict[str, float]:
    lang_sum = sum([l['code'] for l in languages.values()])
    percentages: dict[str, float] = dict()
    for language in languages:
        percentages[language] = 100 * languages[language]['code'] / lang_sum
    return percentages

# Calculate the number of repos per language
def count_lang_repos(tmp_dir: str) -> dict[str, int]:
    repo_language_counts: dict[str, int] = dict()
    for repo in os.listdir(tmp_dir):
        if not os.path.isdir(f"{tmp_dir}/{repo}"):
            continue
        repo_languages = os.popen(
            f"cloc {tmp_dir}/{repo} --json")
        repo_languages = json.loads(repo_languages.read())
        del repo_languages['header']
        del repo_languages['SUM']
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
@click.option('--excluded_languages', default='Text', help='Languages to exclude from the analysis. (type: list[str], default: "[\'Text\']")')
@click.option('--excluded_repos', default="", help='Repos to exclude from the analysis. (type: list[str], default: "[]")')
@click.option('-n', is_flag=True, default=True, help='Disable printing of git cloneing statuses.')
@click.option('-e', is_flag=True, default=True, help='Exclude forks from the analysis.')
@click.option('-d', is_flag=True, default=False, help='Don\'t delete temp directory and print it.')
def main(username: str, max_repos: int, excluded_languages: str, excluded_repos: str,
         n: bool, e: bool, d: bool) -> None:
    excluded_langs: list[str] = re.split('[, ]+', excluded_languages)
    excluded_repos: list[str] = re.split('[, ]+', excluded_repos)
    temp_dir_obj = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    temp_dir = temp_dir_obj.name
    if d:
        print(f"Temp directory: {temp_dir}")

    # start total timer
    total_start = time.time()
    # start a timer
    start = time.time()
    config = DowloadConfig(
        tmp_dir=temp_dir,
        username=username,
        exclude=excluded_repos,
        max_repos=max_repos,
        exclude_forks=e,
        do_print=n
        )
    ret = download_repos(config)
    if not ret:
        print("Failed to download repos.")
        return
    print(f"Downloaded repos in {time.time() - start} seconds.")

    lines = timed_function("Parsed lines in", parse_lines, temp_dir)
    percentages = timed_function("Calculated percentages in", language_percentage, lines)

    repos_per_language = timed_function("Counted repos in", count_lang_repos, temp_dir)

    if not d:
        timed_function("Deleted repos in", temp_dir_obj.cleanup)

    languages: dict[str, Any] = dict()
    for language in percentages:
        if language in excluded_langs:
            continue
        languages[language] = {
            'files': lines[language]['nFiles'],
            'lines': lines[language]['code'],
            'percentage': percentages[language],
            'repos': repos_per_language[language],
            'name': language}

    if not languages:
        print("No languages found.")
        return

    df = pd.DataFrame(languages).transpose() # type: ignore

    # use the scatterplot function to build the bubble map
    sns.scatterplot( # type: ignore
        data=df,
        x="files",
        y="repos",
        size="lines",
        legend=False,
        sizes=(20, 2000))

    plt.xscale('log') # type: ignore
    plt.yscale('log') # type: ignore
    for i in range(df.shape[0]):
        frame: pd.Series[Any] = df.iloc[i]
        bbox = dict(facecolor='black', alpha=0.6)
        fontdict = dict(color='white', size=9)
        plt.text( # type: ignore
            # add space using the log function to label the bubbles
            x=frame.files+(frame.files*0.1),
            y=frame.repos+(frame.repos*0.1),
            s=str(frame.name),
            fontdict=fontdict,
            bbox=bbox)

    print(f"Total time: {time.time() - total_start} seconds.")
    # show the graph
    plt.show() # type: ignore

if __name__ == "__main__":
	main()
