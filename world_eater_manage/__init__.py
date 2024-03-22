import json
import os
import codecs
import time

from mcdreforged.api.all import *

bots_list = {}
bots_restart_list = []
pos3d = []
dimension = None
time_out = 5
USER = None

Prefix = '!!we'
help_msg = '''
------ {1} {2} ------
一款专为技术生存服务器设计的世吞运维插件
§3作者：Bexerlmao, FRUIT_CANDY
§d【格式说明】
!!we 查看帮助信息
!!we spawn <x1> <z1> <x2> <z2> <维度:0主世界,-1地狱,1末地> <服务器视距> <假人名> 坐标所围成的空置域生成假人
!!we spawn <半径> <假人名> 以玩家为中心的半径内生成假人
!!we kill <假人名> 删除该组假人并使其退出游戏
!!we restart <假人名> 使该组假人在服务器重启后自动生成
!!we list 查看正在运行的世吞假人组
'''.format(Prefix, "World_Eater_Manage", "1.0.0")


def print_help_msg(source: CommandSource):
    source.reply(help_msg)


def conversion_chunk(pos):
    return pos//16

def conversion_pos(chunk):
    return chunk*16

def spawn_bot(source: CommandSource, dic: dict):

    if 'name' not in dic:
        value = 1
        while bots_list.get(f"w{value}", False):
            value = value + 1
            dic['name'] = f'w{value}'

    if dic['name'] in bots_list:
        source.reply(f"{dic['name']}已存在")
        return

    botid = 0
    bots_list[dic['name']] = {}

    if dic['x2'] < dic['x1']:
        dic['x2'], dic['x1'] = dic['x1'], dic['x2']
    if dic['z2'] < dic['z1']:
        dic['z2'], dic['z1'] = dic['z1'], dic['z2']


    if abs(dic['x1'] - dic['x2']) <= dic['view'] * 2 + 1 and abs(dic['z1'] - dic['z2']) <= dic['view'] * 2 + 1:
        x = conversion_pos(dic['x1']) + abs(dic['x1'] - dic['x2']) // 2
        z = conversion_pos(dic['z1']) + abs(dic['z1'] - dic['z2']) // 2
        botid = botid + 1
        source.get_server().execute(f"/player {dic['name']}_{botid} spawn at {x} 100 {z} facing 0 0 in minecraft:{dimension} in spectator")
        bots_list[dic['name']][f"{dic['name']}_{botid}"] = (x, z)
    else:
        botid = botid + 1
        source.get_server().execute(
            f"/player {dic['name']}_{botid} spawn at {dic['x1'] + dic['view'] + 1} 100 {dic['z1'] + dic['view'] + 1} facing 0 0 in minecraft:{dimension} in spectator")
        bots_list[dic['name']][f"{dic['name']}_{botid}"] = (dic['x1'] + dic['view'] + 1, dic['z1'] + dic['view'] + 1)
        for xpos in range(conversion_chunk(dic['x1']) + dic['view'], conversion_chunk(dic['x2']), dic['view'] * 2 + 1):
            for zpos in range(conversion_chunk(dic['z1']) - dic['view'], conversion_chunk(dic['z2']), dic['view'] * 2 + 1):
                botid = botid + 1
                source.get_server().execute(f"/player {dic['name']}_{botid} spawn at {conversion_pos(xpos)} 100 {conversion_pos(zpos)} facing 0 0 in minecraft:{dimension} in spectator")
                bots_list[dic['name']][f"{dic['name']}_{botid}"] = (xpos, zpos)



    source.reply(f"成功生成{botid}个假人")

@new_thread("rspawn_bot")
def rspawn_bot(source: CommandSource, dic: dict):
    global pos3d, dimension

    if 'name' not in dic:
        value = 1
        while bots_list.get(f"w{value}", False):
            value = value + 1
            dic['name'] = f'w{value}'

    if dic['r'] < 0:
        source.reply("半径应为大于等于0的整数!")
        return

    if source.get_info().player:
        source.reply("正在获取玩家坐标")
        source.get_server().execute(f"data get entity {source.get_info().player} Dimension")
        source.get_server().execute(f"data get entity {source.get_info().player} Pos")

    t1 = time.time()
    while not pos3d and not dimension:
        time.sleep(0.1)
        if time.time() - t1 > time_out:
            source.reply("获取玩家坐标超时")
            return


        source.get_server().logger.info(pos3d)
        source.get_server().logger.info(dimension)

        user_xpos = conversion_chunk(int(float(pos3d[0])))
        user_zpos = conversion_chunk(int(float(pos3d[2])))

        dic['x1'] = conversion_pos(user_xpos - dic['r'])
        dic['x2'] = conversion_pos(user_xpos + dic['r'])
        dic['z1'] = conversion_pos(user_zpos - dic['r'])
        dic['z2'] = conversion_pos(user_zpos + dic['r'])
        dic['dim'] = dimension

    spawn_bot(source, dic)

@new_thread("get_info")
def on_info(server: PluginServerInterface, info: Info):
    global pos3d, dimension
    if info.content.count("has the following entity data: ") and info.is_from_server:

        if len(info.content.split(" ")) == 9:
            pos3d = [pos.rstrip('d').strip() for pos in info.content.split(":")[-1][2: -1].split(",")]
            return

        if info.content.split(":")[-1][0: -1] == "overworld" or "the_nether" or "the_end":
            dimension = info.content.split(":")[-1][0: -1]


def kill_bot(source: CommandSource, dic: dict):
    for bot in bots_list[dic['name']]:
        source.get_server().execute(f"/player {bot} kill")
    del bots_list[dic['name']]
    bots_restart_list.remove(dic['name'])

def restart_bot(source: CommandSource, dic: dict):
    try:
        bots_list[dic['name']]
        bots_restart_list.append(dic['name'])
        source.reply(f"添加{dic['name']}至重启列表")
    except:
        source.reply(f"{dic['name']}不存在")

def list_bot(source: CommandSource, dic: dict):
    source.reply(f"正在运行的世吞假人组: {bots_list.keys()}")

def reload_plugin(source: CommandSource):
    source.get_server().reload_plugin("world_eater_manage")
    source.reply("§a§l插件已重载")

def on_load(server: PluginServerInterface, prev: PluginServerInterface):

    for index in bots_restart_list:
        for bot in bots_list[index]:
            server.execute(f"/player {bot} spawn at {bots_list[index][bot][0]} 100 {bots_list[index][bot][1]} facing 0 0 in minecraft:overworld in spectator")

    builder = SimpleCommandBuilder()

    builder.command('!!we', print_help_msg)
    builder.command('!!we reload', reload_plugin)
    builder.command('!!we spawn <x1> <z1> <x2> <z2> <dim> <view> <name>', spawn_bot)
    builder.command('!!we spawn <x1> <z1> <x2> <z2> <dim> <view>', spawn_bot)
    builder.command('!!we rspawn <r> <view> <name>', rspawn_bot)
    builder.command('!!we rspawn <r> <view>', rspawn_bot)
    builder.command('!!we kill <name>', kill_bot)
    builder.command('!!we restart <name>', restart_bot)
    builder.command('!!we list', list_bot)

    builder.arg('x1', Integer)
    builder.arg('z1', Integer)
    builder.arg('x2', Integer)
    builder.arg('z2', Integer)
    builder.arg('dim', Text)
    builder.arg('view', Integer)
    builder.arg('name', Text)
    builder.arg('r', Integer)

    builder.register(server)



