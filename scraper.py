from instapy import InstaPy
from instascrape import *
from time import sleep
#browser = webdriver.Firefox()
#browser.get('https://www.instagram.com/bohdanzoshchenko')
#sleep(5)



sess = InstaPy(username="bohdanzoshchenko", password="artaxerx", headless_browser=True)
sess.login() 

sleep(2)


session_id = sess.browser.session_id

sleep(2)
# Connecting the profile 
# Instantiate the scraper objects 
profile = Profile('https://www.instagram.com/mari_ko_bakeryclub/')

# Scrape their respective data 
profile.scrape(webdriver=sess.browser)

recent = profile.get_recent_posts(1)[0]



sess.browser.close()
print("Awesome")