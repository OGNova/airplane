import random
import requests
import humanize
import operator
import gevent
import disco

from six import BytesIO
from PIL import Image
from peewee import fn
from gevent.pool import Pool
from datetime import datetime, timedelta
from collections import defaultdict

from disco.types.user import GameType, Status
from disco.types.message import MessageEmbed
from disco.util.snowflake import to_datetime
from disco.util.sanitize import S

from rowboat.plugins import RowboatPlugin as Plugin, CommandFail
from disco.bot import CommandLevels
from rowboat.util.timing import Eventual
from rowboat.util.input import parse_duration
from rowboat.util.gevent import wait_many
from rowboat.util.stats import statsd, to_tags
from rowboat.types.plugin import PluginConfig
from rowboat.redis import rdb
from rowboat.models.guild import GuildVoiceSession
from rowboat.models.user import User, Infraction
from rowboat.models.message import Message, Reminder
from rowboat.util.images import get_dominant_colors_user, get_dominant_colors_guild
from rowboat.constants import (
    STATUS_EMOJI, SNOOZE_EMOJI, GREEN_TICK_EMOJI, GREEN_TICK_EMOJI_ID,
    EMOJI_RE, USER_MENTION_RE, YEAR_IN_SEC, CDN_URL
)


def get_status_emoji(presence):
    if presence.game and presence.game.type == GameType.STREAMING:
        return STATUS_EMOJI[GameType.STREAMING], 'Streaming'
    elif presence.status == Status.ONLINE:
        return STATUS_EMOJI[Status.ONLINE], 'Online'
    elif presence.status == Status.IDLE:
        return STATUS_EMOJI[Status.IDLE], 'Idle',
    elif presence.status == Status.DND:
        return STATUS_EMOJI[Status.DND], 'DND'
    elif presence.status in (Status.OFFLINE, Status.INVISIBLE):
        return STATUS_EMOJI[Status.OFFLINE], 'Offline'

def default_color(avatar_color):
    switcher = {
        'blurple': "https://cdn.discordapp.com/embed/avatars/0.png",
        'grey': "https://cdn.discordapp.com/embed/avatars/1.png",
        'green': "https://cdn.discordapp.com/embed/avatars/2.png",
        'orange': "https://cdn.discordapp.com/embed/avatars/3.png",
        'red': "https://cdn.discordapp.com/embed/avatars/4.png"
    }
    return switcher.get(avatar_color)

def get_emoji_url(emoji):
    return CDN_URL.format('-'.join(
        char.encode("unicode_escape").decode("utf-8")[2:].lstrip("0")
        for char in emoji))


class UtilitiesConfig(PluginConfig):
    pass


@Plugin.with_config(UtilitiesConfig)
class UtilitiesPlugin(Plugin):
    def load(self, ctx):
        super(UtilitiesPlugin, self).load(ctx)
        self.reminder_task = Eventual(self.trigger_reminders)
        self.spawn_later(10, self.queue_reminders)
        self.server_owners = {
            '158200017906171904': "Xen's Streamerino Disco", # Xentiran#0007
            '166304313004523520': "airplane, PokeBlobs", # OGNovuh#0003
            '175805198017626114': "Swagger's Hangout", # SwaggerSouls#4295
            '127060170802069505': "Hotel Fitz", # Fitz#9588
            '152626930250678273': "Ollybits!", # Q__Q#8008
            '107941250228830208': "Jameskii", # Jameskii#0001
            '197316087879172096': "Daniel's Discord", # danielharrison#0001
            '226912511302041601': "xd Official Discord", # McCreamy#6793
            '265986744019714050': "Dooocord", # TheDooo#4877
            '202271067912404992': "Donut Operator's Discord", # DonutOperator#5512
        }
        self.server_managers = {
            '158200017906171904': "Hotel Fitz", # Xentiran#0007
            '191793155685744640': "Hotel Fitz, Jameskii, Swagger's Hangout", # Terminator966#0966
            '227888061353164810': "Hotel Fitz", # emily#2900
            '324645959265157120': "Swagger's Hangout", # Mushy The Wizard#2319
            '285238487618420737': "Swagger's Hangout", # Boubie#0305
            '244907038667177984': "Swagger's Hangout", # Kata#7886
            '194903108495605760': "Swagger's Hangout", # Solaire#4156
            '138842652585099264': "Swagger's Hangout", # Xeano#4444
            '285712318464000000': "xd Official Discord", # Nuna#0001
            '340753167098839051': "Donut Operator's Discord", # Valkyrie#5555
            '339254723091890177': "Donut Operator's Discord", # AmazonPrimes#7409
            '173895003641217024': "Dooocord", # Gullus#0765
        }

    def queue_reminders(self):
        try:
            next_reminder = Reminder.select().order_by(
                Reminder.remind_at.asc()
            ).limit(1).get()
        except Reminder.DoesNotExist:
            return

        self.reminder_task.set_next_schedule(next_reminder.remind_at)

    @Plugin.command('coin', group='random', global_=True)
    def coin(self, event):
        """
        Flip a coin
        """
        event.msg.reply(random.choice(['heads', 'tails']))

    @Plugin.command('number', '[end:int] [start:int]', group='random', global_=True)
    def random_number(self, event, end=10, start=0):
        """
        Returns a random number
        """

        # Because someone will be an idiot
        if end > 9223372036854775807:
            return event.msg.reply(':warning: ending number too big!')

        if end <= start:
            return event.msg.reply(':warning: ending number must be larger than starting number!')

        event.msg.reply(str(random.randint(start, end)))

    @Plugin.command('cat', global_=True)
    def cat(self, event):
        # Sometimes random.cat gives us gifs (smh)
        for _ in range(3):
            try:
                r = requests.get('http://aws.random.cat/meow')
                r.raise_for_status()
            except:
                continue

            url = r.json()['file']
            if not url.endswith('.gif'):
                break
        else:
            return event.msg.reply('404 cat not found :(')

        r = requests.get(url)
        r.raise_for_status()
        event.msg.reply('', attachments=[('cat.jpg', r.content)])

    @Plugin.command('duck', aliases=['quack'], global_=True)
    def duck(self, event):
        # Sometimes random.cat gives us gifs (smh)
        for _ in range(3):
            try:
                r = requests.get('https://random-d.uk/api/v1/random?type=jpg')
                r.raise_for_status()
            except:
                continue

            url = r.json()['url']
            if not url.endswith('.gif'):
                break
        else:
            return event.msg.reply('404 duck not found :(')

        r = requests.get(url)
        r.raise_for_status()
        event.msg.reply('', attachments=[('duck.jpg', r.content)])
    
    @Plugin.command('bunny', aliases=['bunbun', 'wabbit', 'fluff'], global_=True)
    def bunny(self, event):
        try:
            r = requests.get('https://api.bunnies.io/v2/loop/random/?media=png,gif')
            r.raise_for_status()
        except:
            return event.msg.reply('404 bunny not found :(')

        media = r.json()['media']
        ext = 'png'
        if (media['gif']):
            url = media['gif']
            ext='gif'
        elif(media['png']):
            url = media['png']
        else:
            return event.msg.reply('404 bunny not found :(')

        r = requests.get(url)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            self.log.error('Bunny fetch failed: {}'.format(str(e)))
            return event.msg.reply('404 bunny not found :(')

        try:
            event.msg.reply('', attachments=[('bunny.{}'.format(ext), r.content)])
        except APIException:
            self.bunny(event)
    
    @Plugin.command('dog', global_=True)
    def dog(self, event):
        # Sometimes random.dog gives us gifs or mp4s (smh)
        for _ in range(3):
            try:
                r = requests.get('https://random.dog/woof.json')
                r.raise_for_status()
            except:
                continue
            
            url = r.json()['url']
            if not url.endswith('.gif') or not url.endswith('.mp4'):
                break
        else:
            return event.msg.reply('404 dog not found :(')

        r = requests.get(url)
        r.raise_for_status()
        event.msg.reply('', attachments=[('dog.jpg', r.content)])

    @Plugin.command('bird', aliases=['birb'], global_=True)
    def bird(self, event):
        # Sometimes random.birb gives us gifs or mp4s (smh)
        for _ in range(3):
            try:
                r = requests.get('https://random.birb.pw/tweet.json/')
                r.raise_for_status()
            except:
                continue
            
            name = r.json()['file']
            if not name.endswith('.gif') or not name.endswith('.mp4'):
                break
        else:
            return event.msg.reply('404 bird not found :(')

        r = requests.get('https://random.birb.pw/img/' + name)
        r.raise_for_status()
        event.msg.reply('', attachments=[('bird.jpg', r.content)])

    @Plugin.command('emoji', '<emoji:str>', global_=True)
    def emoji(self, event, emoji):
        if not EMOJI_RE.match(emoji):
            return event.msg.reply(u'Unknown emoji: `{}`'.format(S(emoji)))

        fields = []

        name, eid = EMOJI_RE.findall(emoji)[0]
        fields.append('**ID:** {}'.format(eid))
        fields.append('**Name:** {}'.format(S(name)))

        guild = self.state.guilds.find_one(lambda v: eid in v.emojis)
        if guild:
            fields.append('**Guild:** {} ({})'.format(S(guild.name), guild.id))

        anim = emoji.startswith('<a:')
        fields.append('**Animated:** {}'.format('Yes' if anim else 'No'))

        ext = 'gif' if anim else 'png'
        url = 'https://discordapp.com/api/emojis/{}.{}'.format(eid, ext)
        r = requests.get(url)
        r.raise_for_status()
        return event.msg.reply('\n'.join(fields), attachments=[('emoji.'+ext, r.content)])

    @Plugin.command('jumbo', '<emojis:str...>', global_=True)
    def jumbo(self, event, emojis):
        urls = []
        first_emote = emojis.split(' ')[0]
        if first_emote.startswith('<a:'):
            if EMOJI_RE.match(first_emote):
                eid = EMOJI_RE.findall(first_emote)[0]
                url = 'https://discordapp.com/api/emojis/{}.gif'.format(eid[1])
                r = requests.get(url)
                r.raise_for_status()
                return event.msg.reply('', attachments=[('emoji.gif', r.content)])
            else:
                raise CommandFail('Invalid Animated Emote.')
        else:
            for emoji in emojis.split(' ')[:5]:
                if emoji.startswith('<a:'):
                    continue
                if EMOJI_RE.match(emoji):
                    _, eid = EMOJI_RE.findall(emoji)[0]
                    urls.append('https://discordapp.com/api/emojis/{}.png'.format(eid))
                else:
                    urls.append(get_emoji_url(emoji))

            width, height, images = 0, 0, []

            for r in Pool(6).imap(requests.get, urls):
                try:
                    r.raise_for_status()
                except requests.HTTPError:
                    return

                img = Image.open(BytesIO(r.content))
                height = img.height if img.height > height else height
                width += img.width + 10
                images.append(img)

            image = Image.new('RGBA', (width, height))
            width_offset = 0
            for img in images:
                image.paste(img, (width_offset, 0))
                width_offset += img.width + 10

            combined = BytesIO()
            image.save(combined, 'png', quality=55)
            combined.seek(0)
            return event.msg.reply('', attachments=[('emoji.png', combined)])
    @Plugin.command('ping', level=CommandLevels.ADMIN)
    def command_ping(self, event):
        return event.msg.reply(':ping_pong: stop pinging me asshole!!!!!')
    @Plugin.command('seen', '<user:user>', global_=True)
    def seen(self, event, user):
        try:
            msg = Message.select(Message.timestamp).where(
                Message.author_id == user.id
            ).order_by(Message.timestamp.desc()).limit(1).get()
        except Message.DoesNotExist:
            return event.msg.reply(u"I've never seen {}".format(user))

        event.msg.reply(u'I last saw {} {} ago (at {})'.format(
            user,
            humanize.naturaldelta(datetime.utcnow() - msg.timestamp),
            msg.timestamp
        ))

    @Plugin.command('search', '<query:str...>', global_=True)
    def search(self, event, query):
        queries = []

        if query.isdigit():
            queries.append((User.user_id == query))

        q = USER_MENTION_RE.findall(query)
        if len(q) and q[0].isdigit():
            queries.append((User.user_id == q[0]))
        else:
            queries.append((User.username ** u'%{}%'.format(query.replace('%', ''))))

        if '#' in query:
            username, discrim = query.rsplit('#', 1)
            if discrim.isdigit():
                queries.append((
                    (User.username == username) &
                    (User.discriminator == int(discrim))))

        users = User.select().where(reduce(operator.or_, queries))
        if len(users) == 0:
            return event.msg.reply(u'No users found for query `{}`'.format(S(query, escape_codeblocks=True)))

        if len(users) == 1:
            if users[0].user_id in self.state.users:
                return self.info(event, self.state.users.get(users[0].user_id))

        return event.msg.reply(u'Found the following users for your query: ```{}```'.format(
            u'\n'.join(map(lambda i: u'{} ({})'.format(unicode(i), i.user_id), users[:25]))
        ))

    @Plugin.command('server', '[guild_id:snowflake]', global_=True)
    def server(self, event, guild_id=None):
        guild = self.state.guilds.get(guild_id) if guild_id else event.guild
        if not guild:
            raise CommandFail('invalid server')

        content = []
        content.append(u'**\u276F Server Information**')

        created_at = to_datetime(guild.id)
        content.append(u'Created: {} ago ({})'.format(
            humanize.naturaldelta(datetime.utcnow() - created_at),
            created_at.isoformat(),
        ))
        content.append(u'Members: {}'.format(len(guild.members)))
        content.append(u'Features: {}'.format(', '.join(guild.features) or 'none'))

        content.append(u'\n**\u276F Counts**')
        text_count = sum(1 for c in guild.channels.values() if not c.is_voice)
        voice_count = len(guild.channels) - text_count
        content.append(u'Roles: {}'.format(len(guild.roles)))
        content.append(u'Text: {}'.format(text_count))
        content.append(u'Voice: {}'.format(voice_count))

        content.append(u'\n**\u276F Members**')
        status_counts = defaultdict(int)
        for member in guild.members.values():
            if not member.user.presence:
                status = Status.OFFLINE
            else:
                status = member.user.presence.status
            status_counts[status] += 1

        for status, count in sorted(status_counts.items(), key=lambda i: str(i[0]), reverse=True):
            content.append(u'<{}> - {}'.format(
                STATUS_EMOJI[status], count
            ))

        embed = MessageEmbed()
        if guild.icon:
            embed.set_thumbnail(url=guild.icon_url)
            embed.color = get_dominant_colors_guild(guild)
        embed.description = '\n'.join(content)
        event.msg.reply('', embed=embed)

    # --------------Coded by Xenthys#0001 for Rawgoat--------------
    @Plugin.command('info', '[user:user|snowflake]')
    def info(self, event, user=None):
        if user is None:
            user = event.author

        user_id = 0
        if isinstance(user, (int, long)):
            user_id = user
            user = self.state.users.get(user)

        if user and not user_id:
            user = self.state.users.get(user.id)

        if not user:
            if user_id:
                user = self.fetch_user(user_id)
                User.from_disco_user(user)
            else:
                raise CommandFail('unknown user')

        content = []
        content.append(u'**\u276F User Information**')
        content.append(u'ID: {}'.format(user.id))
        content.append(u'Profile: <@{}>'.format(user.id))

        if user.presence:
            emoji, status = get_status_emoji(user.presence)
            content.append('Status: {} <{}>'.format(status, emoji))

            game = user.presence.game
            if game and game.name:
                activity = ['Playing', 'Stream'][int(game.type or 0)]
                if not game.type:
                    if game.name == 'Spotify':
                        activity = 'Listening to'
                    else:
                        activity = None
                if activity:
                    content.append(u'{}: {}'.format(activity,
                        u'[{}]({})'.format(game.name, game.url) if game.url else game.name
                    ))


        created_dt = to_datetime(user.id)
        content.append('Created: {} ago ({})'.format(
            humanize.naturaldelta(datetime.utcnow() - created_dt),
            created_dt.isoformat()
        ))

        for i in self.server_owners:
            if i == str(user.id):
                content.append('Server Ownership: {}'.format(self.server_owners[i]))
        
        for i in self.server_managers:
            if i == str(user.id):
                content.append('Community Manager: {}'.format(self.server_managers[i]))

        if user.id == self.state.me.id:
            content.append('Documentation: https://aetherya.stream/')
        elif rdb.sismember('global_admins', user.id):
            content.append('Airplane Staff: Global Administrator')

        member = event.guild.get_member(user.id) if event.guild else None
        if member:
            content.append(u'\n**\u276F Member Information**')

            if member.nick:
                content.append(u'Nickname: {}'.format(member.nick))

            content.append('Joined: {} ago ({})'.format(
                humanize.naturaldelta(datetime.utcnow() - member.joined_at),
                member.joined_at.isoformat(),
            ))

            if member.roles:
                roles = []
                for r in member.roles:
                    roles.append(member.guild.roles.get(r))
                roles = sorted(roles, key=lambda r: r.position, reverse=True)
                total = len(member.roles)
                roles = roles[:20]
                content.append(u'Roles ({}): {}{}'.format(
                    total, ' '.join(r.mention for r in roles),
                    ' (+{})'.format(total-20) if total > 20 else ''
                ))

        # Execute a bunch of queries async
        newest_msg = Message.select(Message.timestamp).where(
            (Message.author_id == user.id) &
            (Message.guild_id == event.guild.id)
        ).order_by(Message.timestamp.desc()).limit(1).async()

        # oldest_msg = Message.select(Message.timestamp).where(
        #     (Message.author_id == user.id) &
        #     (Message.guild_id == event.guild.id)
        # ).order_by(Message.timestamp.asc()).limit(1).async()

        infractions = Infraction.select(
            Infraction.guild_id,
            fn.COUNT('*')
        ).where(
            (Infraction.user_id == user.id) &
            (Infraction.type_ != 6) & # Unban
            (~(Infraction.reason ** '[NOTE]%'))
        ).group_by(Infraction.guild_id).tuples().async()

        voice = GuildVoiceSession.select(
            GuildVoiceSession.user_id,
            fn.COUNT('*'),
            fn.SUM(GuildVoiceSession.ended_at - GuildVoiceSession.started_at)
        ).where(
            (GuildVoiceSession.user_id == user.id) &
            (~(GuildVoiceSession.ended_at >> None))
        ).group_by(GuildVoiceSession.user_id).tuples().async()

        # Wait for them all to complete (we're still going to be as slow as the
        #  slowest query, so no need to be smart about this.)
        try:
            wait_many(newest_msg, infractions, voice, timeout=3)
        except gevent.Timeout:
            pass
        tags = to_tags(guild_id=event.msg.guild.id)
            
        if newest_msg.value:
            content.append(u'\n **\u276F Activity**')
            statsd.timing('sql.duration.newest_msg', newest_msg.value._query_time, tags=tags)
            newest_msg = newest_msg.value.get()
            content.append('Last Message: {} ago ({})'.format(
                humanize.naturaldelta(datetime.utcnow() - newest_msg.timestamp),
                newest_msg.timestamp.isoformat(),
            ))

        # if oldest_msg.value:
        #     statsd.timing('sql.duration.oldest_msg', oldest_msg.value._query_time, tags=tags)
        #     oldest_msg = oldest_msg.value.get()
        #     content.append('First Message: {} ago ({})'.format(
        #         humanize.naturaldelta(datetime.utcnow() - oldest_msg.timestamp),
        #         oldest_msg.timestamp.isoformat(),
        #     ))

        if infractions.value:
            statsd.timing('sql.duration.infractions', infractions.value._query_time, tags=tags)
            infractions = list(infractions.value)
            total = sum(i[1] for i in infractions)
            content.append(u'\n**\u276F Infractions**')
            content.append('Total Infractions: {}'.format(total))
            content.append('Unique Servers: {}'.format(len(infractions)))

        if voice.value:
            statsd.timing('plugin.utilities.info.sql.voice', voice.value._query_time, tags=tags)
            voice = list(voice.value)
            content.append(u'\n**\u276F Voice**')
            content.append(u'Sessions: {}'.format(voice[0][1]))
            content.append(u'Time: {}'.format(humanize.naturaldelta(
                voice[0][2]
            )))

        embed = MessageEmbed()

        avatar = user.avatar
        if avatar:
            avatar = u'https://cdn.discordapp.com/avatars/{}/{}.{}'.format(
                user.id, avatar, u'gif' if avatar.startswith('a_') else u'png'
            )
        else:
            avatar = u'https://cdn.discordapp.com/embed/avatars/{}.png'.format(
                int(user.discriminator) % 5
            )

        embed.set_author(name=u'{}#{}'.format(
            user.username,
            user.discriminator,
        ), icon_url=avatar)

        embed.set_thumbnail(url=avatar)

        embed.description = '\n'.join(content)
        try:
            embed.color = get_dominant_colors_user(user, avatar)
        except:
            pass
        event.msg.reply('', embed=embed)

# --------------Coded by Xenthys#0001 for Rawgoat--------------

    def trigger_reminders(self):
        reminders = Reminder.with_message_join().where(
            (Reminder.remind_at < (datetime.utcnow() + timedelta(seconds=1)))
        )

        waitables = []
        for reminder in reminders:
            waitables.append(self.spawn(self.trigger_reminder, reminder))

        for waitable in waitables:
            waitable.join()

        self.queue_reminders()

    def trigger_reminder(self, reminder):
        message = reminder.message_id
        channel = self.state.channels.get(message.channel_id)
        if not channel:
            self.log.warning('Not triggering reminder, channel %s was not found!',
                message.channel_id)
            reminder.delete_instance()
            return

        msg = channel.send_message(u'<@{}> you asked me at {} ({} ago) to remind you about: {}'.format(
            message.author_id,
            reminder.created_at,
            humanize.naturaldelta(reminder.created_at - datetime.utcnow()),
            S(reminder.content)
        ))

        # Add the emoji options
        msg.add_reaction(SNOOZE_EMOJI)
        msg.add_reaction(GREEN_TICK_EMOJI)

        try:
            mra_event = self.wait_for_event(
                'MessageReactionAdd',
                message_id=msg.id,
                conditional=lambda e: (
                    (e.emoji.name == SNOOZE_EMOJI or e.emoji.id == GREEN_TICK_EMOJI_ID) and
                    e.user_id == message.author_id
                )
            ).get(timeout=30)
        except gevent.Timeout:
            reminder.delete_instance()
            return
        finally:
            # Cleanup
            msg.delete_reaction(SNOOZE_EMOJI)
            msg.delete_reaction(GREEN_TICK_EMOJI)

        if mra_event.emoji.name == SNOOZE_EMOJI:
            reminder.remind_at = datetime.utcnow() + timedelta(minutes=20)
            reminder.save()
            msg.edit(u'Ok, I\'ve snoozed that reminder for 20 minutes.')
            return

        reminder.delete_instance()

    @Plugin.command('clear', group='r', global_=True)
    def cmd_remind_clear(self, event):
        count = Reminder.delete_for_user(event.author.id)
        return event.msg.reply(':ok_hand: I cleared {} reminders for you'.format(count))

    @Plugin.command('add', '<duration:str> <content:str...>', group='r', global_=True)
    @Plugin.command('remind', '<duration:str> <content:str...>', global_=True)
    def cmd_remind(self, event, duration, content):
        if Reminder.count_for_user(event.author.id) > 30:
            return event.msg.reply(':warning: you an only have 15 reminders going at once!')

        remind_at = parse_duration(duration)
        if remind_at > (datetime.utcnow() + timedelta(seconds=5 * YEAR_IN_SEC)):
            return event.msg.reply(':warning: thats too far in the future, I\'ll forget!')

        r = Reminder.create(
            message_id=event.msg.id,
            remind_at=remind_at,
            content=content
        )
        self.reminder_task.set_next_schedule(r.remind_at)
        event.msg.reply(':ok_hand: I\'ll remind you at {} ({})'.format(
            r.remind_at.isoformat(),
            humanize.naturaldelta(r.remind_at - datetime.utcnow()),
        ))
