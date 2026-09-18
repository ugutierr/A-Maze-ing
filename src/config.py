from dotenv import load_dotenv
import os
from pydantic import BaseModel, field_validator, Field, model_validator
from typing import Annotated, Any, Self
from enum import Enum
from mazegen import AlgorithmType


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
    load_dotenv("config.example.txt")
    for key in config_keys:
        config_dic[key.lower()] = os.getenv(key)
        if not config_dic[key.lower()]:
            config_dic[key.lower()] = os.getenv(key.lower())
    config = Config(**config_dic)
    return config
