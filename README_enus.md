# wechat-telegram-forwarding-bot

<a href="README.md">中文版本Readme</a>
## Deploy
1. Forst you need a Telegram Bot https://core.telegram.org/bots and its token api
2. The running machine network can access both Telegram and Wechat(Which filters maybe a lot)
3. Install dependencies, `sh apt.sh`
4. Create config.txt, with token as first line，second line as Telegram username without @
For example:
```
186256385:hjibbhiuhgYGYUgvFFTY
botfather
```
5. Run `python3 main.py`
6. Start Bot, Use login and /logout to login ot logout

Run as following, fetch and push every 10s   
<img src="assets/demo.gif"  width="200"/>  

## Known Issues
1. Gecko version may interrupt due in unstable network
2. Gecko is tested on Ubuntu 20.04, Chrome is tested on Arch, we have no plan supporting this program on Windows or MacOS

## Things Special
Cowork by @Nagato and @Sida, special thanks to Sida supporting Fetch function and Chrome support（Chrome version has a much better user experience than Gecko version which is done by Sida）

## Disclaimer
Under GPL v3, this program is based on Web wechat and provided "AS IS"