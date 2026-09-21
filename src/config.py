import os
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Self

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, model_validator

from mazegen import AlgorithmType


class ConfigError(RuntimeError):
    pass


class DisplayModeType(str, Enum):
    pass


NonNegativeInt = Annotated[int, Field(ge=0)]


class Config(BaseModel):
    width: Annotated[int, Field(ge=11, le=1000)]
    height: Annotated[int, Field(ge=9, le=1000)]
    entry: tuple[NonNegativeInt, NonNegativeInt]
    exit: tuple[NonNegativeInt, NonNegativeInt]
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

    @model_validator(mode="after")
    def check_algorithm(self) -> Self:
        if self.perfect and self.algorithm == AlgorithmType.PACMAN:
            raise ValueError(
                "Incompatible requirements, PACMAN like and pefect maze"
            )
        if not self.perfect and (
            self.algorithm == AlgorithmType.DFS
            or self.algorithm == AlgorithmType.PRIM
        ):
            raise ValueError(
                "Incompatible requirements, " + "DFS"
                if self.algorithm == AlgorithmType.DFS
                else "PRIM" + "and not a perfect maze"
            )
        return self

    @model_validator(mode="after")
    def check_endpoints(self) -> Self:
        if self.entry == self.exit:
            raise ValueError("Entry and exit cannot be the same cell")
        for cell in (self.entry, self.exit):
            if cell[0] >= self.width or cell[1] >= self.height:
                raise ValueError(
                    "Entry"
                    if cell == self.entry
                    else "Exit"
                    + " must have x and y coordinates"
                    + " less than width and height respectively"
                )
        return self


def load_config(config_file: str) -> None:
    path = Path(config_file)

    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")

    if not path.is_file():
        raise ConfigError(f"Configuration path is not a file: {path}")

    try:
        load_dotenv(path)

    except PermissionError as e:
        raise ConfigError(
            f"Cannot read configuration file (permission denied): {path}"
        ) from e
    except UnicodeDecodeError as e:
        raise ConfigError(
            f"Cannot read configuration file (invalid UTF-8): {path}"
        ) from e
    except OSError as e:
        raise ConfigError(
            f"Cannot read configuration file: {path}: {e}"
        ) from e


def get_config(config_file: str) -> Config:
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
    load_dotenv(config_file)
    for key in config_keys:
        config_dic[key.lower()] = os.getenv(key)
        if not config_dic[key.lower()]:
            config_dic[key.lower()] = os.getenv(key.lower())
    config = Config(**config_dic)
    return config
