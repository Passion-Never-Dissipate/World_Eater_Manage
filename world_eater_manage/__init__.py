import os
import time
import re
import math
import copy
import traceback

from mcdreforged.api.all import *
from world_eater_manage.config import we_config as we
from world_eater_manage.json_message import Message
from ruamel.yaml import YAML

Prefix = '!!we'

coding = "utf-8-sig"

cfg_path = os.path.join(".", "config", "world_eater.json")

cfg = we

user = None

data = []

restart_list = {
    "default": {},
    "manual": {}
}

bot_list = copy.deepcopy(restart_list)

'''
ep:
bot_list = {
    "default": {
        "we1": bot:we1 组we1对应的由bot类创建的对象,
        "we2": bot:we2 组we2对应的由bot类创建的对象
    },
    "manual": {
        "load1": bot:load1 组load1对应的由bot类创建的对象,
        "bot1": bot:load1 组bot1对应的由bot类创建的对象
    }
}
restart_list的结构与上例相同
'''


class bot:

    def __init__(self, info, dic):

        if "group" not in dic:
            tag = "default"
            group = self.sort(cfg.group_name, tag)

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
                ServerInterface.get_instance().reply(info, tr("limit", cfg.max_chunk_length))
                return

            self.info = info_

            if "dim" in dic:
                if not cfg.dimension_list.get(str(dic["dim"])):
                    ServerInterface.get_instance().reply(info, tr("spawn_error.dim_error"))
                    return
                self.dim = cfg.dimension_list.get(str(dic["dim"]))

            else:
                self.dim = dic["data"][-1]

            self.res = False
            self.group = group
            self.tag = tag
            self.prefix = cfg.bot_prefix
            self.suffix = cfg.bot_suffix
            bot_list[self.tag][self.group] = self
            self.spawn()
            ServerInterface.get_instance().reply(info, tr("spawn", self.group))

        except Exception:
            ServerInterface.get_instance().reply(info, tr("spawn_error.unknown_error", traceback.format_exc()))

    def spawn(self):

        for i, j in self.info.items():
            ServerInterface.get_instance().execute(
                tr("spawn_command", i, j[0], cfg.y_position, j[1], self.dim, cfg.gamemode)
            )
            time.sleep(0.1)

    def kill(self):

        for i in self.info:
            ServerInterface.get_instance().execute(
                tr(
                    "kill_command", getattr(
                        self, "prefix", cfg.bot_prefix) + i + getattr(
                        self, "suffix", cfg.bot_suffix
                    )
                )
            )
            time.sleep(0.05)

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

            lst = sorted([int(i.split(we.group_name)[-1]) for i in bot_list["default"]])

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

        if width > cfg.max_chunk_length or height > cfg.max_chunk_length:
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
                info[group + "_" + str(c)] = (init_x * 16 + 8, init_z * 16 + 8)
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

    @classmethod
    def is_empty(cls, bot_list_):
        return not (bot_list_.get("default") or bot_list_.get("manual"))


def tr(key, *args):
    return ServerInterface.get_instance().tr(f"world_eater_manage.{key}", *args)


def print_help_msg(source: CommandSource):
    source.reply(Message.get_json_str(tr("help_message", Prefix, "World_Eater_Manage", "1.4.1")))


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
            if len(data) < 1:
                data.append([i.strip('d') for i in re.findall(r"[-+]?\d*\.\d+", raw)])
                return
            data.append(raw.strip('"'))


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
    if get_fpr_status():
        ServerInterface.get_instance().broadcast(tr("restart_error.fpr_enabled"))
        return

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
    for g in bot_list.values():
        for k, v in g.items():
            if v.res:
                msg.append(tr("list_restart", k))
                continue
            msg.append(tr("list_normal", k))

    if len(msg) > 1:
        source.reply(Message.get_json_str("\n".join(msg)))

    else:
        source.reply(tr("msg.empty"))


def clear_bot(source: CommandSource):
    global restart_list, bot_list
    for i in bot_list.values():
        for j in i.values():
            j.kill()

    restart_list = {
        "default": {},
        "manual": {}
    }

    bot_list = copy.deepcopy(restart_list)

    source.reply(tr("clear"))


def reload_plugin(source: CommandSource):
    source.get_server().reload_plugin("world_eater_manage")
    source.reply(tr("reload"))


def on_unload(server: PluginServerInterface):
    global user, data
    user, data = None, []


def on_server_startup(server: PluginServerInterface):
    global bot_list, restart_list
    if get_fpr_status() and not bot.is_empty(restart_list):
        restart_list = {
            "default": {},
            "manual": {}
        }
        bot_list = copy.deepcopy(restart_list)
        ServerInterface.get_instance().broadcast(tr("restart_error.fpr_enabled"))
        return

    bot_list = copy.deepcopy(restart_list)

    for i in bot_list.values():
        for j in i.values():
            j.spawn()


def on_load(server: PluginServerInterface, prev_module):
    global cfg, bot_list, restart_list

    if not os.path.exists(cfg_path):
        ServerInterface.get_instance().as_plugin_server_interface().save_config_simple(
            config=we.get_default(),
            file_name=cfg_path,
            in_data_folder=False,
            encoding=coding
        )

    cfg = ServerInterface.get_instance().as_plugin_server_interface().load_config_simple(
        file_name=cfg_path,
        in_data_folder=False,
        encoding=coding,
        target_class=we
    )

    if prev_module:
        bot_list = prev_module.bot_list
        restart_list = prev_module.restart_list

    level_dict = cfg.minimum_permission_level

    require = Requirements()

    builder = SimpleCommandBuilder()

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

    for literal in level_dict:
        permission = level_dict[literal]

        builder.literal(literal).requires(
            require.has_permission(permission),
            failure_message_getter=lambda err: tr("lack_permission")
        )

    builder.register(server)


def get_server_folder_name(file_path):
    yaml = YAML()
    with open(file_path, 'r', encoding='utf-8') as file:
        config = yaml.load(file)
    try:
        server_name = config['working_directory']
        return server_name
    except Exception:
        # print(f"Key error: {e}. Make sure the key exists in the YAML file.")
        return None


def get_level_name(file_path, key_target):
    properties = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if line.startswith('#') or not line.strip():
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            properties[key] = value
    level_name = properties.get(key_target)
    return level_name


def get_fpr_status():
    mcdr_config_path = './config.yml'
    server_name = get_server_folder_name(mcdr_config_path)

    if server_name is None:
        return

    properties_path = f'./{server_name}/server.properties'
    level_name = get_level_name(properties_path, "level-name")

    if not level_name:
        return

    carpet_conf_path = f'./{server_name}/{level_name}/carpet.conf'

    # FPR:FakePlayerResidence of Gugle Carpet Addition, which is not compatible with rspawn function of WE.
    try:
        carpet_conf = {}
        with open(carpet_conf_path, 'r', encoding='utf-8') as file:
            for line in file:
                if line.startswith('#') or not line.strip():
                    continue
                key, value = line.split(None, 1)
                key = key.strip()
                value = value.strip()
                carpet_conf[key] = value

        fpr_status = carpet_conf.get("fakePlayerResident")
        bool_map = {"true": True, "false": False}
        if fpr_status in bool_map:
            return bool_map[fpr_status]
    except Exception:
        return None
