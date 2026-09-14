from config import get_config
from pydantic import ValidationError
from mazegen import Maze, MazeGenerator
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(message)s | %(filename)s:%(lineno)d",
)
logger = logging.getLogger(__name__)  # cambiar anter de entregar


def gen_output_file(name: str, maze: Maze) -> None:
    with open(name, "w") as f:
        msg = (
            maze.get_bitmap()
            + "\n\n"
            + str(maze.entry[0])
            + ","
            + str(maze.entry[1])
            + "\t\t# entry\t(x,y)\n"
            + str(maze.exit[0])
            + ","
            + str(maze.exit[1])
            + "\t\t# exit\t(x,y)\n"
            + "\n"
            + maze.shortest_path()
            + "\n"
        )
        f.write(msg)


def main() -> int:
    try:
        config = get_config()
        maze_config = config.model_dump(
            include={"width", "height", "entry", "exit"}
        )
        mazegen_config = config.model_dump(
            include={"seed", "perfect", "algorithm"}
        )
        maze = Maze(**maze_config)
        mazegen = MazeGenerator(**mazegen_config)
        mazegen.generate(maze)
        gen_output_file(config.output_file, maze)

    except PermissionError:
        logger.error(
            f"Permission denied to create or modify {config.output_file}"
        )
    except FileNotFoundError:
        logger.error(f"Could not find {config.output_file}")
    except IsADirectoryError:
        logger.error(config.output_file, "is a directory")
    except OSError as e:
        logger.error(f"Error openning file {e}")
    except ValidationError as e:
        logger.error("Invalid configuration:")
        for error in e.errors():
            logger.error(f"  {error['loc'][0]}: {error['msg']}")
    except KeyboardInterrupt:
        logger.info("Process interrupted")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.exception(f"Unexpected error: {e}")
    else:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
