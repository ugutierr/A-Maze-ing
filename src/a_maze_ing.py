from config import get_config
from pydantic import ValidationError
from mazegen import Maze, MazeGenerator


def main() -> int:
    try:
        config = get_config()
        maze_config = config.model_dump(
            exclude={"seed", "perfect", "algorithm", "display_mode"}
        )
        mazegen_config = config.model_dump(
            include={"seed", "perfect", "algorithm"}
        )
        maze = Maze(**maze_config)
        mazegen = MazeGenerator(**mazegen_config)
        mazegen.generate(maze)

    except ValidationError as e:
        print("ERROR: Invalid configuration:")
        for error in e.errors():
            print(f"  {error['loc'][0]}: {error['msg']}")
        return 1
    except KeyboardInterrupt:
        print("\n\nProcess interrupted\n Exiting...")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
