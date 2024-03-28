from mcdreforged.api.utils.serializer import Serializable
from typing import Dict


class we_config(Serializable):
    bot_prefix: str = ""
    bot_suffix: str = ""
    y_position: int = 128
    gamemode: str = "spectator"
    group_name: str = "we"
    server_path: str = "./server"
    minimum_permission_level: Dict[str, int] = {
        "spawn": 1,
        "rspawn": 1,
        "kill": 1,
        "restart": 1,
        "reload": 2,
        "list": 0
    }

