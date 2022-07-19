import requests
from bs4 import BeautifulSoup
import re
import json
import os

bearer_token = 'AAAAAAAAAAAAAAAAAAAAAAMlewEAAAAAl3yqrDPaP3YQJvMgzyGfse4ZxNo%3Dewys4deYQb5QbukLv21J1yTl8pPvPGJZpXUT7Ldd4NMtSnCuQe'
headers = {'Authorization': f"Bearer {bearer_token}"}

def get_article(url):
	"""
	Use requests and BS4, get and parse the article from saltwire's website. Return a clean string.
	"""
	#base = "https://www.saltwire.com"
	#url = base+path
	r = requests.get(url)
	soup = BeautifulSoup(r.text)
	info = soup.find("span","sw-article__author-byline")
	try:
		byline = info.find("a").text
		
	except:
		byline = None
	title = soup.find("h1").text
	posted = re.findall("(?<=Posted: ).*",info.text)[0].split("|")[0].strip()
	para = soup.find_all(lambda tag: tag.name == 'p' and not tag.attrs)
	removals = ['Start your Membership\xa0Now','UNLIMITED DIGITAL ACCESS','SUBSCRIBE NOW',
			   'Ensure local journalism stays in your community by purchasing a membership today.']
	text = []
	for p in para:
		if (p.text == "") or (p.text.strip() in removals):
			pass
		else:
			text.append(p.text.strip())
	c = "\n".join(text)
	clean_text = c.replace(u'\xa0', u' ').replace("\n", " ")
	#return info,author,url,title,body
	return {'posted':posted,'byline':byline,'url':url,'title':title,'body':clean_text}

def get_replies(conversation_id):
	"""Return direct replies dictionary"""
	base = 'https://api.twitter.com/2/tweets/search/recent'
	fields = f"?query=conversation_id:{conversation_id}&tweet.fields=in_reply_to_user_id,author_id,created_at,conversation_id"
	url = base+fields
	r = requests.get(url, headers=headers)
	j = json.loads(r.text)
	if 'data' in j:
		return j['data']