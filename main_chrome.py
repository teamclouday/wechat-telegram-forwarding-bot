import time
import json
from selenium import webdriver
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, Updater, Filters

import requests
from PIL import Image
from io import BytesIO

# edit this to change fetch interval
FETCH_INTERVAL = 20

# edit this to change qrcode timer limit
QRCODE_TIMER = 45

# setup
USER_CUSTOM_SETUP = {
    "block_voice": False,
    "block_image": False,
    "block_video": False,
    "block_group": False
}

def main():
    with open("config.txt", "r") as f:
        word=f.readlines()
        allowed_user="@"+str(word[1].strip())
        token=str(word[0].strip())

    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    def login(update, context):
        if ("loggedin" in context.user_data.keys()) and context.user_data["loggedin"]:
            context.bot.send_message(chat_id=update.effective_chat.id, text="你已经登录，输入/logout来登出")
            return
        context.bot.send_message(chat_id=update.effective_chat.id, text="正在初始化。。。")

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        driver.get("https://wx.qq.com/?lang=en_US")

        qr = driver.find_element_by_css_selector("div.qrcode img.img")
        qr_image = Image.open(BytesIO(requests.get(qr.get_attribute("src")).content))
        qr_image = qr_image.resize((qr_image.width//2, qr_image.height//2))
        qr_buffer = BytesIO()
        qr_image.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=qr_buffer)

        timer=QRCODE_TIMER
        timer_test = driver.find_elements_by_css_selector("div.chat_item div.avatar")
        while (timer >= 0) and ((timer_test == []) or (not timer_test[0].is_displayed())):
            timer_test = driver.find_elements_by_css_selector("div.chat_item div.avatar")
            time.sleep(1)
            timer-=1

        if timer < 0:
            context.bot.send_message(chat_id=update.effective_chat.id, text="你的二维码已过期（45秒）")
            driver.close()
            return

        context.bot.send_message(chat_id=update.effective_chat.id, text="你已成功登录")
        context.user_data["driver"]=driver
        context.user_data["loggedin"]=True
        if "custom_setup" not in context.user_data.keys():
            context.user_data["custom_setup"] = USER_CUSTOM_SETUP
        context.user_data["chatid"] = update.effective_chat.id
        context.job_queue.run_repeating(fetch, FETCH_INTERVAL, context=context.user_data)

    def fetch(context):
        driver = context.job.context["driver"]

        def capturechat(driver):
            response = driver.find_elements_by_css_selector("div.chat_item div.avatar i.icon")
            return response
        response=capturechat(driver)

        if response!=[]:
            for sender in response:
                if sender.text == "":
                    if context.job.context["custom_setup"]["block_group"]: continue
                    sender.click()
                    sendername = driver.find_element_by_css_selector("div.title_wrap a.title_name").text
                    context.bot.send_message(chat_id=context.job.context["chatid"], text="群“{}”有新消息".format(sendername))
                    continue
                number = int(sender.text)
                sender.click()
                sendername = driver.find_element_by_css_selector("div.title_wrap a.title_name").text
                message_raw = driver.find_elements_by_css_selector("div.message:not(.me) div.content div.plain,div.picture,div.voice,div.video")

                sender_crypt = driver.find_element_by_css_selector("div.message img.avatar").get_attribute("mm-src")
                sender_crypt = sender_crypt[sender_crypt.find("crypt_")+6:]

                for i in message_raw[len(message_raw)-number:]:
                    real_sendername = i.find_element_by_xpath("../../..").find_elements_by_tag_name("h4")
                    real_sendername = real_sendername[0].text if len(real_sendername) > 0 else sendername
                    i_class = i.get_attribute("class")
                    if i_class == "plain":
                        if real_sendername == sendername:
                            context.bot.send_message(chat_id=context.job.context["chatid"], text="“{}”对你说：\n{}".format(sendername, i.text))
                        else:
                            context.bot.send_message(chat_id=context.job.context["chatid"], text="群“{}”的“{}”说：\n{}".format(sendername, real_sendername, i.text))
                    elif i_class == "picture":
                        if context.job.context["custom_setup"]["block_image"]: continue
                        img = i.find_element_by_css_selector("img.msg-img")
                        img = Image.open(BytesIO(img.screenshot_as_png))
                        img = img.resize((img.width*2, img.height*2))
                        img_buffer = BytesIO()
                        img.save(img_buffer, format="PNG")
                        img_buffer.seek(0)
                        if real_sendername == sendername:
                            context.bot.send_message(chat_id=context.job.context["chatid"], text="“{}”给你发了一张图片".format(sendername))
                        else:
                            context.bot.send_message(chat_id=context.job.context["chatid"], text="群“{}”的“{}”发了一张图片".format(sendername, real_sendername))
                        context.bot.send_photo(chat_id=context.job.context["chatid"], photo=img_buffer)
                    elif i_class == "voice":
                        if context.job.context["custom_setup"]["block_voice"]: continue
                        voice_msg_id = json.loads(i.find_element_by_xpath("../..").get_attribute("data-cm"))["msgId"]
                        voice_url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetvoice?msgid=" + voice_msg_id + "&skey=@crypt_" + sender_crypt
                        cookies = {}
                        for c in driver.get_cookies():
                            cookies[c["name"]] = c["value"]
                        r = requests.get(voice_url, cookies=cookies, stream=True)
                        voice_buffer = BytesIO()
                        for chunk in r.iter_content(chunk_size=512):
                            if chunk: voice_buffer.write(chunk)
                        voice_buffer.seek(0)
                        if real_sendername == sendername:
                            context.bot.send_message(chat_id=context.job.context["chatid"], text="“{}”给你发送了一条语音".format(sendername))
                        else:
                            context.bot.send_message(chat_id=context.job.context["chatid"], text="群“{}”的“{}”发送了一条语音".format(sendername, real_sendername))
                        context.bot.send_voice(chat_id=context.job.context["chatid"], voice=voice_buffer)
                    elif i_class == "video":
                        if context.job.context["custom_setup"]["block_video"]: continue
                        video_msg_id = json.loads(i.find_element_by_xpath("../..").get_attribute("data-cm"))["msgId"]
                        video_url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetvideo?msgid=" + video_msg_id + "&skey=%2540crypt_" + sender_crypt
                        cookies = {}
                        for c in driver.get_cookies():
                            cookies[c["name"]] = c["value"]
                        headers = {
                            "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36",
                            "Referer": "https://wx.qq.com/?lang=en_US",
                            "Accept-Encoding": "identity;q=1, *;q=0",
                            "Range": "bytes=0-"
                        }
                        r = requests.get(video_url, cookies=cookies, stream=True, headers=headers)
                        video_buffer = BytesIO()
                        for chunk in r.iter_content(chunk_size=1024):
                            if chunk: video_buffer.write(chunk)
                        video_buffer.seek(0)
                        if real_sendername == sendername:
                            context.bot.send_message(chat_id=context.job.context["chatid"], text="“{}”给你发送了一段视频".format(sendername))
                        else:
                            context.bot.send_message(chat_id=context.job.context["chatid"], text="群“{}”的“{}”发送了一段视频".format(sendername))
                        context.bot.send_video(chat_id=context.job.context["chatid"], video=video_buffer)
 
                ft = [a for a in driver.find_elements_by_css_selector("div.chat_item") if "File Transfer" in a.text][0]
                ft.click()

    def logout(update, context):
        if ("loggedin" not in context.user_data.keys()) or (not context.user_data["loggedin"]):
            context.bot.send_message(chat_id=update.effective_chat.id, text="你还没登录，输入/login来登录")
            return
        context.job_queue.stop()
        driver = context.user_data["driver"]
        driver.close()
        context.bot.send_message(chat_id=update.effective_chat.id, text="你已登出")
        context.user_data["loggedin"] = False

    def echo(update, context):
        update.message.reply_text(update.message.text)

    B_VOICE, B_IMAGE, B_VIDEO, B_GROUP = range(4)

    def setup_start(update, context):
        if "custom_setup" not in context.user_data.keys():
            context.user_data["custom_setup"] = USER_CUSTOM_SETUP
        context.bot.send_message(chat_id=update.effective_chat.id, text="开始配置自定义屏蔽选项\n请选择是/否")
        reply_keyboard = [["是", "否"]]
        update.message.reply_text("是否屏蔽语音信息？", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return B_VOICE
    def setup_voice(update, context):
        context.user_data["custom_setup"]["block_voice"] = True if update.message.text == "是" else False
        reply_keyboard = [["是", "否"]]
        update.message.reply_text("是否屏蔽图片信息？", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return B_IMAGE
    def setup_image(update, context):
        context.user_data["custom_setup"]["block_image"] = True if update.message.text == "是" else False
        reply_keyboard = [["是", "否"]]
        update.message.reply_text("是否屏蔽视频信息？", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return B_VIDEO
    def setup_video(update, context):
        context.user_data["custom_setup"]["block_video"] = True if update.message.text == "是" else False
        reply_keyboard = [["是", "否"]]
        update.message.reply_text("是否屏蔽消息免打扰的群信息？", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return B_GROUP
    def setup_group(update, context):
        context.user_data["custom_setup"]["block_group"] = True if update.message.text == "是" else False
        update.message.reply_text("自定义配置成功", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    def setup_end(update, context):
        update.message.reply_text("自定义配置失败，输入/setup重试", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    dispatcher.add_handler(CommandHandler("login", login, pass_job_queue=True, filters=Filters.user(username=allowed_user)))
    dispatcher.add_handler(CommandHandler("logout", logout, pass_job_queue=True, filters=Filters.user(username=allowed_user)))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command & ~Filters.regex("^(是|否)$"), echo))
    dispatcher.add_handler(ConversationHandler(
        entry_points=[CommandHandler("setup", setup_start, filters=Filters.user(username=allowed_user))],
        states={
            B_VOICE: [MessageHandler(Filters.regex("^(是|否)$"), setup_voice)],
            B_IMAGE: [MessageHandler(Filters.regex("^(是|否)$"), setup_image)],
            B_VIDEO: [MessageHandler(Filters.regex("^(是|否)$"), setup_video)],
            B_GROUP: [MessageHandler(Filters.regex("^(是|否)$"), setup_group)],
        },
        fallbacks=[CommandHandler("cancel", setup_end, filters=Filters.user(username=allowed_user))]
    ))
    updater.start_polling()
    print("bot started")
    updater.idle()
    updater.stop()

if __name__=="__main__":
    main()