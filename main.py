#!/usr/bin/env python3
import requests
import json
import os
import sys
import click
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

#Check if the user is valid
def check_usr_valid(username):
	response = requests.get('https://api.github.com/users/' + username)
	if(response.status_code == 200):
		return True
	elif (response.status_code == 404):
		return False
	return None

#Get the user's repos
def get_repos(username):
	repsonse = requests.get('https://api.github.com/users/' + username + '/repos?per_page=100')
	if(repsonse.status_code == 200):
		return repsonse.json()
	return None

#Check if repo is a fork
def check_fork(repo):
	if(repo['fork'] == True):
		return True
	return False

#Download the repos
def download_repos(username,exclude):
	try:
		os.system("rm -rf /tmp/" + username)
	except:
		pass
	try:
		if(check_usr_valid(username) == True):
			repos = get_repos(username)
			if(repos == None):
				return False
			cwd = os.getcwd()
			os.mkdir("/tmp/" + username)
			os.chdir("/tmp/" + username)
			for repo in repos:
				if (not check_fork(repo)) and (not (repo['clone_url'] in exclude)):
					os.system('git clone --depth 1 ' + repo['clone_url'] +' 2> /dev/null')
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
	langsum = sum([ l['code'] for l in languages.values()])
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
		repo_languages = os.popen('cloc /tmp/' + username + '/' + repo + ' --json')
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
@click.option('--username', prompt='github username', help='The github username for which you want to analyze language use.')
def main(username):
	excluded_languages = ['C']
	excluded_repos = []
	download_repos(username,excluded_repos)
	
	lines = parse_lines(username)
	percentages = language_percentage(lines)
	repos_per_language = count_lang_repos(username)

	os.system("rm -rf /tmp/" + username)

	languages = dict()
	for language in percentages:
		if language in excluded_languages:
			continue
		languages[language] = dict()
		languages[language]['files'] = lines[language]['nFiles']
		languages[language]['lines'] = lines[language]['code']
		languages[language]['percentage'] = percentages[language]
		languages[language]['repos'] = repos_per_language[language]
		languages[language]['name'] = language
	print(languages)

	df = pd.DataFrame(languages).transpose()
	print(df)
	
	# use the scatterplot function to build the bubble map
	sns.scatterplot(data=df, x="files", y="repos", size="lines", legend=False , sizes=(20, 2000))
	for i in range(df.shape[0]):
		plt.text(x=df.files[i]+0.3,y=df.repos[i]+0.3,s=df.name[i],fontdict=dict(color='red',size=10),bbox=dict(facecolor='yellow',alpha=0.5))


	# show the graph
	plt.show()


main()