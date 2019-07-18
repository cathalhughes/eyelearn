from splinter import Browser
import time
import os



executable_path = {'executable_path':'static/testing/chromedriver.exe'}
#executable_path = {'executable_path':'static/testing/geckodriver.exe'}

browser = Browser('chrome', **executable_path) ##chrome
#browser = Browser(user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 11_1 like Mac OS X) AppleWebKit/604.2.8 (KHTML, like Gecko) Version/11.0 Mobile/15B57 Safari/604.1", **executable_path) ## iPhone
#browser = Browser('firefox', **executable_path) ##firefox

#Test Case 1
print("=========================================================")
print("Running Test Case 1: Visit Home Page")
browser.visit('localhost:5000/')
print("Visiting browser...")
time.sleep(2)
# element = browser.driver.find_element_by_id("imageFile")
# pathToImage = os.path.abspath("static/testing/Capture5.JPG")
# element.send_keys(pathToImage)
# print("Image chosen...")
# time.sleep(2)
# browser.click_link_by_id('submit')
# print("Image submitted for classification...")
# time.sleep(2)
assert browser.is_text_present('Please log in to access this page.') == True
assert browser.is_text_present('Sign In') == True
print("=========================================================")

print("Running Test Case 2: Sign in to app")
browser.fill('username', 'student')
browser.fill('password', "1")
browser.check('remember_me')
browser.find_by_name('submit').first.click()


#Test Case 2
print("Running Test Case 3: Visit Activities/Utilities Page")
#browser.visit('http://54.191.193.7:5000/')
print("Clicking Play Button")
time.sleep(2)
browser.find_link_by_text('Play').first.click()
print("Play button pressed...")
time.sleep(2)
assert browser.is_text_present('Activities') == True
print("=========================================================")

#Test Case 3
print("Running Test Case 4: Test Image Upload Pages")
browser.find_by_id("sportsButton").first.click()
print("Visiting sports upload image activity")
assert "selfie/sports" in browser.url
browser.back()
browser.find_by_id("vehiclesButton").first.click()
assert "selfie/vehicles" in browser.url
browser.back()
# browser.find_by_id("emojisButton").first.click()
# assert "selfie/emojis" in browser.url
# browser.back()
# browser.find_by_id("animalsButton").first.click()
# assert "selfie/animals" in browser.url

#Test Case 4:
print("Running test case 5: Test Image swipe pages accessible")
browser.find_by_id("swipeSports").first.click()
assert "swipe/sports" in browser.url
browser.back()
browser.find_by_id("swipeVehicles").first.click()
assert "swipe/vehicles" in browser.url
browser.back()
browser.find_by_id("swipeEmojis").first.click()
assert "swipe/emojis" in browser.url
browser.back()
browser.find_by_id("swipeAnimals").first.click()
assert "swipe/animals" in browser.url
browser.back()

#Test Case 5
print("Running Test Case 6: Visit other activity pages")
browser.find_by_id("scrambleButton").first.click()
assert "scramble" in browser.url
browser.back()
browser.find_by_id("tts").first.click()
assert "tts" in browser.url
browser.back()
browser.find_by_id("speech").first.click()
assert "speech" in browser.url
browser.back()
browser.find_by_id("classroom").first.click()
assert "classroom" in browser.url
browser.back()


#Test Case 6
print("Test Case 7: Test Canvas Pages")
browser.find_by_id("spelling").first.click()
assert "numbersOrSpelling" in browser.url
browser.back()
browser.find_by_id("numbers").first.click()
assert "numbers" in browser.url
browser.back()

#Test Case 7
print("Test Case 8: Visit Utility Pages")
browser.find_by_id("speechTranslator").first.click()
assert "speechTranslation" in browser.url
browser.back()
browser.find_by_id("objectTranslator").first.click()
assert "image" in browser.url
browser.back()


#Test Case 8
print("Test Case 9: Visit Navbar Links")
browser.find_link_by_text("Home").first.click()
assert "/" in browser.url
browser.find_link_by_text("About").first.click()
assert "about" in browser.url
browser.find_link_by_text("Play").first.click()
assert "difficulty" in browser.url

print("Test Case 9: Visit profile pages")
browser.find_link_by_text("Home").first.click()
browser.find_link_by_text("student testclass").first.click()
assert browser.is_text_present("User: student")

print("Test Case 10: Visit Analytics Pages")
browser.find_by_id("practiceAreaButton1").first.click()
assert browser.is_text_present("Analytics")

print("Test Case 11: Visit Edit profile Page")
browser.back()
browser.find_link_by_text("Edit your profile").first.click()
browser.fill("about_me", "I love French")
assert browser.is_text_present("About me")

print("Test Case 12: Visit join a Class page")
browser.back()
browser.find_link_by_text("Join a Class").first.click()
browser.fill("class_id", "test")
assert browser.is_text_present("Enter Class Code")

print("Test Case 13: Visit Change Class Page")
browser.back()
browser.find_link_by_text("Change Current Active Class or Practice Area").first.click()
assert browser.is_text_present("Your Practice Areas:")

print("Test Case 14: Logout")
browser.find_link_by_text("Home").first.click()
browser.find_link_by_text("Logout").first.click()
assert browser.is_text_present('Sign In') == True

print("Test Case 15: Register")
print("Clicking register link")
browser.find_link_by_text("Click to Register!").first.click()
browser.fill('username', 'student')
browser.fill('password', "1")
browser.fill('password2', "1")
browser.find_by_name('submit').first.click()
assert browser.is_text_present("Register")











browser.quit()
