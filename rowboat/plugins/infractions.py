import csv
import gevent
import humanize

from StringIO import StringIO
from holster.emitter import Priority

from datetime import datetime

from disco.bot import CommandLevels
from disco.types.user import User as DiscoUser
from disco.types.message import MessageTable, MessageEmbed

from rowboat.plugins import RowboatPlugin as Plugin, CommandFail, CommandSuccess
from rowboat.util.timing import Eventual
from rowboat.util.input import parse_duration
from rowboat.types import Field, snowflake
from rowboat.types.plugin import PluginConfig
from rowboat.types import ChannelField, SlottedModel, ListField, DictField
from rowboat.plugins.modlog import Actions
from rowboat.models.user import User, Infraction
from rowboat.models.guild import GuildMemberBackup, GuildBan
from rowboat.sql import database
from rowboat.constants import (
    GREEN_TICK_EMOJI_ID, RED_TICK_EMOJI_ID, GREEN_TICK_EMOJI, RED_TICK_EMOJI
)


def clamp(string, size):
    if len(string) > size:
        return string[:size] + '...'
    return string

def maybe_string(obj, exists, notexists, **kwargs):
    if obj:
        return exists.format(o=obj, **kwargs)
    return notexists.format(**kwargs)
class NotifyConfig(SlottedModel):
    mutes = Field(bool, default=False)
    warns = Field(bool, default=False)
    kicks = Field(bool, default=False)
    bans = Field(bool, default=False)
    invite_back = Field(bool, default=False)

class InfractionsConfig(PluginConfig):
    # Whether to confirm actions in the channel they are executed
    confirm_actions = Field(bool, default=True)
    confirm_actions_reaction = Field(bool, default=False)
    confirm_actions_expiry = Field(int, default=0)

    # Whether to notify users on actions
    notify_action_on = Field(NotifyConfig, default=None)

    # The mute role
    mute_role = Field(snowflake, default=None)

    # Level required to edit reasons
    reason_edit_level = Field(int, default=int(CommandLevels.ADMIN))

def invite_finder(guildid):
    switcher = {
        224914336538296322: "https://discord.gg/swaggersouls",
        264508089686949888: "https://discord.gg/jameskii",
        292516924557099008: "https://discord.gg/fitz",
        299736482992619520: "https://discord.gg/thedooo",
        454533671622410251: "https://discord.gg/xdgang",
        469566508838682644: "https://discord.gg/Gu7jRdW"

    }
    return switcher.get(guildid, "No stored invite for this server.")

@Plugin.with_config(InfractionsConfig)
class InfractionsPlugin(Plugin):
    def load(self, ctx):
        super(InfractionsPlugin, self).load(ctx)

        self.inf_task = Eventual(self.clear_infractions)
        self.spawn_later(5, self.queue_infractions)

    def queue_infractions(self):
        next_infraction = list(Infraction.select().where(
            (Infraction.active == 1) &
            (~(Infraction.expires_at >> None))
        ).order_by(Infraction.expires_at.asc()).limit(1))

        if not next_infraction:
            self.log.info('[INF] no infractions to wait for')
            return

        self.log.info('[INF] waiting until %s for %s', next_infraction[0].expires_at, next_infraction[0].id)
        self.inf_task.set_next_schedule(next_infraction[0].expires_at)

    def clear_infractions(self):
        expired = list(Infraction.select().where(
            (Infraction.active == 1) &
            (Infraction.expires_at < datetime.utcnow()) #testing to fix temp inf counting up
        ))

        self.log.info('[INF] attempting to clear %s expired infractions', len(expired))

        for item in expired:
            guild = self.state.guilds.get(item.guild_id)
            if not guild:
                self.log.warning('[INF] failed to clear infraction %s, no guild exists', item.id)
                continue

            # TODO: hacky
            type_ = {i.index: i for i in Infraction.Types.attrs}[item.type_]
            if type_ == Infraction.Types.TEMPBAN:
                self.call(
                    'ModLogPlugin.create_debounce',
                    guild.id,
                    ['GuildBanRemove'],
                    user_id=item.user_id,
                )

                try:
                    guild.delete_ban(item.user_id)
                except:
                    pass

                # TODO: perhaps join on users above and use username from db
                self.call(
                    'ModLogPlugin.log_action_ext',
                    Actions.MEMBER_TEMPBAN_EXPIRE,
                    guild.id,
                    user_id=item.user_id,
                    user=unicode(self.state.users.get(item.user_id) or item.user_id),
                    inf=item
                )
            elif type_ == Infraction.Types.TEMPMUTE or Infraction.Types.TEMPROLE:
                member = guild.get_member(item.user_id)
                if member:
                    if item.metadata['role'] in member.roles:
                        self.call(
                            'ModLogPlugin.create_debounce',
                            guild.id,
                            ['GuildMemberUpdate'],
                            user_id=item.user_id,
                            role_id=item.metadata['role'],
                        )

                        try:
                            member.remove_role(item.metadata['role'])
                        except:
                            pass

                        self.call(
                            'ModLogPlugin.log_action_ext',
                            Actions.MEMBER_TEMPMUTE_EXPIRE,
                            guild.id,
                            member=member,
                            inf=item
                        )
                        # if self.config.notify_action_on.mutes:
                        #     try:
                        #         item.guild_id.get_member(item.user_id).user.open_dm().send_message('Your **Temporary Mute** in the guild **{}** has expired.'.format(event.guild.name))
                        #     except:
                        #         pass
                        # else:
                        #     pass
                else:
                    GuildMemberBackup.remove_role(
                        item.guild_id,
                        item.user_id,
                        item.metadata['role'])

                    # if self.config.notify_action_on.mutes:
                    #     try:
                    #         item.guild_id.get_member(item.user_id).user.open_dm().send_message('Your **Temporary Mute** in the guild **{}** has expired.'.format(event.guild.name))
                    #     except:
                    #         pass
                    # else:
                    #     pass
            else:
                self.log.warning('[INF] failed to clear infraction %s, type is invalid %s', item.id, item.type_)
                continue

            # TODO: n+1
            item.active = False
            item.save()

        # Wait a few seconds to backoff from a possible bad loop, and requeue new infractions
        gevent.sleep(5)
        self.queue_infractions()

    @Plugin.listen('GuildMemberUpdate', priority=Priority.BEFORE)
    def on_guild_member_update(self, event):
        pre_member = event.guild.members.get(event.id)
        if not pre_member:
            return

        pre_roles = set(pre_member.roles)
        post_roles = set(event.roles)
        if pre_roles == post_roles:
            return

        removed = pre_roles - post_roles

        # If the user was unmuted, mark any temp-mutes as inactive
        if event.config.mute_role in removed:
            Infraction.clear_active(event, event.user.id, [Infraction.Types.TEMPMUTE])

    @Plugin.listen('GuildBanRemove')
    def on_guild_ban_remove(self, event):
        Infraction.clear_active(event, event.user.id, [Infraction.Types.BAN, Infraction.Types.TEMPBAN])

    @Plugin.command('unban', '<user:snowflake> [reason:str...]', level=CommandLevels.MOD)
    def unban(self, event, user, reason=None):
        try:
            GuildBan.get(user_id=user, guild_id=event.guild.id)
            event.guild.delete_ban(user)
        except GuildBan.DoesNotExist:
            raise CommandFail('user with id `{}` is not banned'.format(user))

        Infraction.create(
            guild_id=event.guild.id,
            user_id=user,
            actor_id=event.author.id,
            type_=Infraction.Types.UNBAN,
            reason=reason
        )
        raise CommandSuccess('unbanned user with id `{}`'.format(user))

    @Plugin.command('archive', group='infractions', level=CommandLevels.ADMIN)
    def infractions_archive(self, event):
        user = User.alias()
        actor = User.alias()

        q = Infraction.select(Infraction, user, actor).join(
            user,
            on=((Infraction.user_id == user.user_id).alias('user'))
        ).switch(Infraction).join(
            actor,
            on=((Infraction.actor_id == actor.user_id).alias('actor'))
        ).where(Infraction.guild_id == event.guild.id)

        buff = StringIO()
        w = csv.writer(buff)

        for inf in q:
            w.writerow([
                inf.id,
                inf.user_id,
                unicode(inf.user).encode('utf-8'),
                inf.actor_id,
                unicode(inf.actor).encode('utf-8'),
                unicode({i.index: i for i in Infraction.Types.attrs}[inf.type_]).encode('utf-8'),
                unicode(inf.reason).encode('utf-8'),
            ])

        event.msg.reply('Ok, here is an archive of all infractions', attachments=[
            ('infractions.csv', buff.getvalue())
        ])

    @Plugin.command('info', '<infraction:int>', group='infractions', level=CommandLevels.MOD)
    def infraction_info(self, event, infraction):
        try:
            user = User.alias()
            actor = User.alias()

            infraction = Infraction.select(Infraction, user, actor).join(
                user,
                on=((Infraction.user_id == user.user_id).alias('user'))
            ).switch(Infraction).join(
                actor,
                on=((Infraction.actor_id == actor.user_id).alias('actor'))
            ).where(
                    (Infraction.id == infraction) &
                    (Infraction.guild_id == event.guild.id)
            ).get()
        except Infraction.DoesNotExist:
            raise CommandFail('cannot find an infraction with ID `{}`'.format(infraction))

        type_ = {i.index: i for i in Infraction.Types.attrs}[infraction.type_]
        embed = MessageEmbed()

        if type_ in (Infraction.Types.MUTE, Infraction.Types.TEMPMUTE, Infraction.Types.TEMPROLE):
            embed.color = 0xfdfd96
        elif type_ in (Infraction.Types.KICK, Infraction.Types.SOFTBAN):
            embed.color = 0xffb347
        else:
            embed.color = 0xff6961

        embed.title = str(type_).title()
        embed.set_thumbnail(url=infraction.user.get_avatar_url())
        embed.add_field(name='User', value=unicode(infraction.user), inline=True)
        embed.add_field(name='Moderator', value=unicode(infraction.actor), inline=True)
        embed.add_field(name='Active', value='yes' if infraction.active else 'no', inline=True)
        if infraction.active and infraction.expires_at:
            embed.add_field(name='Expires', value=humanize.naturaldelta(infraction.expires_at - datetime.utcnow()))
        embed.add_field(name='Reason', value=infraction.reason or '_No Reason Given', inline=False)
        embed.timestamp = infraction.created_at.isoformat()
        event.msg.reply('', embed=embed)

    @Plugin.command('search', '[query:user|str...]', group='infractions', level=CommandLevels.MOD)
    def infraction_search(self, event, query=None):
        q = (Infraction.guild_id == event.guild.id)

        if query and isinstance(query, list) and isinstance(query[0], DiscoUser):
            query = query[0].id
        elif query:
            query = ' '.join(query)

        if query and (isinstance(query, int) or query.isdigit()):
            q &= (
                (Infraction.id == int(query)) |
                (Infraction.user_id == int(query)) |
                (Infraction.actor_id == int(query)))
        elif query:
            q &= (Infraction.reason ** query)

        user = User.alias()
        actor = User.alias()

        infractions = Infraction.select(Infraction, user, actor).join(
            user,
            on=((Infraction.user_id == user.user_id).alias('user'))
        ).switch(Infraction).join(
            actor,
            on=((Infraction.actor_id == actor.user_id).alias('actor'))
        ).where(q).order_by(Infraction.created_at.desc()).limit(6)

        tbl = MessageTable()

        tbl.set_header('ID', 'Created', 'Type', 'User', 'Moderator', 'Active', 'Reason')
        for inf in infractions:
            type_ = {i.index: i for i in Infraction.Types.attrs}[inf.type_]
            reason = inf.reason or ''
            if len(reason) > 256:
                reason = reason[:256] + '...'

            if inf.active:
                active = 'yes'
                if inf.expires_at:
                    active += ' (expires in {})'.format(humanize.naturaldelta(inf.expires_at - datetime.utcnow()))
            else:
                active = 'no'

            tbl.add(
                inf.id,
                inf.created_at.isoformat(),
                str(type_),
                unicode(inf.user),
                unicode(inf.actor),
                active,
                clamp(reason, 128)
            )

        event.msg.reply(tbl.compile())

    @Plugin.command('recent', aliases=['latest'], group='infractions', level=CommandLevels.MOD)
    def infractions_recent(self, event):
        # TODO: fucking write this bruh
        pass

    @Plugin.command('duration', '<infraction:int> <duration:str>', group='infractions', level=CommandLevels.MOD)
    def infraction_duration(self, event, infraction, duration):
        try:
            inf = Infraction.get(id=infraction)
        except Infraction.DoesNotExist:
            raise CommandFail('invalid infraction (try `!infractions recent`)')

        if inf.actor_id != event.author.id and event.user_level < CommandLevels.ADMIN:
            raise CommandFail('only administrators can modify the duration of infractions created by other moderators')

        if not inf.active:
            raise CommandFail('that infraction is not active and cannot be updated')

        expires_dt = parse_duration(duration, inf.created_at)

        converted = False
        if inf.type_ in [Infraction.Types.MUTE.index, Infraction.Types.BAN.index]:
            inf.type_ = (
                Infraction.Types.TEMPMUTE
                if inf.type_ == Infraction.Types.MUTE.index else
                Infraction.Types.TEMPBAN
            )
            converted = True
        elif inf.type_ not in [
                Infraction.Types.TEMPMUTE.index,
                Infraction.Types.TEMPBAN.index,
                Infraction.Types.TEMPROLE.index]:
            raise CommandFail('cannot set the duration for that type of infraction')

        inf.expires_at = expires_dt
        inf.save()
        self.queue_infractions()

        if converted:
            raise CommandSuccess('ok, I\'ve made that infraction temporary, it will now expire on {}'.format(
                inf.expires_at.isoformat()
            ))
        else:
            raise CommandSuccess('ok, I\'ve updated that infractions duration, it will now expire on {}'.format(
                inf.expires_at.isoformat()
            ))

    @Plugin.command('reason', '<infraction:int> <reason:str...>', group='infractions', level=CommandLevels.MOD)
    def reason(self, event, infraction, reason):
        try:
            inf = Infraction.get(id=infraction)
        except Infraction.DoesNotExist:
            inf = None

        if inf is None or inf.guild_id != event.guild.id:
            event.msg.reply('Unknown infraction ID')
            return

        if not inf.actor_id:
            inf.actor_id = event.author.id

        if inf.actor_id != event.author.id and event.user_level < event.config.reason_edit_level:
            raise CommandFail('you do not have the permissions required to edit other moderators infractions')

        inf.reason = reason
        inf.save()

        raise CommandSuccess('I\'ve updated the reason for infraction #{}'.format(inf.id))

    def can_act_on(self, event, victim_id, throw=True):
        if event.author.id == victim_id:
            if not throw:
                return False
            raise CommandFail('cannot execute that action on yourself')

        victim_level = self.bot.plugins.get('CorePlugin').get_level(event.guild, victim_id)

        if event.user_level <= victim_level:
            if not throw:
                return False
            raise CommandFail('invalid permissions')

        return True

    def confirm_action(self, event, message):
        if not event.config.confirm_actions:
            return

        if event.config.confirm_actions_reaction:
            event.msg.add_reaction(GREEN_TICK_EMOJI)
            return

        msg = event.msg.reply(message)

        if event.config.confirm_actions_expiry > 0:
            # Close over this thread local
            expiry = event.config.confirm_actions_expiry

            def f():
                gevent.sleep(expiry)
                msg.delete()

            # Run this in a greenlet so we dont block event execution
            self.spawn(f)

    @Plugin.command('delete', '<infraction:int> [reason:str...]', group='infractions', level=-1)
    def infraction_delete(self, event, infraction):
        query = "DELETE FROM infractions WHERE id=%s RETURNING *;"

        msg = event.msg.reply('Ok, delete infraction #`{}`?'.format(infraction))
        msg.chain(False).\
            add_reaction(GREEN_TICK_EMOJI).\
            add_reaction(RED_TICK_EMOJI)

        try:
            mra_event = self.wait_for_event(
                'MessageReactionAdd',
                message_id=msg.id,
                conditional=lambda e: (
                    e.emoji.id in (GREEN_TICK_EMOJI_ID, RED_TICK_EMOJI_ID) and
                    e.user_id == event.author.id
                )).get(timeout=10)
        except gevent.Timeout:
            return
        finally:
            msg.delete()

        if mra_event.emoji.id != GREEN_TICK_EMOJI_ID:
            return
        conn = database.obj.get_conn()
        try:
            c = conn.cursor()
            c.execute(query, (infraction,))
            conn.commit()
            c.close    
        except Infraction.DoesNotExist:
            raise CommandFail('invalid infraction (try `!infractions recent`)')
        except:
            raise CommandFail('Failed to delete infraction #`{}`'.format(infraction))
        self.queue_infractions()
        c.close()
        conn.close()
        raise CommandSuccess('Successfully deleted inf #`{}`.'.format(infraction))


        # if inf.actor_id != event.author.id and event.user_level < CommandLevels.ADMIN:
        #     raise CommandFail('only administrators can modify the duration of infractions created by other moderators')
    
    @Plugin.command('mute', '<user:user|snowflake> [reason:str...]', level=CommandLevels.MOD)
    @Plugin.command('tempmute', '<user:user|snowflake> <duration:str> [reason:str...]', level=CommandLevels.MOD)
    def tempmute(self, event, user, duration=None, reason=None):
        if not duration and reason:
            duration = parse_duration(reason.split(' ')[0], safe=True)
            if duration:
                if ' ' in reason:
                    reason = reason.split(' ', 1)[-1]
                else:
                    reason = None
        elif duration:
            duration = parse_duration(duration)

        member = event.guild.get_member(user)
        if member:
            self.can_act_on(event, member.id)
            if not event.config.mute_role:
                raise CommandFail('mute is not setup on this server')

            if event.config.mute_role in member.roles:
                raise CommandFail(u'{} is already muted'.format(member.user))

            # If we have a duration set, this is a tempmute
            if duration:
                # Create the infraction
                       
                
                Infraction.tempmute(self, event, member, reason, duration)
                self.queue_infractions()

                self.confirm_action(event, maybe_string(
                    reason,
                    u':ok_hand: {u} is now muted for {t} (`{o}`)',
                    u':ok_hand: {u} is now muted for {t}',
                    u=member.user,
                    t=humanize.naturaldelta(duration - datetime.utcnow()),
                ))

                if not event.config.notify_action_on:
                    return
                else:                
                    if event.config.notify_action_on.mutes:
                        try:
                            event.guild.get_member(user.id).user.open_dm().send_message('You have been **Temporarily Muted** in the guild **{}** for **{}** for `{}`'.format(event.guild.name, humanize.naturaldelta(duration - datetime.utcnow()), reason or 'no reason specified.'))
                            event.msg.reply('Dm was successfully sent. <:'+GREEN_TICK_EMOJI+'>')
                        except:
                            event.msg.reply('Unable to send a DM to this user.')
                    else:
                        pass
            else:
                existed = False
                # If the user is already muted check if we can take this from a temp
                #  to perma mute.
                if event.config.mute_role in member.roles:
                    existed = Infraction.clear_active(event, member.id, [Infraction.Types.TEMPMUTE])
                    # The user is 100% muted and not tempmuted at this point, so lets bail
                    if not existed:
                        raise CommandFail(u'{} is already muted'.format(member.user))

                Infraction.mute(self, event, member, reason)                       

                existed = u' [was temp-muted]' if existed else ''
                self.confirm_action(event, maybe_string(
                    reason,
                    u':ok_hand: {u} is now muted (`{o}`)' + existed,
                    u':ok_hand: {u} is now muted' + existed,
                    u=member.user,
                ))
                if event.config.notify_action_on.mutes:
                    try:
                        event.guild.get_member(user.id).user.open_dm().send_message('You have been **Permanently Muted** in the guild **{}** for `{}`'.format(event.guild.name, reason or 'no reason specified.'))
                        event.msg.reply('Dm was successfully sent. <:'+GREEN_TICK_EMOJI+'>')
                    except:
                        event.msg.reply('Unable to send a DM to this user.')
                else:
                    pass
        else:
            raise CommandFail('invalid user')

    @Plugin.command(
        'temprole',
        '<user:user|snowflake> <role:snowflake|str> <duration:str> [reason:str...]',
        level=CommandLevels.MOD)
    def temprole(self, event, user, role, duration, reason=None):
        member = event.guild.get_member(user)
        if not member:
            raise CommandFail('invalid user')

        self.can_act_on(event, member.id)
        role_id = role if isinstance(role, (int, long)) else event.config.role_aliases.get(role.lower())
        if not role_id or role_id not in event.guild.roles:
            raise CommandFail('invalid or unknown role')

        if role_id in member.roles:
            raise CommandFail(u'{} is already in that role'.format(member.user))

        expire_dt = parse_duration(duration)
        Infraction.temprole(self, event, member, role_id, reason, expire_dt)
        self.queue_infractions()

        self.confirm_action(event, maybe_string(
            reason,
            u':ok_hand: {u} is now in the {r} role for {t} (`{o}`)',
            u':ok_hand: {u} is now in the {r} role for {t}',
            r=event.guild.roles[role_id].name,
            u=member.user,
            t=humanize.naturaldelta(expire_dt - datetime.utcnow()),
        ))

    @Plugin.command('unmute', '<user:user|snowflake>', level=CommandLevels.MOD)
    def unmute(self, event, user, reason=None):
        # TOOD: eventually we should pull the role from the GuildMemberBackup if they arent in server
        member = event.guild.get_member(user)

        if member:
            self.can_act_on(event, member.id)
            if not event.config.mute_role:
                raise CommandFail('mute is not setup on this server')

            if event.config.mute_role not in member.roles:
                raise CommandFail(u'{} is not muted'.format(member.user))

            Infraction.clear_active(event, member.id, [Infraction.Types.MUTE, Infraction.Types.TEMPMUTE])

            self.call(
                'ModLogPlugin.create_debounce',
                event,
                ['GuildMemberUpdate'],
                role_id=event.config.mute_role,
            )

            member.remove_role(event.config.mute_role)


            self.call(
                'ModLogPlugin.log_action_ext',
                Actions.MEMBER_UNMUTED,
                event.guild.id,
                member=member,
                actor=unicode(event.author) if event.author.id != member.id else 'Automatic',
            )

            self.confirm_action(event, u':ok_hand: {} is now unmuted'.format(member.user))
            if event.config.notify_action_on.mutes:
                try:
                    event.guild.get_member(user.id).user.open_dm().send_message('You have been **Un-Muted** in the guild **{}**'.format(event.guild.name))
                    event.msg.reply('Dm was successfully sent. <:'+GREEN_TICK_EMOJI+'>')
                except:
                    event.msg.reply('Unable to send a DM to this user.')
            else:
                pass
        else:
            raise CommandFail('invalid user')

    @Plugin.command('kick', '<user:user|snowflake> [reason:str...]', level=CommandLevels.MOD)
    def kick(self, event, user, reason=None):
        member = event.guild.get_member(user)
        if member:
            if event.config.notify_action_on.kicks:
                if not event.config.notify_action_on.invite_back:
                    try:
                        event.guild.get_member(user.id).user.open_dm().send_message('You have been **Kicked** from the guild **{}** for `{}`'.format(event.guild.name, reason or 'no reason'))
                        event.msg.reply('Dm was successfully sent. <:'+GREEN_TICK_EMOJI+'>')
                    except:
                        event.msg.reply('Unable to send a DM to this user.')
                else:    
                    guild_invite = invite_finder(event.guild.id)
                    try:
                        event.guild.get_member(user.id).user.open_dm().send_message('You have been **Kicked** from the guild **{}** for `{}`\nYou can join back with this invite link: {}'.format(event.guild.name, reason or 'no reason', guild_invite))
                        event.msg.reply('Dm was successfully sent. <:'+GREEN_TICK_EMOJI+'>')
                    except:
                        event.msg.reply('Unable to send a DM to this user.')                    
            else:
                pass
            self.can_act_on(event, member.id)
            Infraction.kick(self, event, member, reason)
            self.confirm_action(event, maybe_string(
                reason,
                u':ok_hand: kicked {u} (`{o}`)',
                u':ok_hand: kicked {u}',
                u=member.user,
            ))
        else:
            raise CommandFail('invalid user')

    @Plugin.command('mkick', parser=True, level=CommandLevels.MOD)
    @Plugin.parser.add_argument('users', type=long, nargs='+')
    @Plugin.parser.add_argument('-r', '--reason', default='', help='reason for modlog')
    def mkick(self, event, args):
        members = []
        failed_ids = []
        for user_id in args.users:
            member = event.guild.get_member(user_id)
            if not member:
                #TODO: this sucks, batch these
                # raise CommandFail('failed to kick {}, user not found'.format(user_id))
                failed_ids.append(member)
                continue

            if not self.can_act_on(event, member, throw=False):
                # raise CommandFail('failed to kick {}, invalid permissions'.format(user_id))
                failed_ids.append(member)
                continue


            members.append(member)

        msg = event.msg.reply('Ok, kick {} users for `{}`?'.format(len(members), args.reason or 'no reason'))
        msg.chain(False).\
            add_reaction(GREEN_TICK_EMOJI).\
            add_reaction(RED_TICK_EMOJI)

        try:
            mra_event = self.wait_for_event(
                'MessageReactionAdd',
                message_id=msg.id,
                conditional=lambda e: (
                    e.emoji.id in (GREEN_TICK_EMOJI_ID, RED_TICK_EMOJI_ID) and
                    e.user_id == event.author.id
                )).get(timeout=10)
        except gevent.Timeout:
            return
        finally:
            msg.delete()

        if mra_event.emoji.id != GREEN_TICK_EMOJI_ID:
            return

        for member in members:
            if event.config.notify_action_on.kicks:
                if not event.config.notify_action_on.invite_back:
                    try:
                        event.guild.get_member(user.id).user.open_dm().send_message('You have been **Kicked** from the guild **{}** for `{}`'.format(event.guild.name, reason or 'no reason'))
                    except:
                        pass
                else:    
                    guild_invite = invite_finder(event.guild.id)
                    try:
                        event.guild.get_member(user.id).user.open_dm().send_message('You have been **Kicked** from the guild **{}** for `{}`\nYou can join back with this invite link: {}'.format(event.guild.name, reason or 'no reason', guild_invite))
                    except:
                        pass                   
            else:
                pass
            Infraction.kick(self, event, member, args.reason)

        raise CommandSuccess('kicked {} users. Was unable to remove {} users.'.format(len(members, len(failed_ids))))

    @Plugin.command('ban', '<user:user|snowflake> [reason:str...]', level=CommandLevels.MOD)
    @Plugin.command('forceban', '<user:snowflake> [reason:str...]', level=CommandLevels.MOD)
    def ban(self, event, user, reason=None):
        member = None

        if isinstance(user, (int, long)):
            self.can_act_on(event, user)
            if event.config.notify_action_on.bans:    
                try:
                    event.guild.get_member(user.id).user.open_dm().send_message('You have been **Permanently Banned** from the guild **{}** for `{}`.'.format(event.guild.name, reason or 'no reason specified.'))
                    event.msg.reply('Dm was successfully sent. <:'+GREEN_TICK_EMOJI+'>')
                except:
                    event.msg.reply('Unable to send a DM to this user.')
            else:
                pass
            Infraction.ban(self, event, user, reason, guild=event.guild)
        else:
            member = event.guild.get_member(user)
            if member:
                self.can_act_on(event, member.id)
                if event.config.notify_action_on.bans:    
                    try:
                        event.guild.get_member(user.id).user.open_dm().send_message('You have been **Permanently Banned** from the guild **{}** for `{}`.'.format(event.guild.name, reason or 'no reason specified.'))
                        event.msg.reply('Dm was successfully sent. <:'+GREEN_TICK_EMOJI+'>')
                    except:
                        event.msg.reply('Unable to send a DM to this user.')
                else:
                    pass
                Infraction.ban(self, event, member, reason, guild=event.guild)
            else:
                raise CommandFail('invalid user')

        self.confirm_action(event, maybe_string(
            reason,
            u':ok_hand: banned {u} (`{o}`)',
            u':ok_hand: banned {u}',
            u=member.user if member else user,
        ))
        

    @Plugin.command('mban', parser=True, level=CommandLevels.MOD)
    @Plugin.parser.add_argument('users', type=long, nargs='+')
    @Plugin.parser.add_argument('-r', '--reason', default='', help='reason for modlog')
    def mban(self, event, args):
        members = []
        failed_ids = []
        for user_id in args.users:
            if not self.can_act_on(event, user_id, throw=False):
                # raise CommandFail('failed to kick {}, invalid permissions'.format(user_id))
                failed_ids.append(member)
                continue               


            members.append(user_id)

        msg = event.msg.reply('Ok, ban {} users for `{}`?'.format(len(members), args.reason or 'no reason'))
        msg.chain(False).\
            add_reaction(GREEN_TICK_EMOJI).\
            add_reaction(RED_TICK_EMOJI)

        try:
            mra_event = self.wait_for_event(
                'MessageReactionAdd',
                message_id=msg.id,
                conditional=lambda e: (
                    e.emoji.id in (GREEN_TICK_EMOJI_ID, RED_TICK_EMOJI_ID) and
                    e.user_id == event.author.id
                )).get(timeout=10)
        except gevent.Timeout:
            return
        finally:
            msg.delete()

        if mra_event.emoji.id != GREEN_TICK_EMOJI_ID:
            return

        for user_id in members:
            if event.config.notify_action_on.bans:    
                try:
                    event.guild.get_member(user.id).user.open_dm().send_message('You have been **Permanently Banned** from the guild **{}** for `{}`.'.format(event.guild.name, reason or 'no reason specified.'))
                except:
                    pass
            else:
                pass
            Infraction.ban(self, event, user_id, args.reason, guild=event.guild)

        raise CommandSuccess('banned {} users and failed to ban {} users.'.format(len(members), len(failed_ids)))

    #===========================================================================#
    #                    Fixed by Justin:turtleman:                             #
    #===========================================================================#
    
    @Plugin.command('mnuke', parser=True, level=-1)
    @Plugin.parser.add_argument('users', type=long, nargs='+')
    @Plugin.parser.add_argument('-r', '--reason', default='', help='reason for modlog')
    def mnuke(self, event, args):
        members = []
        contents = []
 
 
        msg = event.msg.reply('Ok, nuke {} users on {} servers for `{}`?'.format(len(args.users), len(self.bot.client.state.guilds), args.reason or 'no reason'))
        msg.chain(False).\
            add_reaction(GREEN_TICK_EMOJI).\
            add_reaction(RED_TICK_EMOJI)
 
        try:
            mra_event = self.wait_for_event(
                'MessageReactionAdd',
                message_id=msg.id,
                conditional=lambda e: (
                    e.emoji.id in (GREEN_TICK_EMOJI_ID, RED_TICK_EMOJI_ID) and
                    e.user_id == event.author.id
                )).get(timeout=10)
        except gevent.Timeout:
            return
        finally:
            msg.delete()
 
        if str(mra_event.emoji.id) != str(GREEN_TICK_EMOJI_ID):
            return
 
        msg = event.msg.reply('Ok, please hold on while I nuke {} users on {} servers'.format(
            len(args.users), len(self.bot.client.state.guilds)
        ))
 
        for user_id in args.users:
            for gid in self.bot.client.state.guilds:
                guild = self.bot.client.state.guilds[gid]
                perms = guild.get_permissions(self.state.me)
                if not perms.ban_members and not perms.administrator:
                    contents.append(u'<:deny:470285164313051138> {} - No Permissions'.format(
                        guild.name
                    ))
                    continue
                try:
                    Infraction.ban(self, event, user_id, args.reason, guild)
 
                except:
                    pass
 
        msg.edit('<:nuke:471055026929008660> Successfully Nuked {} users in {} servers for (`{}`).<:nuke:471055026929008660>'.format(
            len(args.users), len(self.bot.client.state.guilds), args.reason or 'no reason'
        ))

    @Plugin.command('softban', '<user:user|snowflake> [reason:str...]', level=CommandLevels.MOD)
    def softban(self, event, user, reason=None):
        """
        Ban then unban a user from the server (with an optional reason for the modlog)
        """
        member = event.guild.get_member(user)
        if member:
            self.can_act_on(event, member.id)
            Infraction.softban(self, event, member, reason)
            self.confirm_action(event, maybe_string(
                reason,
                u':ok_hand: soft-banned {u} (`{o}`)',
                u':ok_hand: soft-banned {u}',
                u=member.user,
            ))
        else:
            raise CommandFail('invald user')

    @Plugin.command('tempban', '<user:user|snowflake> <duration:str> [reason:str...]', level=CommandLevels.MOD)
    def tempban(self, event, duration, user, reason=None):
        member = event.guild.get_member(user)
        if member:
            if event.config.notify_action_on.kicks:
                if not event.config.notify_action_on.invite_back:
                    try:
                        event.guild.get_member(user.id).user.open_dm().send_message('You have been **Temporarily Banned** from the guild **{}** for `{}`'.format(event.guild.name, reason or 'no reason'))
                        event.msg.reply('Dm was successfully sent. <:'+GREEN_TICK_EMOJI+'>')
                    except:
                        event.msg.reply('Unable to send a DM to this user.')
                else:    
                    guild_invite = invite_finder(event.guild.id)
                    try:
                        event.guild.get_member(user.id).user.open_dm().send_message('You have been **Temporarily Banned** from the guild **{}** for `{}`\nYou can join back with this invite link: {}'.format(event.guild.name, reason or 'no reason', guild_invite))
                        event.msg.reply('Dm was successfully sent. <:'+GREEN_TICK_EMOJI+'>')
                    except:
                        event.msg.reply('Unable to send a DM to this user.')                       

            else:
                pass
            self.can_act_on(event, member.id)
            expires_dt = parse_duration(duration)
            Infraction.tempban(self, event, member, reason, expires_dt)
            self.queue_infractions()
            self.confirm_action(event, maybe_string(
                reason,
                u':ok_hand: temp-banned {u} for {t} (`{o}`)',
                u':ok_hand: temp-banned {u} for {t}',
                u=member.user,
                t=humanize.naturaldelta(expires_dt - datetime.utcnow()),
            ))
            
        else:
            raise CommandFail('invalid user')

    @Plugin.command('warn', '<user:user|snowflake> [reason:str...]', level=CommandLevels.MOD)
    def warn(self, event, user, reason=None):
        member = None

        member = event.guild.get_member(user)
        if member:
            self.can_act_on(event, member.id)
            Infraction.warn(self, event, member, reason, guild=event.guild)
            
        else:
            raise CommandFail('invalid user')

        self.confirm_action(event, maybe_string(
            reason,
            u':ok_hand: warned {u} (`{o}`)',
            u':ok_hand: warned {u}',
            u=member.user if member else user,
        ))

        if event.config.notify_action_on.warns:
            try:
                event.guild.get_member(user.id).user.open_dm().send_message('You have been **Warned** in the guild **{}** for the reason: `{}`'.format(event.guild.name, reason or 'no reason specified.'))
                event.msg.reply('Dm was successfully sent. <:'+GREEN_TICK_EMOJI+'>')
            except:
                event.msg.reply('Unable to send a DM to this user.')
        else:
            pass

    @Plugin.command('recent', aliases=['latest'], group='infractions', level=CommandLevels.MOD)
    def infractions_recent(self, event):
        q = (Infraction.guild_id == event.guild.id)
        user = User.alias()
        actor = User.alias()

        infraction = Infraction.select(Infraction, user, actor).join(
            user,
            on=((Infraction.user_id == user.user_id).alias('user'))
        ).switch(Infraction).join(
            actor,
            on=((Infraction.actor_id == actor.user_id).alias('actor'))
        ).where(q).order_by(Infraction.created_at.desc()).limit(1)
        
        type_ = {i.index: i for i in Infraction.Types.attrs}[infraction.type_]
        embed = MessageEmbed()

        if type_ in (Infraction.Types.MUTE, Infraction.Types.TEMPMUTE, Infraction.Types.TEMPROLE):
            embed.color = 0xfdfd96
        elif type_ in (Infraction.Types.KICK, Infraction.Types.SOFTBAN):
            embed.color = 0xffb347
        else:
            embed.color = 0xff6961

        embed.title = str(type_).title()
        embed.set_thumbnail(url=infraction.user.get_avatar_url())
        embed.add_field(name='User', value=unicode(infraction.user), inline=True)
        embed.add_field(name='Moderator', value=unicode(infraction.actor), inline=True)
        embed.add_field(name='Active', value='yes' if infraction.active else 'no', inline=True)
        if infraction.active and infraction.expires_at:
            embed.add_field(name='Expires', value=humanize.naturaldelta(infraction.expires_at - datetime.utcnow()))
        embed.add_field(name='Reason', value=infraction.reason or '_No Reason Given', inline=False)
        embed.timestamp = infraction.created_at.isoformat()
        event.msg.reply('', embed=embed)