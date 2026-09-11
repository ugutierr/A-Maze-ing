from dotenv import load_dotenv
import os
from pydantic import BaseModel, ValidationError
from typing import Annotated, Any

class AlgorithmType(str, Enum):
    

class DisplayModeType(str, Enum):


class Config(BaseModel):
    width: Annotated[int] # falta maximo/minimo de width
    height: Annotated[int]
    entry: Annotatedo[tuple[int, int]]
    exit: Annotated[tuple[int, int]]
    output_file: Annotated[str]
    perfect: Annotated[bool]
    seed: Annotated[None | str]
    algorithm: AlgorithmType | None
    display_mode: DisplayModeType | None
    
    @field_validator("entry", "exit", mode="before")
    @classmethod
    def parse_point(cls, value: Any) -> Any:
        if isinstance(value, str):
            return tuple(map(int, value.split(",")))
        return value


def main() -> None:
    config_keys = ["WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT",
    "SEED", "ALGORITHM", "DISPLAY_MODE"]
    config_dic = {}
    load_dotenv("config.txt")
    for key in config_keys:
        config[key.lower()] = os.getenv(key)
        if not config[key]:
            config[key] = os.getenv(key.lower())
    try:
        config = Config(config_dic)
    except ValidationError as e:
        for error in e.errors():
            print("Error in configuration field:", error["loc"][0])
            print(error["msg"])




if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted\n Exiting...")
    except Exception:
        print("Unknown error")
