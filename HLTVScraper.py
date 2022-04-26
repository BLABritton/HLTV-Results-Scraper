import cfscrape
import datetime
import csv
import time
from bs4 import BeautifulSoup

scraper = cfscrape.CloudflareScraper()
base_url = "https://www.hltv.org/results?offset=0"
response = scraper.get(base_url)
soup = BeautifulSoup(response.content, "lxml")
print("Sucessfully got soup code 2")

pagination_data = soup.find("span", {"class": "pagination-data"}).text
page_count = round((int(pagination_data.split("of ")[1])/100)*100)

maps_final = []
rate_limit_wait_time = 360

def get_lines_in_results():
	lines = []
	with open("results.csv", "r") as file:
		reader = csv.reader(file)
		for row in reader:
			lines.append(row)
		file.close()
	return(lines)

def write_to_results():
	lines = get_lines_in_results()
	for map_ in maps_final:
		if map_ not in lines:
			lines.append(map_)
	with open("results.csv", "w", newline="") as write_file:
		writer = csv.writer(write_file)
		for line in lines:
			writer.writerow(line)
		write_file.close()

def write_page_at_error(page):
	with open("lastpage.txt", "w") as file:
		file.write(str(page))
		file.close()

def get_last_page():
	with open("lastpage.txt", "r") as file:
		page = int(file.read())
		file.close()
	return(page)
print("Starting loop.")
for page in range(get_last_page(), page_count, 100):
	write_page_at_error(page)
	url = "{0}={1}".format(base_url.split("=")[0], str(page))
	response = scraper.get(url)
	if str(response.status_code)[0] != "2":
		write_page_at_error(page)
		write_to_results()
		while str(response.status_code)[0] != "2":
			print("\n Error fetching page, prob rate limited.")
			print(f"Trying again in {rate_limit_wait_time} seconds.")
			time.sleep(rate_limit_wait_time)
			rate_limit_wait_time = rate_limit_wait_time*1.5
			response = scraper.get(url)
	soup = BeautifulSoup(response.content, "html.parser")
	print("Sucessfully got soup code 1")
	results_all = soup.find("div", {"class": "results-holder allres"}).find("div", {"class": "results-all"})
	results_by_date = results_all.find_all("div", class_="results-sublist".split())
	for result in results_by_date:
		time.sleep(25)
		print("Sleeping for 25 seconds to prevent rate limit.")
		game_date = result.find("span", {"class": "standard-headline"}).text.split("Results for ")[1]
		for game in result.find_all("div", class_="result-con".split()):
			time.sleep(6)
			print("Sleeping for 6 seconds to prevent rate limit.")
			maps = []
			gameurl = game.find("a", {"class": "a-reset"}, href=True)["href"]
			match_type = game.find("div", {"class": "map-text"}).text
			try:
				score_won = game.find("span", {"class": "score-won"}).text
			except:
				continue
			try:
				score_lost = game.find("span", {"class": "score-lost"}).text
			except:
				continue
			event_name = game.find("span", {"class": "event-name"}).text
			#get all maps from game
			url_match_page = f"https://www.hltv.org{gameurl}"
			response_match_page = scraper.get(url_match_page)
			if str(response_match_page.status_code)[0] != "2":
				write_page_at_error(page)
				write_to_results()
				while str(response_match_page.status_code)[0] != "2":
					print("\n Error fetching page, prob rate limited.")
					print(f"Trying again in {rate_limit_wait_time} seconds.")
					time.sleep(rate_limit_wait_time)
					rate_limit_wait_time = rate_limit_wait_time*1.5
					response_match_page = scraper.get(url_match_page)
			soup_match_page = BeautifulSoup(response_match_page.content, "html.parser")
			print("Sucessfully got soup code 2")
			maps_played_count = sum([int(score_won), int(score_lost)])
			maps_column = soup_match_page.find("div", {"class": "flexbox-column"})
			for i, map_row in enumerate(maps_column.find_all("div", class_="mapholder".split()), 1):
				if i > maps_played_count:
					break
				map_name = map_row.find("div", {"class": "mapname"}).text
				for result_box in (map_row.find("div", {"class": "results played"}).findChildren("div", recursive=False)+map_row.find("div", {"class": "results played"}).findChildren("span", recursive=False)):
					if "lost" in str(result_box["class"]):
						team_lost = result_box.find("div", {"class": "results-teamname text-ellipsis"}).text
						score_lost = result_box.find("div", {"class": "results-team-score"}).text
					if "won" in str(result_box["class"]):
						team_won = result_box.find("div", {"class": "results-teamname text-ellipsis"}).text
						score_won = result_box.find("div", {"class": "results-team-score"}).text
					if str(result_box["class"]) == "['results-center']":
						scores_ct = result_box.find_all("span", class_="ct".split())
						scores_t = result_box.find_all("span", class_="t".split())
						try:
							left_ct = scores_ct[0].text
						except:
							left_ct = "0"
						try:
							left_t = scores_t[0].text
						except:
							left_t = "0"
						try:
							right_t = scores_t[1].text
						except:
							right_t = "0"
						try:
							right_ct = scores_ct[1].text
						except:
							right_ct = "0"
						if sum([int(left_ct), int(left_t)]) == 16:
							team_won_half_score = f"(CT:{left_ct},T:{left_t})"
							team_lost_half_score = f"(CT:{right_ct},T:{right_t})"
						else:
							team_lost_half_score = f"(CT:{left_ct},T:{left_t})"
							team_won_half_score = f"(CT:{right_ct},T:{right_t})"
				maps.append([gameurl, game_date, event_name, map_name, team_won, team_lost, score_won, score_lost, team_won_half_score, team_lost_half_score])
				print("Map Added for date: "+game_date)
			for map_ in maps:
				maps_final.append(map_)
		write_to_results()



