from disco.bot import Plugin
import disco
from disco.bot import CommandLevels
from rowboat.types.plugin import PluginConfig
from rowboat.redis import rdb
from disco.types.user import User as DiscoUser
from disco.types.message import MessageTable, MessageEmbed
from rowboat.types import Field, DictField, ListField, snowflake, SlottedModel, snowflake


class MemesConfig(PluginConfig):
    #auto-reply to meesux
    hate_meesux = Field(bool, default=False)
@Plugin.with_config(MemesConfig)
class MemesPlugin(Plugin):
    def load(self, ctx):
        super(MemesPlugin, self).load(ctx)
    
    @Plugin.listen('MessageCreate')
    def meesucks_listener(self, event):
        if event.config.hate_meesux:
            if event.message.author.id != '159985870458322944':
                return
            event.message.reply('<@159985870458322944> **NO ONE CARES.**')
        else:
            return

    # @Plugin.listen('alexa play despacito')
    # def alexa_play_despacito_listener(self, event):
    #     if event.message.author.id != '191793155685744640':
    #         return
    #     event.message.reply('des')
    #     gevent.sleep(.5)
    #     event.message.reply('pa')
    #     gevent.sleep(.5)
    #     event.message.reply('cito') 

    @disco.bot.plugin.BasePluginDeco.listen("MessageCreate")
    def on_message_create(self, event):
        if "alexa play despacito" in event.message.content and event.author.id == 191793155685744640:
            def f():
                event.message.reply('des')
                gevent.sleep(.5)
                event.message.reply('pa')
                gevent.sleep(.5)
                event.message.reply('cito')
            gevent.spawn(f)
