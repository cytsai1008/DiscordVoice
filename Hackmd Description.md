---
- title: 透過 Python 製作 Discord 機器人
- description: 這是cytsai1008/DiscordVoice用於學習歷程的文件
---

{%hackmd BJrTq20hE %}

# 透過 Python 製作 Discord 機器人  

<a href="https://github.com/cytsai1008/DiscordVoice" target="_blank">
  <img src="https://opengraph.githubassets.com/536867101165/cytsai1008/DiscordVoice" alt="GitHub Open Graph Image" style="border-radius: 0.5rem; max-width: 350px">
</a>
<a href="https://github.com/cytsai1008/What-For-Next-Meal" target="_blank">
  <img src="https://opengraph.githubassets.com/536867101165/cytsai1008/What-For-Next-Meal" alt="GitHub Open Graph Image" style="border-radius: 0.5rem; max-width: 350px;opacity:0.55;filter:grayscale(70%)">
</a>

**P.S. [What-For-Next-Meal](https://github.com/cytsai1008/What-For-Next-Meal) 為節省Heroku的運作時數已整合進 [DiscordVoice](https://github.com/cytsai1008/DiscordVoice) 中，且原Repo已封存，部分於 [What-For-Next-Meal](https://github.com/cytsai1008/What-For-Next-Meal) 之內容並非最新，還請以 [DiscordVoice](https://github.com/cytsai1008/DiscordVoice) 中`wfnm`前綴之檔名為主**  

## What-For-Next-Meal

## DiscordVoice

### 動機  

與朋友在 Discord 進行語音聊天時常常會遇到不方便開 Mic 的情況，但有時遊戲中無法第一時間切到文字頻道看他們說了甚麼內容。  
因此想做一台機器人能在語音說出內容，以方便能讓語音中的人都能快速了解到現在情形。

### 方法  

#### 語言：Python  
>(嚴格來說JavaScript與官方API擁有最好的支援度但我能力有限，也許之後有機會能重寫成JavaScript)  

#### 主要用到的套件包：

1. [py-cord](https://github.com/Pycord-Development/pycord)

> 此為[discord.py](https://github.com/Rapptz/discord.py)的其中一個分支，由於開發者與Discord官方的內部問題因此在我接觸時Repo是被封存的狀態  
> 現在雖然已經回復正常但仍有許多API不支援  

2. [google-cloud-texttospeech](https://github.com/googleapis/python-texttospeech)

> 最初選擇使用[Google Cloud Platform](https://cloud.google.com/)的[Cloud Text-to-Speech API](https://cloud.google.com/text-to-speech/)作為TTS引擎的提供者  

3. [azure-cognitiveservices-speech](https://pypi.org/project/azure-cognitiveservices-speech/)

> 原本其實是突發奇想想到既然GCP能用，那為何不也用[Azure](https://azure.microsoft.com)的[Cognitives Services/Text to Speech API](https://azure.microsoft.com/en-us/services/cognitive-services/text-to-speech)做為另一種聲音的來源。

4. [redis-py](https://github.com/redis/redis-py)

> 在轉移至heroku時受到朋友推薦的資料庫軟體，由於heroku無法儲存在dyno中的檔案，因此必須將資料儲存在外部資料提供者。  
> 我選擇使用[RedisLabs](https://www.redis.com)

5. [flask](https://github.com/pallets/flask/)

> Lorem lpsium

6. [mechanize](https://github.com/python-mechanize/mechanize)

> Lorem lpsium

完整套件包資料：[requirements.txt](https://github.com/cytsai1008/DiscordVoice/blob/main/requirements.txt)

#### 架設到免費伺服器  

1. replit  

2. heroku  

### 未完成功能  

## 心得  

~~我快爆肝了~~  