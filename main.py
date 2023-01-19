#!/usr/bin/env python3
import requests
import json
import os
import sys

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
	repsonse = requests.get('https://api.github.com/users/' + username + '/repos?per_page=2')
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
def parse_languages(username):
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

# Main function
def main():
	username = 'Mr-Bossman'
	excluded_languages = ['C']
	excluded_repos = []
	download_repos(username,excluded_repos)
	languages = parse_languages(username)
	os.system("rm -rf /tmp/" + username)
	for language in excluded_languages:
		if language in languages:
			del languages[language]
	percentages = language_percentage(languages)
	print(percentages)

main()