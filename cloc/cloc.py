import os
import json
from typing import Self
from dataclasses import dataclass

@dataclass
class Lang_Stat:
    nFiles: int
    blank: int
    comment: int
    code: int

    def __init__(self, data: dict[str, int]):
        self.nFiles = data['nFiles']
        self.blank = data['blank']
        self.comment = data['comment']
        self.code = data['code']

@dataclass
class Repo_Stat(Lang_Stat):
    repos: int

    def __init__(self, data: dict[str, int] | Lang_Stat):
        if isinstance(data, Lang_Stat):
            self.nFiles = data.nFiles
            self.blank = data.blank
            self.comment = data.comment
            self.code = data.code
            self.repos = 1
        else:
            super(Repo_Stat, self).__init__(data)
            self.repos = data['repos']

    def __add__(self, other: Self) -> Self:
        return type(self)({
            'nFiles': self.nFiles + other.nFiles,
            'blank': self.blank + other.blank,
            'comment': self.comment + other.comment,
            'code': self.code + other.code,
            'repos': self.repos + other.repos
        })

@dataclass
class Lang_Stats(dict[str, Lang_Stat]):
    def __init__(self, init_val: dict[str, dict[str, int]]):
        super(Lang_Stats, self).__init__({key: Lang_Stat(value) for key, value in init_val.items()})

@dataclass
class Repo_Stats(dict[str, Repo_Stat]):
    def __init__(self, init_val: Lang_Stats):
        super(Repo_Stats, self).__init__({key: Repo_Stat(value) for key, value in init_val.items()})

    # Why do we need a return type here?
    def __iadd__(self, other: Lang_Stats) -> Self:
        for language in other:
            if language not in self:
                self[language] = Repo_Stat(other[language])
            else:
                self[language] += Repo_Stat(other[language])
        return self

# Parse languages in the repos
def parse_lines(tmp_dir: str, repo: str  = '') -> Lang_Stats:
    languages = os.popen(f"cloc --json {tmp_dir}/{repo}")
    languages = json.loads(languages.read())
    del languages['header']
    del languages['SUM']
    return Lang_Stats(languages)

# Calculate the percentage of each language
def language_percentage(languages: Lang_Stats | Repo_Stats) -> dict[str, float]:
    lang_sum = sum([l.code for l in languages.values()])
    percentages: dict[str, float] = dict()
    for language in languages:
        percentages[language] = 100 * languages[language].code / lang_sum
    return percentages


# Calculate the number of repos per language
def count_lang_repos(tmp_dir: str) -> Repo_Stats:
    repo_language_counts: Repo_Stats = Repo_Stats(Lang_Stats({}))
    for repo in os.listdir(tmp_dir):
        if not os.path.isdir(f"{tmp_dir}/{repo}"):
            continue
        repo_language_counts += parse_lines(tmp_dir, repo)
    return repo_language_counts
