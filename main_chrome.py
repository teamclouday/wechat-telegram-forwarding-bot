import time
from selenium import webdriver
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, Updater, Filters
from telegram import KeyboardButton, ReplyKeyboardMarkup

ALIVE = 0

def main():
    with open("token.txt", "r") as f:
        token=f.read()

    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    def start(update, context):
        context.user_data["loggedin"] = False
        keyboard = [[KeyboardButton("登入"),
            KeyboardButton("刷新消息"),
            KeyboardButton("登出")]]
        reply_markup = ReplyKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=update.message.chat_id, text="bot已启动", reply_markup=reply_markup)
        return ALIVE

    def button(update, context):
        if update.message.text == "登入":
            login(update, context)
        elif update.message.text == "刷新消息":
            fetch(update, context)
        elif update.message.text == "登出":
            logout(update, context)
        return ALIVE

    def login(update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="正在初始化。。。")

        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        driver.get("https://wx.qq.com/?lang=en_US")

        qr = driver.find_element_by_css_selector("div.qrcode  img.img").get_attribute("src")
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=qr)

        timer=45
        while (driver.find_elements_by_css_selector("div.qrcode img.img") != []) and timer>=0:
            time.sleep(1)
            timer-=1
            print(timer)

        if timer < 0:
            context.bot.send_message(chat_id=update.effective_chat.id, text="你的二维码已过期")
            driver.close()
            return

        context.bot.send_message(chat_id=update.effective_chat.id, text="你已成功登入")
        context.user_data["driver"]=driver
        context.user_data["loggedin"]=True

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

                #print(sendername, number)
                message = []
                for i in message_raw:
                    if i.tag_name == "div":
                        if i.get_attribute("class") == "voice": message.append("你受到一条语音")
                        else: message.append(i.text)
                    elif i.tag_name == "img": message.append("你受到一个图片")
                bot_message = "{} 向你发送了{}条消息：\n{}".format(sendername, number, "\n".join(message[len(message)-number:]))
                context.bot.send_message(chat_id=update.effective_chat.id, text=bot_message)
                #print(message[len(message)-number:])

                ft = [a for a in driver.find_elements_by_css_selector("div.chat_item") if "File Transfer" in a.text][0]
                ft.click()

    def logout(update, context):
        if not context.user_data["loggedin"]:
            context.bot.send_message(chat_id=update.effective_chat.id, text="你还没登录")
            return
        driver = context.user_data["driver"]
        driver.close() 
        print("Service stop")
        context.bot.send_message(chat_id=update.effective_chat.id, text="你已登出")

    dispatcher.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ALIVE: [MessageHandler(Filters.regex('^(登入|刷新消息|登出)$'), button)]
        },
        fallbacks=[CommandHandler("start", start)]
    ))
    updater.start_polling()
    updater.idle()
    updater.stop()

if __name__=="__main__":
    main()