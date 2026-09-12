from config import get_config
from pydantic import ValidationError


def main() -> int:
    try:
        config = get_config()
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


if __name__ == "__main__":
    raise SystemExit(main())
