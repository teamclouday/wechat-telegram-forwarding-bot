import time
from selenium import webdriver
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, Updater, Filters
from telegram import KeyboardButton, ReplyKeyboardMarkup

import base64
import requests
from PIL import Image
from io import BytesIO

ALIVE = 0

def main():
    with open("token.txt", "r") as f:
        token=f.read()

    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    def start(update, context):
        context.user_data["loggedin"] = False
        keyboard = [[KeyboardButton("Login"),
            KeyboardButton("Fetch"),
            KeyboardButton("Logout")]]
        reply_markup = ReplyKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.message.chat_id, text="bot已启动", reply_markup=reply_markup)
        return ALIVE

    def button(update, context):
        if update.message.text == "Login":
            login(update, context)
        elif update.message.text == "Fetch":
            fetch(update, context)
        elif update.message.text == "Logout":
            logout(update, context)
        return ALIVE

    def login(update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="正在初始化。。。")

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        driver.get("https://wx.qq.com/?lang=en_US")

        qr = driver.find_element_by_css_selector("div.qrcode img.img")
        qr_image = Image.open(BytesIO(requests.get(qr.get_attribute("src")).content))
        qr_image = qr_image.resize((qr_image.width//2, qr_image.height//2))
        qr_buffer = BytesIO()
        qr_image.save(qr_buffer, format="JPEG")
        qr_buffer.seek(0)
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=qr_buffer)

        timer=45
        while qr.is_displayed() and (timer >= 0):
            time.sleep(1)
            timer-=1

        if timer < 0:
            context.bot.send_message(chat_id=update.effective_chat.id, text="你的二维码已过期（45秒）")
            driver.close()
            return

        context.bot.send_message(chat_id=update.effective_chat.id, text="你已成功登入")
        context.user_data["driver"]=driver
        context.user_data["loggedin"]=True
        time.sleep(2)

    def fetch(update,context):
        if not context.user_data["loggedin"]:
            context.bot.send_message(chat_id=update.effective_chat.id, text="你还没登录")
            return
        driver = context.user_data["driver"]

        def capturechat(driver):
            response = driver.find_elements_by_css_selector("div.chat_item div.avatar i.icon")
            return response
        response=capturechat(driver)

        if response!=[]:
            for sender in response:
                number = int(sender.text)
                sender.click()
                sendername = driver.find_element_by_css_selector("div.title_wrap a.title_name").text
                message_raw = driver.find_elements_by_css_selector("div.message:not(.me) div.content div.plain,img.msg-img,div.voice")

                for i in message_raw[len(message_raw)-number:]:
                    if i.tag_name == "div":
                        if i.get_attribute("class") == "voice":
                            context.bot.send_message(chat_id=update.effective_chat.id, text="{} 给你发送了一条语音".format(sendername))
                        else:
                            context.bot.send_message(chat_id=update.effective_chat.id, text="{} 对你说：\n{}".format(sendername, i.text))
                    elif i.tag_name == "img":
                        context.bot.send_message(chat_id=update.effective_chat.id, text="{} 给你发了一个照片".format(sendername))
                
                ft = [a for a in driver.find_elements_by_css_selector("div.chat_item") if "File Transfer" in a.text][0]
                ft.click()
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="无最新消息")

    def logout(update, context):
        if not context.user_data["loggedin"]:
            context.bot.send_message(chat_id=update.effective_chat.id, text="你还没登录")
            return
        driver = context.user_data["driver"]
        driver.close()
        context.bot.send_message(chat_id=update.effective_chat.id, text="你已登出")

    dispatcher.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ALIVE: [MessageHandler(Filters.regex('^(Login|Fetch|Logout)$'), button)]
        },
        fallbacks=[CommandHandler("start", start)]
    ))
    updater.start_polling()
    print("bot started")
    updater.idle()
    updater.stop()

if __name__=="__main__":
    main()