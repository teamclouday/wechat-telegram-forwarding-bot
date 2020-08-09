from selenium import webdriver
import time
from telegram.ext import CommandHandler, Updater, Filters
from selenium.webdriver.firefox.options import Options
from PIL import Image
import requests
from io import BytesIO
import os


def main():
    f = open("token.txt", "r")
    token=f.read()
    print(token)
    f.close()

    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    def login(update, context):
        if ("loggedin" in context.user_data.keys()) and context.user_data["loggedin"]:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Logged in already")
            return
        context.bot.send_message(chat_id=update.effective_chat.id, text="Fetching wechat login info")

        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Firefox(options=options)
        driver.get("https://wx.qq.com/?lang=en_US")

        qr = driver.find_element_by_css_selector("div.qrcode img.img")
        qr_image = Image.open(BytesIO(requests.get(qr.get_attribute("src")).content))
        qr_image = qr_image.resize((qr_image.width//2, qr_image.height//2))
        qr_buffer = BytesIO()
        qr_image.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=qr_buffer)

        timer=45
        timer_test = driver.find_elements_by_css_selector("div.chat_item div.avatar")
        while (timer >= 0) and ((timer_test == []) or (not timer_test[0].is_displayed())):
            timer_test = driver.find_elements_by_css_selector("div.chat_item div.avatar")
            time.sleep(1)
            timer-=1

        if timer < 0:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Your login expired")
            driver.close()
            return

        context.bot.send_message(chat_id=update.effective_chat.id, text="Connected, loading...")
        time.sleep(2)
        context.bot.send_message(chat_id=update.effective_chat.id, text="You have logged in")

        context.user_data["driver"]=driver
        context.user_data["loggedin"] = True
        context.user_data["chatid"] = update.effective_chat.id
        context.job_queue.run_repeating(fetch, 10, context=context.user_data)

    def fetch(context):
        driver = context.job.context["driver"]

        def capturechat(driver):
            response = driver.find_elements_by_css_selector("div.chat_item div.avatar i.icon")
            return response
        response=capturechat(driver)

        if response!=[]:
            for sender in response:
                if sender.text =="":
                    continue
                number = int(sender.text)
                sender.click()
                sendername = driver.find_element_by_css_selector("div.title_wrap a.title_name").text
                message_raw = driver.find_elements_by_css_selector("div.message:not(.me) div.content div.plain,img.msg-img,div.voice")

                for i in message_raw[len(message_raw)-number:]:
                    if i.tag_name == "div":
                        if i.get_attribute("class") == "voice":
                            context.bot.send_message(chat_id=context.job.context["chatid"], text="{} sent you a voice message".format(sendername))
                        else:
                            context.bot.send_message(chat_id=context.job.context["chatid"], text="{} sent you a message: {}".format(sendername, i.text))
                    elif i.tag_name == "img":
                        img = Image.open(BytesIO(i.screenshot_as_png))
                        img = img.resize((img.width*2, img.height*2))
                        img_buffer = BytesIO()
                        img.save(img_buffer, format="PNG")
                        img_buffer.seek(0)
                        context.bot.send_message(chat_id=context.job.context["chatid"], text="{} sent a picture".format(sendername))
                        context.bot.send_photo(chat_id=context.job.context["chatid"], photo=img_buffer)

            ft = [a for a in driver.find_elements_by_css_selector("div.chat_item") if "File Transfer" in a.text][0]
            ft.click()

    def logout(update, context):
        if ("loggedin" not in context.user_data.keys()) or (not context.user_data["loggedin"]):
            context.bot.send_message(chat_id=update.effective_chat.id, text="You have not logged in")
            return
        context.job_queue.stop()
        driver = context.user_data["driver"]
        driver.close() 
        print("Service stop")
        context.bot.send_message(chat_id=update.effective_chat.id, text="You have logged out")

    dispatcher.add_handler(CommandHandler("login", login, pass_job_queue=True))
    dispatcher.add_handler(CommandHandler("logout", logout, pass_job_queue=True))

    updater.start_polling()
    updater.idle()
    updater.stop()

if __name__=="__main__":
    main()