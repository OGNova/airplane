from datetime import datetime, timedelta
from disco.bot import CommandLevels
from disco.voice.player import Player
from disco.voice.playable import YoutubeDLInput, BufferedOpusEncoderPlayable
from disco.voice.client import VoiceException
from disco.types.message import MessageTable

from rowboat.plugins import RowboatPlugin as Plugin, CommandFail, CommandSuccess
from rowboat.types import Field
from rowboat.models.guild import Guild
from rowboat.types.plugin import PluginConfig

class MusicConfig(PluginConfig):
    max_song_length = Field(int, default=7200)

@Plugin.with_config(MusicConfig)
class MusicPlugin(Plugin):
    def load(self, ctx):
        super(MusicPlugin, self).load(ctx)
        self.guilds = {}

    @Plugin.command('connect', level=CommandLevels.TRUSTED)
    def on_join(self, event):
        g = Guild.select(Guild).where((Guild.guild_id == event.guild.id)).get()    

        if g.premium == False:
          raise CommandFail('This guild does not have premium enabled, please contact an Airplane global administrator.')

        if event.guild.id in self.guilds:
            return event.msg.reply("I'm already playing music here.")

        state = event.guild.get_member(event.author).get_voice_state()
        if not state:
            return event.msg.reply('You must be connected to voice to use that command.')

        try:
            client = state.channel.connect()
        except VoiceException as e:
            return event.msg.reply('Failed to connect to voice: `{}`'.format(e))

        self.guilds[event.guild.id] = Player(client)
        self.guilds[event.guild.id].complete.wait()
        del self.guilds[event.guild.id]

    def get_player(self, guild_id):
        if guild_id not in self.guilds:
            raise CommandFail("I'm not currently playing music here.")
        return self.guilds.get(guild_id)

    @Plugin.command('disconnect', level=CommandLevels.TRUSTED)
    def on_leave(self, event):
        self.get_player(event.guild.id).disconnect()

    @Plugin.command('play', '<url:str>', level=CommandLevels.TRUSTED)
    def on_play(self, event, url):
        g = Guild.select(Guild).where((Guild.guild_id == event.guild.id)).get()
        
        if g.premium == False:
          raise CommandFail('This guild does not have premium enabled, please contact an Airplane global administrator.')
        
        # item = YoutubeDLInput(url, command='ffmpeg').pipe(BufferedOpusEncoderPlayable)
        # self.get_player(event.guild.id).queue.append(item)
        item = YoutubeDLInput(url)
        song = item.info
        if song['extractor'] is 'youtube':
            if song['is_live']:
                raise CommandFail('Sorry, live streams are not supported.')
        if song['duration'] > 7200:
            raise CommandFail('Sorry you are not allowed to play songs over 2 hours.')
        if song['duration'] > event.config.max_song_length:
            raise CommandFail('Sorry, you may not go over the server time limit.')
        item2 = item.pipe(BufferedOpusEncoderPlayable)
        self.get_player(event.guild.id).queue.append(item2)
        song = item.info
        if song['extractor'] is 'youtube':
            if song['artist']:
                return event.msg.reply('Now playing **{songname}** by **{author}**. Song length is `{duration}`'.format(songname=song['alt_title'], author=song['artist'], duration=timedelta(seconds=song['duration'])))
            else:
                return event.msg.reply('Now playing **{songname}** uploaded by **{author}**. Song length is `{duration}`'.format(songname=song['title'], author=song['uploader'], duration=timedelta(seconds=song['duration'])))
        else:
            return CommandSuccess('You\'re playing a song :D')

    @Plugin.command('pause', level=CommandLevels.TRUSTED)
    def on_pause(self, event):
        self.get_player(event.guild.id).pause()

    @Plugin.command('resume', level=CommandLevels.TRUSTED)
    def on_resume(self, event):
        self.get_player(event.guild.id).resume()

    @Plugin.command('stop', level=CommandLevels.TRUSTED)
    def on_stop(self, event):
        self.get_player(event.guild.id).stop()

    @Plugin.command('kill', level=CommandLevels.MOD)
    def on_kill(self, event):
        self.get_player(event.guild.id).client.ws.sock.shutdown()

    @Plugin.command('queue', level=CommandLevels.TRUSTED)
    def on_queue(self, event):
        player = self.get_player(event.guild.id)
        queue = player.queue
        np = player.now_playing.metadata

        if len(queue) is 0:
            return event.msg.reply('The queue is empty. Try adding some songs.')
        _msg = [
            '__**Queue**__'
        ]

        if np['artist']:
            _msg.append('***Playing***: **{}** by **{}** (`{}` long)'.format(np['alt_title'], np['artist'], timedelta(seconds=np['duration'])))
        else:
            _msg.append('***Playing***: **{}** by **{}** (`{}` long)'.format(np['title'], np['uploader'], timedelta(seconds=np['duration'])))

        for index, x in enumerate(queue):
            if x.metadata['artist']:
                y = x.metadata
                _msg.append('`{}`) **{}** by **{}** (`{}` long)'.format(index, y['alt_title'], y['artist'], timedelta(seconds=y['duration'])))
            else:
                y = x.metadata
                _msg.append('`{}`) **{}** by **{}** (`{}` long)'.format(index, y['title'], y['uploader'], timedelta(seconds=y['duration'])))

        event.msg.reply('\n'.join(_msg))

    @Plugin.command('np', level=CommandLevels.TRUSTED)
    def on_np(self, event):
        player = self.get_player(event.guild.id)
        np = player.now_playing.metadata
        event.msg.reply('Now playing **{}** by **{}**. Song length is `{}`'.format(np['alt_title'], np['artist'], timedelta(seconds=np['duration'])))