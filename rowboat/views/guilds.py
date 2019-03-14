# -*- coding: utf-8 -*-
import yaml
import json
import functools
import operator
import emoji
import disco
import requests
import psycopg2
import flask

from flask.json import jsonify
from flask import Blueprint, g, make_response, request
from emoji.unicode_codes import UNICODE_EMOJI
from rowboat.util.decos import authed
from rowboat.models.guild import Guild, GuildConfigChange, GuildEmoji
from rowboat.models.user import User, Infraction
from rowboat.models.message import Message, Command
from rowboat.sql import database
from rowboat.redis import rdb
from rowboat.constants import ROWBOAT_LOG_CHANNEL

guilds = Blueprint('guilds', __name__, url_prefix='/api/guilds')

with open('config.yaml', 'r') as config:
    cfg = yaml.load(config)

API_TOKEN = cfg['token']

def serialize_user(u):
    return {
        'user_id': str(u.user_id),
        'username': u.username,
        'discriminator': u.discriminator,
    }


def with_guild(f=None):
    def deco(f):
        @authed
        @functools.wraps(f)
        def func(*args, **kwargs):
            try:
                if g.user.admin:
                    guild = Guild.select().where(Guild.guild_id == kwargs.pop('gid')).get()
                    guild.role = 'admin'
                else:
                    guild = Guild.select(
                        Guild,
                        Guild.config['web'][str(g.user.user_id)].alias('role')
                    ).where(
                        (Guild.guild_id == kwargs.pop('gid')) &
                        (~(Guild.config['web'][str(g.user.user_id)] >> None))
                    ).get()

                return f(guild, *args, **kwargs)
            except Guild.DoesNotExist:
                return 'Invalid Guild', 404
        return func

    if f and callable(f):
        return deco(f)

    return deco


@guilds.route('/<gid>')
@with_guild
def guild_get(guild):
    return jsonify(guild.serialize())


@guilds.route('/<gid>/config')
@with_guild
def guild_config(guild):
    return jsonify({
        'contents': unicode(guild.config_raw) if guild.config_raw else yaml.safe_dump(guild.config),
    })


@guilds.route('/<gid>/config', methods=['POST'])
@with_guild
def guild_z_config_update(guild):
    if guild.role not in ['admin', 'editor']:
        return 'Missing Permissions', 403

    # Calculate users diff
    try:
        data = yaml.load(request.json['config'])
    except:
        return 'Invalid YAML', 400

    before = sorted(guild.config.get('web', {}).items(), key=lambda i: i[0])
    after = sorted([(str(k), v) for k, v in data.get('web', {}).items()], key=lambda i: i[0])

    if guild.role != 'admin' and before != after:
        return 'Invalid Access', 403

    role = data.get('web', {}).get(g.user.user_id) or data.get('web', {}).get(str(g.user.user_id))
    if guild.role != role and not g.user.admin:
        print g.user.admin
        return 'Cannot change your own permissions', 400

    try:
        guild.update_config(g.user.user_id, request.json['config'])
        return '', 200
    except Guild.DoesNotExist:
        return 'Invalid Guild', 404
    except Exception as e:
        return 'Invalid Data: %s' % e, 400


CAN_FILTER = ['id', 'user_id', 'actor_id', 'type', 'reason']
CAN_SORT = ['id', 'user_id', 'actor_id', 'created_at', 'expires_at', 'type']


@guilds.route('/<gid>/infractions')
@with_guild
def guild_infractions(guild):
    user = User.alias()
    actor = User.alias()

    page = int(request.values.get('page', 1))
    if page < 1:
        page = 1

    limit = int(request.values.get('limit', 1000))
    if limit < 1 or limit > 1000:
        limit = 1000

    q = Infraction.select(Infraction, user, actor).join(
        user,
        on=((Infraction.user_id == user.user_id).alias('user'))
    ).switch(Infraction).join(
        actor,
        on=((Infraction.actor_id == actor.user_id).alias('actor'))
    )

    queries = []
    if 'filtered' in request.values:
        filters = json.loads(request.values['filtered'])

        for f in filters:
            if f['id'] not in CAN_FILTER:
                continue

            if f['id'] == 'type':
                queries.append(Infraction.type_ == Infraction.Types.get(f['value']))
            elif f['id'] == 'reason':
                queries.append(Infraction.reason ** ('%' + f['value'].lower().replace('%', '') + '%'))
            elif f['id'] == 'user':
                queries.append(Infraction.user_id.in_(search_users(f['value'])))
            elif f['id'] == 'actor':
                queries.append(Infraction.actor_id.in_(search_users(f['value'])))
            else:
                queries.append(getattr(Infraction, f['id']) == f['value'])

    if queries:
        q = q.where(
            (Infraction.guild_id == guild.guild_id) &
            reduce(operator.and_, queries)
        )
    else:
        q = q.where((Infraction.guild_id == guild.guild_id))

    sorted_fields = []
    if 'sorted' in request.values:
        sort = json.loads(request.values['sorted'])

        for s in sort:
            if s['id'] not in CAN_SORT:
                continue

            if s['desc']:
                sorted_fields.append(
                    getattr(Infraction, s['id']).desc()
                )
            else:
                sorted_fields.append(
                    getattr(Infraction, s['id'])
                )

    results = {
        "pages": len(q) // limit,
        "infractions": []
    }

    if sorted_fields:
        q = q.order_by(*sorted_fields)
    else:
        q = q.order_by(Infraction.id.desc())

    q = q.paginate(
        page,
        limit,
    )

    results["infractions"] = [i.serialize(guild=guild, user=i.user, actor=i.actor) for i in q]

    return jsonify(results)


@guilds.route('/<gid>/config/history')
@with_guild
def guild_config_history(guild):
    def serialize(gcc):
        return {
            'user': serialize_user(gcc.user_id),
            'before': unicode(gcc.before_raw),
            'after': unicode(gcc.after_raw),
            'created_at': gcc.created_at.isoformat(),
        }

    q = GuildConfigChange.select(GuildConfigChange, User).join(
        User, on=(User.user_id == GuildConfigChange.user_id),
    ).where(GuildConfigChange.guild_id == guild.guild_id).order_by(
        GuildConfigChange.created_at.desc()
    ).paginate(int(request.values.get('page', 1)), 5)

    return jsonify(map(serialize, q))


@guilds.route('/<gid>/stats/messages', methods=['GET'])
@with_guild()
def guild_stats_messages(guild):
    def serialize(gcc):
        return {
            "day": gcc[0],
            "count": int(gcc[1]),
        }

    unit = request.values.get('unit', 'days')
    amount = int(request.values.get('amount', 7))

    sql = '''
        SELECT date, coalesce(count, 0) AS count
        FROM
            generate_series(
                NOW() - interval %s,
                NOW(),
                %s
            ) AS date
        LEFT OUTER JOIN (
            SELECT date_trunc(%s, timestamp) AS dt, count(*) AS count
            FROM messages
            WHERE
                timestamp >= (NOW() - interval %s) AND
                timestamp < (NOW()) AND
                guild_id=%s
            GROUP BY dt
        ) results
        ON (date_trunc(%s, date) = results.dt);
    '''

    tuples = list(Message.raw(
        sql,
        '{} {}'.format(amount, unit),
        '1 {}'.format(unit),
        unit,
        '{} {}'.format(amount, unit),
        guild.guild_id,
        unit
    ).tuples())

    return jsonify(map(serialize, tuples))

@guilds.route('/<gid>/stats', methods=['GET'])
@with_guild()
def guild_stats_self(guild):
    def serialize_user(gcc):
        for i in gcc:
            user_raw = '''
                SELECT username, discriminator
                FROM users
                WHERE
                    user_id=%s AND
                    bot=false;
            '''

            user = list(User.raw(
                user_raw,
                i[1]
                ).tuples())

            if user:
                return {
                    'user': {
                        'username': user[0][0],
                        'discrim': str(user[0][1]),
                        'id': i[1]
                    },
                    'user_count': int(i[0]),
                }

        return {
            'user': 'N/A',
            'user_count': 0,
        }

    def serialize_emoji(gcc):
        for i in gcc:
            emoji_raw = '''
                SELECT emoji_id
                FROM guild_emojis
                WHERE
                    emoji_id=%s AND
                    guild_id=%s;
            '''

            emoji = list(GuildEmoji.raw(
                emoji_raw,
                i[0],
                guild.guild_id
                ).tuples())

            if emoji:
                return str(emoji[0][0])

        return '230870076126003200'

    data = json.loads(rdb.get('web:guild:{}:stats'.format(guild.guild_id)) or '{}')

    if not data:
        # Totals
        totals_messages = Message.select(Message.id).where(
            (Message.guild_id==guild.guild_id)
            ).count()

        totals_infractions = Infraction.select(Infraction.id).where(
            (Infraction.guild_id==guild.guild_id)
            ).count()

        # Peaks
        ## Messages
        peaks_messages_raw = '''
            SELECT count(id), author_id
            FROM
                messages
            WHERE
                guild_id=%s
            GROUP BY author_id
            ORDER BY count DESC
            LIMIT 5;
        '''

        peaks_messages = list(Message.raw(
            peaks_messages_raw,
            guild.guild_id
        ).tuples())

        ## Infractions
        peaks_infractions_raw = '''
            SELECT count(id), user_id
            FROM
                infractions
            WHERE
                guild_id=%s
            GROUP BY user_id
            ORDER BY count DESC
            LIMIT 5;
        '''

        peaks_infractions = list(Infraction.raw(
            peaks_infractions_raw,
            guild.guild_id
        ).tuples())

        ## Emoji
        peaks_emoji_raw = '''
            SELECT id, count(*)
            FROM (
                SELECT unnest(emojis) as id
                FROM messages
                WHERE guild_id=%s and
                cardinality(emojis) > 0
            ) q
            GROUP BY 1
            ORDER BY 2 DESC
            LIMIT 5
        '''

        peaks_emoji = list(Message.raw(
            peaks_emoji_raw,
            guild.guild_id
        ).tuples())

        ## Command
        peaks_command_raw = '''
            SELECT count(c.command), c.command
            FROM
                commands c
            INNER JOIN messages m
            ON (c.message_id = m.id)
            WHERE
                m.guild_id=%s
            GROUP BY 2
            ORDER BY 1 DESC
            LIMIT 1;
        '''

        peaks_command = list(Command.raw(
            peaks_command_raw,
            guild.guild_id
        ).tuples())

        if totals_messages:
            totals_messages = totals_messages
        else:
            totals_messages = 0

        if totals_infractions:
            totals_infractions = totals_infractions
        else:
            totals_infractions = 0

        if peaks_messages:
            pm = serialize_user(peaks_messages)
        else:
            pm = {
                'user': 'N/A',
                'user_count': 0,
            }

        if peaks_infractions:
            pi = serialize_user(peaks_infractions)
        else:
            pi = {
                'user': 'N/A',
                'user_count': 0,
            }

        if peaks_emoji:
            anim = False

            peaks_emoji_id = serialize_emoji(peaks_emoji)
            url = 'https://discordapp.com/api/emojis/{}.gif'.format(peaks_emoji_id)
            r = requests.get(url)
            try:
                r.raise_for_status()
                anim = True
            except requests.HTTPError:
                pass

            if anim:
                peaks_emoji_ext = 'gif'
            else:
                peaks_emoji_ext = 'png'
        else:
            peaks_emoji_id = '230870076126003200'
            peaks_emoji_ext = 'png'

        if peaks_command:
            peaks_command = '{1}'.format(*peaks_command[0])
        else:
            peaks_command = 'N/A'

        data = {'totals': {
              'messages': totals_messages,
              'infractions': totals_infractions,
            },
            'peaks': {
              'messages': pm,
              'infractions': pi,
              'emoji': {
                'id': peaks_emoji_id,
                'ext': peaks_emoji_ext,
              },
              'command': peaks_command,
            },
          }
        rdb.setex('web:guild:{}:stats'.format(guild.guild_id), json.dumps(data), 600)

    return jsonify(data)

@guilds.route('/<gid>/premium/enable', methods=['POST'])
@with_guild()
def guild_premium_enable(guild):
    if not g.user.admin:
        return '', 401
    guild.update_premium(True)
    return 'Premium has been enabled.', 200

@guilds.route('/<gid>/premium/disable', methods=['DELETE'])
@with_guild()
def guild_premium_disable(guild):
    if not g.user.admin:
        return '', 401
    guild.update_premium(False)
    return 'Premium has been disabled', 200

@guilds.route('/<gid>', methods=['DELETE'])
@with_guild
def guild_delete(guild):
    if not g.user.admin:
        return '', 401

    guild.emit('GUILD_DELETE')
    conn = database.obj.get_conn()
    curRemove = conn.cursor()
    curConfig = conn.cursor()
    try:
        curConfig.execute("SELECT config_raw FROM guilds WHERE guild_id={}".format(guild.guild_id))
        rawConfig = curConfig.fetchone()[0]
        send_guildMessage(rawConfig, guild.guild_id, guild.owner_id, guild.name, guild.icon)
        curRemove.execute("DELETE FROM guilds WHERE guild_id={}".format(guild.guild_id))
        conn.commit()
    except:
        pass
    return '', 204


def getuser(id):
    url = "https://discordapp.com/api/v6/users/{}".format(id)
    headers = {'user-agent': 'Airplane (aetherya.stream, null)', 'Authorization': 'Bot {}'.format(API_TOKEN)}
    r = requests.get(url, headers=headers)
    username = r.json()['username']
    discriminator = r.json()['discriminator']
    if len(str(discriminator)) is 1:
        discriminator = '000' + discriminator
    elif len(str(discriminator)) is 2:
        discriminator = '00' + discriminator
    elif len(str(discriminator)) is 3:
        discriminator = '0' + discriminator

    fullUser = username + '#' + discriminator
    return fullUser

def send_guildMessage(raw_config, guildID, ownerID, name, Picurl):
    url = "https://discordapp.com/api/v7/channels/{}/messages".format(ROWBOAT_LOG_CHANNEL)
    headers = {'user-agent': 'Airplane (aetherya.stream, null)', 'Authorization': 'Bot {}'.format(API_TOKEN)}
    headers2 = {'user-agent': 'Airplane (aetherya.stream, null)', 'Authorization': 'Bot {}'.format(API_TOKEN), 'Content-Type': 'application/json'}
    FILES = {'Config-{}.yaml'.format(guildID): str(raw_config)}
    if Picurl is None:
        Picurl = "https://discordapp.com/assets/e05ead6e6ebc08df9291738d0aa6986d.png"
    else:
        Picurl = 'https://cdn.discordapp.com/icons/{}/{}.png'.format(guildID, Picurl)
    DATA = json.dumps({
        'embed': {
            "color": 9766889,
            "thumbnail": {
            "url": "{}".format(Picurl)
            },
            "author": {
            "name": "Server Forced Removed"
            },
            "fields": [
            {
                "name": "Server:",
                "value": "`{}` ({})".format(unicode(name).encode('utf-8'), guildID)
            },
            {
                "name": "Owner:",
                "value": "`{}` ({})".format(unicode(getuser(ownerID)).encode('utf-8'), ownerID)
            }
            ]
        }
    })
    r = requests.post(url, headers=headers2, data=DATA)
    requests.post(url, headers=headers, files=FILES)