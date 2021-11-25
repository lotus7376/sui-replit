#ライブラリのインポート
import time
import subprocess
import asyncio
import os
import re

import discord
from discord.ext import commands
import ffmpeg

from voicegenerate import create_MP3
from server import keep_alive

# アクセストークン、プレフィックス、グローバル変数の設定
TOKEN = os.getenv("TOKEN")
ADMIN = int(os.getenv("ADMIN"))
PREFIX = "."
global read_ID
read_ID = []
GREEN = discord.Colour.from_rgb(0, 215, 125)
RED = discord.Colour.from_rgb(225, 80, 80)


class SuiBot(commands.Bot):
    async def on_ready(self):

        # 起動時にターミナルに現在時刻とログイン通知を表示
        print("--------------------")
        print("起動しました")

        # プレイ中のゲームを表示 (.help)
        await bot.change_presence(activity=discord.Game(name=PREFIX + "help"))


class Help(commands.HelpCommand):
    def __init__(self):
        super().__init__()
        self.no_category = "その他"
        self.command_attrs["description"] = "コマンドリストを表示しますぃ"

    async def send_bot_help(self, mapping):
        # ヘルプコマンドの処理を変更する

        embed = discord.Embed(title="コマンドリスト", color=GREEN)
        for cog in mapping:
            field = ""
            # コマンドリストを取得
            command_list = await self.filter_commands(mapping[cog])
            if not command_list:
                # 表示できるコマンドがないとき、他のコグの処理に移る
                continue
            if cog is None:
                # コグが未設定のコマンドの場合、no_category属性を参照
                name = self.no_category
                if self.context.author.id != ADMIN and name == "管理者専用":
                    # 管理者でない場合は管理者コマンドを表示しない
                    continue
            else:
                name = cog.qualified_name
            for command in command_list:
                field += f"{command.name} / {command.description}\n"
            embed.add_field(name=name, value=field, inline=False)

        await self.get_destination().send(embed=embed)

    def command_not_found(self, string):

        # コマンドが見つからなかったときのメッセージ
        return f"{string}というコマンドはないですぃ"


class VoiceCog(commands.Cog, name="参加・退出"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["c", "connect"], description="ボイスチャンネルに接続しますぃ")
    async def sui(self, ctx):

        print("----------")

        title = "エラー"
        item = ""
        color = RED
        if ctx.message.guild:
            # 送信者がボイスチャンネルに接続していない場合は無視
            if ctx.author.voice is None:
                print("エラー：送信者がボイスチャンネルに接続していません")

                item = "あなたはボイスチャンネルに接続してないですぃ"
            else:
                if ctx.guild.voice_client:
                    # 既に送信者と同じボイスチャンネルに接続している場合は無視
                    if ctx.author.voice.channel == ctx.guild.voice_client.channel:
                        print("エラー：既に同じボイスチャンネルに接続しています")

                        item = "もう接続済みですぃ"
                    else:
                        print("エラー：別のボイスチャンネルに接続中です")

                        item = "別のボイスチャンネルに接続中ですぃ"
                else:
                    # 送信者がボイスチャンネルに接続していた場合、そのボイスチャンネルに接続する
                    await ctx.author.voice.channel.connect()
                    # 接続するボイスチャンネル名、読み上げるテキストチャンネル名を取得
                    connectch = ctx.author.voice.channel.name
                    readch = ctx.channel.name
                    read_ID.append(ctx.channel.id)

                    print("読み上げ開始")
                    print("読み上げ中のチャンネル")
                    print(read_ID)

                    title = "読み上げ開始"
                    item = "接続したチャンネル:" + connectch
                    item += "\n"
                    item += "読み上げるチャンネル:" + readch
                    color = GREEN

        # 埋め込みの作成
        embed = discord.Embed(title=title, description=item, color=color)
        await ctx.send(embed=embed)

    @commands.command(aliases=["dc", "disconnect"],
                      description="ボイスチャンネルからばいばいしますぃ")
    async def desui(self, ctx):

        print("----------")
        title = "エラー"
        item = ""
        color = RED

        if ctx.message.guild:
            # ボイスチャンネルに接続していない場合は無視
            if ctx.channel.id in read_ID:
                if ctx.guild.voice_client is None:
                    print("エラー：ボイスチャンネルに接続していません")

                    item = "ボイスチャンネルに接続してないですぃ"
                else:
                    #ボイスチャンネルから切断する
                    print("読み上げ終了")
                    print("読み上げ中のチャンネル")
                    print(read_ID)
                    print("--------------------")

                    read_ID.remove(ctx.channel.id)
                    await ctx.guild.voice_client.disconnect()

                    title = "読み上げ終了"
                    item = "ばいばいですぃ"
                    color = GREEN
            else:
                print("エラー：読み上げているチャンネル以外で切断コマンドが実行されました")

                item = "読み上げているチャンネル以外ではばいばいできないですぃ"

        # 埋め込みの作成
        embed = discord.Embed(title=title, description=item, color=color)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):

        # 読み上げるチャンネルのメッセージを取得し、再生する
        if message.content.startswith(PREFIX):
            pass  # コマンドプレフィックスから始まる場合無視
        elif message.author.bot:
            pass  # 送信者がbotの場合無視
        elif message.guild.voice_client:
            if message.channel.id in read_ID:
                print("----------")
                print(message.content)

                global channelname
                channelname = ""
                # チャンネルメンションが含まれていた場合、idから名前を取得する
                if message.channel_mentions:
                    id = message.raw_channel_mentions
                    for i in id:
                        channel = message.guild.get_channel(i)
                        channelname += "," + channel.name

                global name
                name = ""
                # メンションが含まれていた場合、idから名前を取得する
                if message.mentions:
                    id = message.raw_mentions
                    for i in id:
                        user = await message.guild.fetch_member(i)
                        name += "," + user.name

                global rolelname
                rolename = ""
                # ロールメンションが含まれていた場合、idからロール名を取得する
                if message.role_mentions:
                    id = message.raw_role_mentions
                    for i in id:
                        role = message.guild.get_role(i)
                        rolename += "," + role.name

                # 再生する音声の生成
                mp3url = create_MP3(message.content, name, channelname,
                                    rolename)
                source = discord.FFmpegOpusAudio(mp3url)

                # 音声が再生中の場合再生が終わるまで停止
                while message.guild.voice_client.is_playing():
                    time.sleep(1)

                # 音声の再生
                message.guild.voice_client.play(source)
            else:
                pass
        else:
            pass


class dictionaryCog(commands.Cog, name="辞書"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["aw"], description="辞書に単語を登録しますぃ")
    async def addword(self, ctx, arg1, arg2):

        print("----------")
        print("辞書に単語を追加：" + arg1 + ',' + arg2)
        title = "エラー"
        item = ""
        color = RED

        # ファイルを開く
        f = open("/home/runner/sui/user_dic.txt", mode='a+')

        # 既に追加済みの場合追加しない
        for line in f:
            if arg1 in line:
                print("エラー：「" + line + "」が辞書に存在します")
                item = "「{arg1}」は既に追加済みですぃ"
                f.close()
                break

        # ファイルに書き込み
        f.write(arg1 + ',' + arg2 + '\n')

        title = "辞書に単語を追加"
        item = "追加する単語"
        item += arg1
        item += "\n"
        item += "読み方"
        item += arg2
        color = GREEN

        # 埋め込みの作成
        embed = discord.Embed(title=title, description=item, color=color)
        await ctx.send(embed=embed)

    @commands.command(aliases=["dw"], description="辞書から単語を削除しますぃ")
    async def deleteword(self, ctx, arg):

        print("----------")
        print("削除する単語：" + arg)
        title = "エラー"
        item = ""
        color = RED

        # 削除する単語以外を新しいファイルにコピー
        with open('/home/runner/sui/user_dic.txt', mode='r') as oldfile:
            with open('/home/runner/sui/temp.txt', mode='w') as newfile:

                line = oldfile.readline()

                while line:
                    pattern = line.strip().split(',')
                    print(pattern)
                    if pattern[0] in arg:
                        line = oldfile.readline()
                    else:
                        newfile.write(line)
                        line = oldfile.readline()

        with open('/home/runner/sui/user_dic.txt', mode='r') as oldfile:
            with open('/home/runner/sui/temp.txt', mode='r') as newfile:

                # 単語が削除されていない場合、単語が登録されていない
                if oldfile.readlines() == newfile.readlines():
                    print("エラー：" + arg + "が辞書に存在しません")
                    item = "「{arg}」が追加されてないですぃ"
                else:
                    title = "辞書から単語を削除"
                    item = "削除する単語:{arg}"
                    color = GREEN

        # 埋め込みの作成
        embed = discord.Embed(title=title, description=item, color=color)
        await ctx.send(embed=embed)

        # 古いファイルを削除し、新しいファイルをリネーム
        os.remove('/home/runner/sui/user_dic.txt')
        os.rename('/home/runner/sui/temp.txt', '/home/runner/sui/user_dic.txt')

    @commands.command(description="登録されている単語を表示しますぃ")
    async def wordlist(self, ctx):

        print("----------")
        print("登録されている単語を表示")

        with open('/home/runner/sui/user_dic.txt', mode='r') as f:
            list = f.read()

            print(list)

            embed = discord.Embed(title="登録されている単語一覧",
                                  description=list,
                                  color=GREEN)

            await ctx.send(embed=embed)


class secletCog(commands.Cog, name = "管理者専用"):
    suiflg = True

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):

        # メッセージに「すい」または「すぃ」が含まれていた場合、特定の動作を行う
        if message.content.startswith(PREFIX):
            pass  # コマンドプレフィックスから始まる場合無視
        elif message.author.bot:
            pass  # 送信者がbotの場合無視
        elif "すい" in message.content or "すぃ" in message.content or "sui" in message.content:
            file = discord.File('/home/runner/sui/sui.png', filename='sui.png')
            await message.reply(file=file)
            print("----------")
            print("sent sui to ")
            print(message.author.id)

    @commands.command(description = "リプライ機能のオンオフを切り替えますぃ")
    async def change(self, ctx):
        # 機能のオンオフを切り替える

        if ctx.author.id == ADMIN: # 管理者のみが使用可能
            if secletCog.suiflg:
                secletCog.suiflg = False
                title = "Invalidation"
                item = "無効化しました"
                color = GREEN
                embed = discord.Embed(title = title, description = item, color = color)
                await ctx.send(embed = embed)

            else:
                secletCog.suiflg = True
                title = "Activtion"
                item = "有効化しました"
                color = GREEN
                embed = discord.Embed(title = title, description = item, color = color)
                await ctx.send(embed = embed)

            print("suiflg change to ")
            print(secletCog.suiflg)

    @commands.command(description = "リプライ機能の状態を表示しますぃ")
    async def status(self, ctx):
        # 機能の状況を返す

        title = "Status"
        if ctx.author.id == ADMIN: # 管理者のみが使用可能
            if secletCog.suiflg:
                item = "有効です"
                color = GREEN
                embed = discord.Embed(title = title, description = item, color = color)
                await ctx.send(embed = embed)
            else:
                item = "無効です"
                color = GREEN
                embed = discord.Embed(title = title, description = item, color = color)
                await ctx.send(embed = embed)

            print("suiflg = ")
            print(secletCog.suiflg)

# Webサーバーの起動
keep_alive()

# 接続に必要なオブジェクトの生成
if __name__ == '__main__':
    bot = SuiBot(command_prefix=PREFIX,
                 help_command=Help(),
                 description="読み上げますぃ")

    # コグの追加
    bot.add_cog(VoiceCog(bot))
    bot.add_cog(dictionaryCog(bot))
    bot.add_cog(secletCog(bot))

    # botの起動とdiscordサーバーへの接続
    bot.run(TOKEN)
