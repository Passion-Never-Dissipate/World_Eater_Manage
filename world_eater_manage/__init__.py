import json
import os
import codecs
import time
import re
import math
import copy

from mcdreforged.api.all import *
from world_eater_manage.config import we_config as we
from world_eater_manage.json_message import Message

Prefix = '!!we'

dim_list = {
    0: "minecraft:overworld",
    -1: "minecraft:the_nether",
    1: "minecraft:the_end"
}

cfg = we.get_default().serialize()

bot_prefix = we.bot_prefix

bot_suffix = we.bot_suffix

gamemode = we.gamemode

y_position = we.y_position

group_name = we.group_name

server_path = we.server_path

max_chunk_length = we.max_chunk_length

user = None

data = []

restart_list = {
    "default": {},
    "manual": {}
}

bot_list = copy.deepcopy(restart_list)


class bot:

    def __init__(self, info, dic):

        if "group" not in dic:
            tag = "default"
            group = self.sort(group_name, tag)

        else:
            tag = "manual"
            for i in dic["group"]:
                if '\u4e00' <= i <= '\u9fff':
                    ServerInterface.get_instance().reply(info, tr("spawn_error.char_error"))
                    return

            group = self.sort(dic["group"], tag)

        if not group:
            ServerInterface.get_instance().reply(info, tr("spawn_error.repeat"))
            return

        try:

            info_ = self.get_pos_list(dic, group)

            if not info_:
                ServerInterface.get_instance().reply(info, tr("limit", max_chunk_length))
                return

            self.info = info_

            if "dim" in dic:
                if not dim_list.get(dic["dim"]):
                    ServerInterface.get_instance().reply(info, tr("spawn_error.dim_error"))
                    return
                self.dim = dim_list.get(dic["dim"])

            else:
                self.dim = dic["data"][-1]

            self.res = False
            self.group = group
            self.tag = tag
            bot_list[self.tag][self.group] = self
            self.spawn()
            ServerInterface.get_instance().reply(info, tr("spawn", self.group))

        except Exception as e:
            ServerInterface.get_instance().reply(info, tr("spawn_error.unknown_error", e))

    def spawn(self):

        for i, j in self.info.items():
            ServerInterface.get_instance().execute(
                tr("spawn_command", i, j[0], y_position, j[1], self.dim, gamemode)
            )
            time.sleep(0.1)

    def kill(self):

        for i in self.info:
            ServerInterface.get_instance().execute(
                tr("kill_command", i)
            )
            time.sleep(0.01)

    def restart(self):
        self.res = True
        restart_list[self.tag][self.group] = self

    @classmethod
    def sort(cls, group, tag):
        if tag == "default":

            if not bot_list["default"]:
                j = 1
                while j:
                    if group + str(j) in bot_list["manual"]:
                        j = j + 1
                        continue
                    return group + str(j)

            lst = sorted([int(i.split(group_name)[-1]) for i in bot_list["default"]])

            j = lst[-1] + 1

            while j:
                if group + str(j) in bot_list["manual"]:
                    j = j + 1
                    continue
                return group + str(j)

        for i in bot_list.values():
            if group in i:
                return
        return group

    @classmethod
    def get_pos_list(cls, dic, group):
        info = {}

        if "data" in dic:
            xc, zc = float(dic['data'][0][0]) // 16, float(dic['data'][0][-1]) // 16
            x1, z1 = xc - dic["r"], zc - dic["r"]
            x2, z2 = xc + dic["r"], zc + dic["r"]

        else:
            x1, z1 = float(dic['x1']) // 16, float(dic['z1']) // 16
            x2, z2 = float(dic['x2']) // 16, float(dic['z2']) // 16

        width = abs(x1 - x2) + 1
        height = abs(z1 - z2) + 1

        if width > max_chunk_length or height > max_chunk_length:
            return

        r = dic["view"]

        size = 2 * r - 1

        width_count, width_remain = math.ceil(
            width / size), width % size if width % size > 0 and width > size else 0
        height_count, height_remain = math.ceil(
            height / size), height % size if height % size > 0 and height > size else 0

        c = 1
        init_z = min(z1, z2) + (r - 1)
        for i, k in enumerate(range(height_count)):
            init_x = max(x1, x2) - (r - 1)
            for j, _ in enumerate(range(width_count)):
                info[bot_prefix + group + "_" + str(c) + bot_suffix] = (init_x * 16 + 8, init_z * 16 + 8)
                c += 1
                if j == 0 and width_remain > 0:
                    init_x -= width_remain
                    continue
                init_x -= size

            if i == 0 and height_remain > 0:
                init_z += height_remain
                continue
            init_z += size

        return info


def tr(key, *args):
    return ServerInterface.get_instance().tr(f"world_eater_manage.{key}", *args)


def print_help_msg(source: CommandSource):
    source.reply(Message.get_json_str(tr("help_message", Prefix, "World_Eater_Manage", "1.0.0")))


@new_thread("we_spawn")
def spawn_bot(source: InfoCommandSource, dic: dict):
    bot(source.get_info(), dic)


@new_thread("we_rspawn")
def rspawn_bot(source: InfoCommandSource, dic: dict):
    global user, data

    if not source.get_info().player:
        source.reply(tr("rspawn_error"))
        return

    user = source.get_info().player

    source.get_server().execute(f"data get entity {user} Pos")
    source.get_server().execute(f"data get entity {user} Dimension")

    t1 = time.time()
    while len(data) < 2:
        if time.time() - t1 > 5:
            user, data = None, []
            source.reply(tr("timeout"))
            return
        time.sleep(0.01)

    user = None

    dic["data"] = data.copy()

    data.clear()

    bot(source.get_info(), dic)


def on_info(server: PluginServerInterface, info: Info):
    if user:
        if info.content.startswith(f"{user} has the following entity data: ") and info.is_from_server:
            raw = info.content.split("entity data: ")[-1]
            if raw.startswith("["):
                data.append([i.strip('d') for i in re.findall(r"[-+]?\d*\.\d+", raw)])

            if raw.startswith('"minecraft:'):
                data.append(raw.replace('"minecraft:', "").strip('"'))


def kill_bot(source: CommandSource, dic: dict):
    group = dic["group"]
    for i in bot_list.values():
        if i.get(group):
            i.get(group).kill()
            try:
                restart_list[i.get(group).tag].pop(group)
            except KeyError:
                pass
            bot_list[i.get(group).tag].pop(group)
            source.reply(tr("kill", group))
            return

    source.reply(tr("kill_error", group))


def restart_bot(source: CommandSource, dic: dict):
    for i in bot_list.values():
        if i.get(dic["group"]):
            if i.get(dic["group"]).res:
                source.reply(tr("restart_error.repeat", dic["group"]))
                return
            i.get(dic["group"]).restart()
            source.reply(tr("restart", dic["group"]))
            return

    source.reply(tr("restart_error.empty", dic["group"]))


def list_bot(source: CommandSource):
    msg = [tr("msg.title")]
    for i in bot_list.values():
        if i:
            for j in i:
                msg.append(tr("list", j))

    if len(msg) > 1:
        source.reply(Message.get_json_str("\n".join(msg)))

    else:
        source.reply(tr("msg.empty"))


def clear_bot(source: CommandSource):
    for i in bot_list.values():
        if i:
            for j in i.values():
                j.kill()

    bot_list.clear()
    restart_list.clear()
    source.reply(tr("clear"))


def reload_plugin(source: CommandSource):
    source.get_server().reload_plugin("world_eater_manage")
    source.reply(tr("reload"))


def on_unload(server: PluginServerInterface):
    global user, data
    user, data = None, []


def on_server_startup(server: PluginServerInterface):
    global bot_list
    bot_list = copy.deepcopy(restart_list)
    for i in bot_list.values():
        if i:
            for j in i.values():
                j.spawn()


def on_load(server: PluginServerInterface, prev_module):
    global cfg, bot_prefix, bot_suffix, y_position, gamemode, group_name, server_path, max_chunk_length, bot_list, restart_list

    if not os.path.exists("./config/world_eater.json"):
        with codecs.open("./config/world_eater.json", "w", encoding="utf-8-sig") as fp:
            json.dump(cfg, fp, ensure_ascii=False, indent=4)

    else:
        with codecs.open("./config/world_eater.json", encoding="utf-8-sig") as fp:
            cfg = json.load(fp)

    if prev_module:
        bot_list = prev_module.bot_list
        restart_list = prev_module.restart_list

    bot_prefix = cfg["bot_prefix"]

    bot_suffix = cfg["bot_suffix"]

    y_position = cfg["y_position"]

    gamemode = cfg["gamemode"]

    group_name = cfg["group_name"]

    server_path = cfg["server_path"]

    max_chunk_length = cfg["max_chunk_length"]

    level_dict = cfg["minimum_permission_level"]

    require = Requirements()

    builder = SimpleCommandBuilder()

    command_literals = [
        "reload",
        "spawn",
        "rspawn",
        "kill",
        "clear",
        "restart",
        "list"
    ]

    server.register_help_message('!!we', tr("register_message"))

    builder.command('!!we', print_help_msg)
    builder.command('!!we reload', reload_plugin)
    builder.command('!!we spawn <x1> <z1> <x2> <z2> <dim> <view> <group>', spawn_bot)
    builder.command('!!we spawn <x1> <z1> <x2> <z2> <dim> <view>', spawn_bot)
    builder.command('!!we rspawn <r> <view> <group>', rspawn_bot)
    builder.command('!!we rspawn <r> <view>', rspawn_bot)
    builder.command('!!we kill <group>', kill_bot)
    builder.command('!!we clear', clear_bot)
    builder.command('!!we restart <group>', restart_bot)
    builder.command('!!we list', list_bot)

    builder.arg('x1', Integer)
    builder.arg('z1', Integer)
    builder.arg('x2', Integer)
    builder.arg('z2', Integer)
    builder.arg('dim', Integer)
    builder.arg('view', Integer)
    builder.arg('group', Text)
    builder.arg('r', Integer)

    for literal in command_literals:
        permission = level_dict[literal]

        builder.literal(literal).requires(
            require.has_permission(permission),
            failure_message_getter=lambda err: tr("lack_permission")
        )

    builder.register(server)
