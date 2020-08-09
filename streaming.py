from selenium import webdriver
import time
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Updater, Filters
from selenium.webdriver.firefox.options import Options

f = open("token.txt", "r")
token=f.read()
print(token)
f.close()

updater = Updater(token=token, use_context=True)


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Initializing...")

    options = Options()
    # options.add_argument('--headless')
    driver = webdriver.Firefox(options=options)
    driver.get("https://wx.qq.com")

    qr = driver.find_element_by_css_selector("div.qrcode  img.img").get_attribute("src")
    basewidth = 200
    response = requests.get(qr)
    img = Image.open(BytesIO(response.content))
    wpercent = (basewidth/float(img.size[0]))
    hsize = int((float(img.size[1])*float(wpercent)))
    img = img.resize((basewidth,hsize), Image.ANTIALIAS)
    img.save('qr.jpg')
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('qr.jpg', 'rb'))
    if os.path.exists("qr.jpg"):
        os.remove("qr.jpg")

    while driver.find_element_by_css_selector("div.qrcode img.img").is_displayed():
        time.sleep(1)
    context.bot.send_message(chat_id=update.effective_chat.id, text="You have logged in")

    def capturechat(driver):
        response = driver.find_elements_by_css_selector("div.chat_item div.avatar i.icon")
        return response

    while True:
        time.sleep(30)
        response=capturechat(driver)
        if response!=[]:
            for sender in response:
                number = int(sender.text)
                sender.click()
                sendername = driver.find_element_by_css_selector("div.title_wrap a.title_name").text
                message_raw = driver.find_elements_by_css_selector("div.message:not(.me) div.content div.plain,img.msg-img,div.voice")

                #print(sendername, number)
                message = []
                for i in message_raw:
                    if i.tag_name == "div":
                        if i.get_attribute("class") == "voice": message.append(i.text + " voice message received")
                        else: message.append(i.text)
                    elif i.tag_name == "img": message.append("Image received")
                bot_message = "{} sent you {} messages:\n{}".format(sendername, number, "\n".join(message[len(message)-number:]))
                context.bot.send_message(chat_id=update.effective_chat.id, text=bot_message)
                #print(message[len(message)-number:])

                ft = [a for a in driver.find_elements_by_css_selector("div.chat_item") if "File Transfer" in a.text][0]
                ft.click()

dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
updater.start_polling()
updater.idle()

