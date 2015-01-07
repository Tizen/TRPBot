# Urban Dictionary Query
import requests,urllib
from bs4 import BeautifulSoup as soup

def define(term):
	result = requests.get('http://www.urbandictionary.com/define.php?%s' % (urllib.urlencode({'term':term}),))
	content = result.content if result.status_code == 200 else None
	if content:
		html = soup(content)
		desc = html.find('div',{'class':'meaning'})
		desc = '%s: %s' % (term,desc.text.strip(),) if desc else ''
		exam = html.find('div',{'class':'example'})
		exam = ' (%s)' % (exam.text.strip(),) if desc and exam and len(exam.text.strip()) else ''
		retval = '%s%s' % (desc,exam,)
	else:
		retval = ''
	return retval
