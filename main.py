from selenium import webdriver
import time

driver = webdriver.Firefox()
driver.get("https://wx.qq.com")

qr = driver.find_element_by_css_selector("img.img").get_attribute("src")
print(qr)
def capturechat(driver):
    response = driver.find_elements_by_css_selector("div.chat_item div.avatar i.icon")
    return response

while True:
    time.sleep(60)
    response=capturechat(driver)

    if response!=[]:
        for sender in response:
            number = int(sender.text)
            sender.click()
            sendername = driver.find_element_by_css_selector("div.title_wrap a.title_name").text
            message_raw = driver.find_elements_by_css_selector("div.message:not(.me) div.content div.plain,img.msg-img,div.voice")

            print("**********************")
            print(sendername, number)
            message = []
            for i in message_raw:
                if i.tag_name == "div":
                    if i.get_attribute("class") == "voice": message.append(i.text + " voice message received")
                    else: message.append(i.text)
                elif i.tag_name == "img": message.append("Image received")
            print(message[len(message)-number:])

            ft = [a for a in driver.find_elements_by_css_selector("div.chat_item") if "File Transfer" in a.text][0]
            ft.click()

        



# ft = [a for a in driver.find_elements_by_css_selector("div.chat_item") if "File Transfer" in a.text][0]

# [a.text for a in driver.find_elements_by_css_selector("div.message:not(.me) div.content div.plain")]