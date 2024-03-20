import json
import os
import codecs

from mcdreforged.api.all import *

bots_list = {}

Prefix = '!!we'
help_msg = '''
------ {1} {2} ------
一款专为技术生存服务器设计的世吞运维插件
§3作者：Bexerlmao, FRUIT_CANDY
§d【格式说明】
!!we 查看帮助信息
!!we bot spawn <x1> <z1> <x2> <z2> <维度:0主世界,-1地狱,1末地> <服务器视距> <假人名> 坐标所围成的空置域生成一个世吞假人组假人
!!we kill <假人名> 删除该组假人并使其退出游戏
!!we restart <假人名> 使该组假人在服务器重启后自动生成
!!we list 查看正在运行的世吞假人组
'''.format(Prefix, "World_Eater_Manage", "1.0.0")


def print_help_msg(source: CommandSource):
    source.reply(help_msg)


def spawn_bot(source: CommandSource, dic: dict):
    botid = 0
    bots_list[dic['name']] = {}
    source.get_server().execute(f"/say {botid}")
    if dic['x2'] < dic['x1']:
        dic['x2'], dic['x1'] = dic['x1'], dic['x2']
    if dic['z2'] < dic['z1']:
        dic['z2'], dic['z1'] = dic['z1'], dic['z2']
    for xpos in range(conversion_chunk(dic['x1']), conversion_chunk(dic['x2']), dic['view'] + 1):
        for zpos in range(conversion_chunk(dic['z1']), conversion_chunk(dic['z2']), dic['view'] + 1):
            source.get_server().execute(f"/player {dic['name']} spawn at {conversion_pos(xpos)} 100 {conversion_pos(zpos)} facing 0 0 in minecraft:overworld in spectator")
            botid = botid + 1
            bots_list[dic['name']][f"{dic['name']}{botid}"] = (xpos, zpos)
    if botid == 0:
        x = conversion_pos(dic['x1']) + abs(dic['x1'] - dic['x2']) / 2
        z = conversion_pos(dic['z1']) + abs(dic['z1'] - dic['z2']) / 2
        source.get_server().execute(f"/say {x} {z} {abs(dic['x1'] - dic['x2'])} ")
        source.get_server().execute(f"/player {dic['name']} spawn at {x} 100 {z} facing 0 0 in minecraft:overworld in spectator")
        botid = botid + 1
        bots_list[dic['name']][f"{dic['name']}{botid}"] = (x, z)

    source.get_server().execute(f"/say 成功生成{botid}个假人")
def kill_bot(source: CommandSource, dic: dict):
    pass

def restart_bot(source: CommandSource, dic: dict):
    pass

def list_bot(source: CommandSource, dic: dict):
    pass

def reload_plugin(source: CommandSource):
    source.get_server().reload_plugin("world_eater_manage")
    source.reply("§a§l插件已重载")

def on_load(server: PluginServerInterface, prev: PluginServerInterface):
    builder = SimpleCommandBuilder()

    builder.command('!!we', print_help_msg)
    builder.command('!!we reload', reload_plugin)
    builder.command('!!we spawn <x1> <z1> <x2> <z2> <dim> <view> <name>', spawn_bot)
    builder.command('!!we kill <name>', kill_bot)
    builder.command('!!we restart <name>', restart_bot)
    builder.command('!!we list', list_bot)

    builder.arg('x1', Integer)
    builder.arg('z1', Integer)
    builder.arg('x2', Integer)
    builder.arg('z2', Integer)
    builder.arg('dim', Integer)
    builder.arg('view', Integer)
    builder.arg('name', Text)

    builder.register(server)

def conversion_chunk(pos:Integer):
    return pos//16

def conversion_pos(chunk:Integer):
    return chunk*16 + 8

