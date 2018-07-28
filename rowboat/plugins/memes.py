import disco
from disco.bot import Plugin
from disco.bot import CommandLevels
from rowboat.types.plugin import PluginConfig
from rowboat.redis import rdb
from disco.types.user import User as DiscoUser
from disco.types.message import MessageTable, MessageEmbed
from rowboat.types import Field, DictField, ListField, snowflake, SlottedModel, snowflake
from gevent.pool import Pool
from rowboat.util.gevent import wait_many


class MemesConfig(PluginConfig):
    #auto-reply to meesux
    hate_meesux = Field(bool, default=False)
@Plugin.with_config(MemesConfig)
class MemesPlugin(Plugin):
    def load(self, ctx):
        super(MemesPlugin, self).load(ctx)
    
    @Plugin.listen('MessageCreate')
    def meesucks_listener(self, event):
        if event.config.hate_meesux is False:
            return
        if event.message.author.id != 159985870458322944:
            return
        event.message.reply('<@159985870458322944> **NO ONE CARES.**')
        

    @Plugin.listen('MessageCreate')
    def alexa_play_despacito_listener(self, event):
        if "alexa play despacito" in event.message.content and event.author.id == 191793155685744640:
            def g():
                event.message.reply('des')
                gevent.sleep(.5)
                event.message.reply('pa')
                gevent.sleep(.5)
                event.message.reply('cito')
            gevent.spawn(g) 

    @Plugin.command('pong', level=-1)
    def pong(self, event):
        event.message.reply('I pong, you ping. Idiot...')

    # @disco.bot.plugin.BasePluginDeco.listen("MessageCreate")
    # def on_message_create(self, event):
    #     if "alexa play despacito" in event.message.content and event.author.id == 191793155685744640:
    #         def f():
    #             event.message.reply('des')
    #             gevent.sleep(.5)
    #             event.message.reply('pa')
    #             gevent.sleep(.5)
    #             event.message.reply('cito')
    #         gevent.spawn(f)
