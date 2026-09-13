from dotenv import load_dotenv
import os
from pydantic import BaseModel, field_validator
from typing import Annotated, Any
from enum import Enum


class ConfigError(Exception):
    pass


class AlgorithmType(str, Enum):
    DFS = "DFS"
    PRIM = "PRIM"


class DisplayModeType(str, Enum):
    pass


class Config(BaseModel):
    width: Annotated[int]  # falta maximo/minimo de width
    height: Annotated[int]
    entry: tuple[int, int]
    exit: tuple[int, int]
    output_file: str
    perfect: bool
    seed: None | str
    algorithm: AlgorithmType | None
    display_mode: DisplayModeType | None

    @field_validator("entry", "exit", mode="before")
    @classmethod
    def parse_point(cls, value: Any) -> Any:
        if isinstance(value, str):
            return tuple(map(int, value.split(",")))
        return value

    @field_validator("algorithm", "display_mode", mode="before")
    @classmethod
    def parse_word(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.upper()
        return value


def get_config() -> Config:
    config_keys = [
        "WIDTH",
        "HEIGHT",
        "ENTRY",
        "EXIT",
        "OUTPUT_FILE",
        "PERFECT",
        "SEED",
        "ALGORITHM",
        "DISPLAY_MODE",
    ]
    config_dic: dict[Any, Any] = {}
    load_dotenv("config.txt")
    for key in config_keys:
        config_dic[key.lower()] = os.getenv(key)
        if not config_dic[key]:
            config_dic[key] = os.getenv(key.lower())
    config = Config(**config_dic)
    return config
