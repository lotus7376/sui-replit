import subprocess
import re
import urllib.parse
from gtts import gTTS


# 絵文字は読み上げない
def remove_custom_emoji(text):
    pattern = r"<:[a-zA-Z0-9_]+:[0-9]+>"  # カスタム絵文字のパターン
    return re.sub(pattern, "絵文字", text)  # 置換処理


# URLを省略
def urlAbb(text):
    pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
    return re.sub(pattern, "URL省略ですぃ", text)  # 置換処理


# メンションのIDを名前に変換
def mention_name(text, name, channel, role):
    # ユーザーメンションの置換
    name = name.split(',')
    name.remove('')
    namepattern = r"<[@!]*[0-9]+>"
    for i in name:
        text = re.sub(namepattern, "@" + i, text, 1)

    # チャンネルメンションの置換
    channel = channel.split(',')
    channel.remove('')
    chpattern = r"<#[0-9]+>"
    for i in channel:
        text = re.sub(chpattern, i, text, 1)

    # ロールメンションの置換
    role = role.split(',')
    role.remove('')
    rolepattern = r"<@&[0-9]+>"
    for i in role:
        text = re.sub(rolepattern, "@" + i, text, 1)

    return text


# 登録した文字の読み替え
def user_dic(text):

    # ファイル指定
    f = open('/home/runner/sui-replit/user_dic.txt', 'r')
    line = f.readline()

    while line:
        pattern = line.strip().split(',')
        # textが一致していた場合置き換える
        if pattern[0] in text:
            text = text.replace(pattern[0], pattern[1])
            break
        else:
            line = f.readline()

    f.close()

    return text


def len_cut(text):

    # 文字数が100文字を超える場合省略する
    if len(text) < 100:
        return text
    else:
        return text[:96] + "以下略"


# message.contentを.txtに書き込む
def create_MP3(inputText, name, channel, role):

    # メンションはIDを名前に置換する
    inputText = mention_name(inputText, name, channel, role)
    # 絵文字IDは読み上げない
    inputText = remove_custom_emoji(inputText)
    # URLは省略
    inputText = urlAbb(inputText)
    # ユーザ辞書に登録されていることばの場合は置換する
    inputText = user_dic(inputText)
    # 100文字を超える場合省略
    inputText = len_cut(inputText)

    print("置換後のtext：" + inputText)

    #s_quote = urllib.parse.quote(inputText)
    #mp3url = f'http://translate.google.com/translate_tts?ie=UTF-8&q={s_quote}&tl=ja&client=tw-ob'
    tts = gTTS(inputText, lang='ja')
    tts.save("voice.mp3")
    return
