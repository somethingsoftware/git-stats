#!/usr/bin/env python3
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

from github import github
from cloc import cloc

def timed_function(title: str, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    start = time.time()
    ret = func(*args, **kwargs)
    print(f"{title} {time.time() - start} seconds.")
    return ret

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
        if (github.check_usr_valid(config.username) == False):
            if config.do_print:
                print(f"User {config.username} not found.")
            return False

        repos = github.get_repos(config.username, config.max_repos)
        if (repos == None):
            if config.do_print:
                print(f"Failed to get repo names for {config.username}.")
            return False

        if config.do_print:
            print(f"Found {len(repos)} repos.")
        for repo in repos:
            if repo['clone_url'] in config.exclude:
                continue
            if github.check_fork(repo) and config.exclude_forks:
                continue
            if config.do_print:
                print(f"Cloning {repo.get('name')}...")

            clone_dir = os.path.join(config.tmp_dir, repo['name'])
            code = os.system(f"git clone --depth 1 {repo['clone_url']}  {clone_dir} 2> /dev/null")
            if code:
                print(f"failure trying to clone repo '{repo['name']}'")

    except Exception as e:
        print(e)
        return False
    return True

@click.command()
@click.option('--username', prompt='github username',
	help='The github username for which you want to analyze language use.')
@click.option('--max_repos', default=100, help='The max number of repos to analyze. (default: 100)')
@click.option('--excluded_langs', default='Text', help='Languages to exclude from the analysis. (type: list[str], default: "[\'Text\']")')
@click.option('--excluded_repos', default="", help='Repos to exclude from the analysis. (type: list[str], default: "[]")')
@click.option('-n', is_flag=True, default=True, help='Disable printing of git cloneing statuses.')
@click.option('-e', is_flag=True, default=True, help='Exclude forks from the analysis.')
@click.option('-d', is_flag=True, default=False, help='Don\'t delete temp directory and print it.')
def main(username: str, max_repos: int, excluded_langs: str, excluded_repos: str,
         n: bool, e: bool, d: bool) -> None:
    excluded_languages: list[str] = re.split('[, ]+', excluded_langs)
    excluded_repositories: list[str] = re.split('[, ]+', excluded_repos)
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
        exclude=excluded_repositories,
        max_repos=max_repos,
        exclude_forks=e,
        do_print=n
        )
    ret = download_repos(config)
    if not ret:
        print("Failed to download repos.")
        return
    print(f"Downloaded repos in {time.time() - start} seconds.")


    langs = timed_function("Counted repos in", cloc.count_lang_repos, temp_dir)
    percentages = timed_function("Calculated percentages in", cloc.language_percentage, langs)

    if not d:
        timed_function("Deleted repos in", temp_dir_obj.cleanup)

    languages: dict[str, Any] = dict()
    for language in percentages:
        if language in excluded_languages:
            continue
        languages[language] = {
            'files': langs[language].nFiles,
            'lines': langs[language].code,
            'percentage': percentages[language],
            'repos': langs[language].repos,
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
