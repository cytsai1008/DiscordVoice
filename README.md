# CYTsai's Discord Bots (Old Name: DiscordVoice)  

[![State-of-the-art Shitcode](https://img.shields.io/static/v1?label=State-of-the-art&message=Shitcode&color=7B5804)](https://github.com/trekhleb/state-of-the-art-shitcode)

> **Warning**  
> The [old](/cytsai1008/DiscordVoice/tree/old) and [replit](/cytsai1008/DiscordVoice/tree/replit) branch has deprecated, and [docker](/cytsai1008/DiscordVoice/tree/docker) is work in progress, DO NOT USE.

## What-For-Next-Meal

[Invite Link](https://discord.com/oauth2/authorize?client_id=929275906294448169&permissions=414464724032&scope=bot)

A Discord bot that will help you find what to eat for your next meal.
Supported Meal:
Breakfast, Lunch, Afternoon Tea, Dinner

Command List:

```
nm!help : Show help
nm!ping : Test ping latency
nm!add <meal type> <food name> : Add food
nm!list <meal type (optional)> : Show food list
nm!remove <meal type> <food name> : Remove food
nm!random <meal type (optional)> : Choose random food (Meal type base on time when no meal type specified)
nm!time <Timezone from UTC> : Setup timezone (Number needs to be between ±12 hours)
```

## Be-Your-Mouth

[Invite Link](https://discord.com/oauth2/authorize?client_id=960004225713201172&scope=bot+applications.commands&permissions=139690626112)

A Discord bot plays text messages in voice channel use cloud TTS services.

Current Support TTS Platform: Google, Azure  
Both Azure And Google Supported Language Code:

```
"af-za", "bg-bg", "bn-in", "ca-es", "cs-cz", "da-dk", "de-de", "el-gr", "en-au", 
"en-gb", "en-in", "en-us", "es-es", "es-us", "fi-fi", "fil-ph", "fr-ca", "fr-fr", 
"gu-in", "hi-in", "hu-hu", "id-id", "is-is", "it-it", "ja-jp", "kn-in", "ko-kr", 
"lv-lv", "ml-in", "ms-my", "nb-no", "nl-be", "nl-nl", "pl-pl", "pt-br", "pt-pt", 
"ro-ro", "ru-ru", "sk-sk", "sr-rs", "sv-se", "ta-in", "te-in", "th-th", "tr-tr", 
"uk-ua", "vi-vn", "zh-cn", "zh-tw"
```

Only Google Supported Language Code:
```
"ar-xa", "pa-in", "yue-hk"
```
Only Azure Supported Language Code:

```
"am-et", "ar-ae", "ar-bh", "ar-dz", "ar-eg", "ar-iq", "ar-jo", "ar-kw", "ar-ly", 
"ar-ma", "ar-qa", "ar-sa", "ar-sy", "ar-tn", "ar-ye", "bn-bd", "cy-gb", "de-at", 
"de-ch", "en-ca", "en-hk", "en-ie", "en-ke", "en-ng", "en-nz", "en-ph", "en-sg", 
"en-tz", "en-za", "es-ar", "es-bo", "es-cl", "es-co", "es-cr", "es-cu", "es-do", 
"es-ec", "es-gq", "es-gt", "es-hn", "es-mx", "es-ni", "es-pa", "es-pe", "es-pr", 
"es-py", "es-sv", "es-uy", "es-ve", "et-ee", "fa-ir", "fr-be", "fr-ch", "ga-ie", 
"gl-es", "he-il", "hr-hr", "jv-id", "kk-kz", "km-kh", "lo-la", "lt-lt", "mk-mk", 
"mr-in", "mt-mt", "my-mm", "ps-af", "si-lk", "sl-si", "so-so", "su-id", "sw-ke", 
"sw-tz", "ta-lk", "ta-sg", "ur-in", "ur-pk", "uz-uz", "zh-hk", "zu-za"
```

Command List:
```
$help : Show help
$setchannel <#channel> : Set channel to receive text message to be played at voice channel.
$setlang <language code> : Set language to be speak. (please follow BCP-47 standard)
$setvoice <"Azure", "Google", "Reset"> : Set default TTS platform (support user setting (use DM) or server wide setting)
$say <messages> : Speak text message.
$say_lang <language code> <messages> : Speak text message in specified language.
$stop : Stop speaking.
$join <voice channel (optional)> : Join voice channel.
$move <voice channel (optional)> : Move to another voice channel.
$leave : Leave voice channel.
$ping : Test ping latency.
$invite : Get a link to invite this bot into your server.
```

## Todo (Contribute Welcome)
### WFNM
 - [ ] Code rewrite
### BYM
 - [ ] Queue
 - [ ] Auto disconnect
 - [x] Translate
 - [ ] Rewrite some codeblocks into function
 - [x] Update to `py-cord` 2.0 or (`nextcord/nextcord` for more stable 2.0?)
 - [ ] Command typo auto fix (ex. `$sayABCD` -> `$say ABCD`)
 - [ ] Slash command
 - [ ] Embed message
 - [ ] No command prefix mode
