"""Render the A-maze-ing maze interface with MiniLibX."""

import math
from pathlib import Path
from time import sleep
from typing import Literal

from mazegen import Maze, MazeGenerator
from mlx import Mlx
from .animation import MazeAnimation
from .bitmapfont import draw_text
from .framebuffer import Surface
from config import Config


ASSETS_DIR: Path = Path(__file__).resolve().parents[2] / "assets"


class Window:
    """Manage the MiniLibX window and render an interactive maze.

    The class owns the maze display, textures resources, layout calculations,
    drawing routines, and keyboard/window event handlers.
    """
    ESC_KEYCODE: int = 65307
    REGENERATE_KEYCODE: int = 114
    PATH_KEYCODE: int = 112
    THEME_KEYCODE: int = 99
    ANIMATE_KEYCODE: int = 97
    CLOSE_EVENT: int = 33

    TEXT_COLOR: int = 0xFFFFFF

    # Each theme has independent colors for the floor, walls, 42 logo,
    # outer border, and side panel. None preserves the original texture.
    THEME_NAMES: tuple[str, ...] = ("Classic", "Fire", "Ocean", "Cyber")
    THEMES: dict[str, dict[str, int | None]] = {
        "Classic": {
            "floor": None,
            "wall": None,
            "logo42": None,
            "border": None,
            "panel": 0xC9B47A,
        },
        "Fire": {
            "floor": 0xE85602,
            "wall": 0x262D29,
            "logo42": 0xF5A16D,
            "border": 0xF03B1A,
            "panel": 0xFF4C00,
        },
        "Ocean": {
            "floor": 0x75C5D9,
            "wall": 0x0D3DDF,
            "logo42": 0xB8C6FF,
            "border": 0x0D3DDF,
            "panel": 0x8AA1FF,
        },
        "Cyber": {
            "floor": 0x27F5EB,
            "wall": 0xC809C8,
            "logo42": 0xE46CFF,
            "border": 0x7F00B2,
            "panel": 0xFF8AC0,
        },
    }

    REFERENCE_SCREEN_WIDTH: int = 1920
    REFERENCE_SCREEN_HEIGHT: int = 1080
    REFERENCE_WINDOW_WIDTH: int = 1200
    GOLDEN_RATIO: float = (1 + math.sqrt(5)) / 2

    WALL_REFERENCE_CELL_SIZE: float = 64.0
    WALL_REFERENCE_WIDTH: int = 6

    PANEL_REFERENCE_HEIGHT: float = 742.0
    PANEL_GRAPHIC_TOP_MARGIN: int = 15
    PANEL_GRAPHIC_LEFT_MARGIN: int = 15
    PANEL_DOG_AREA_SIZE: int = 145
    ASSET_SCALE: float = 2.0

    def __init__(
        self,
        title: str,
        maze: Maze,
        generator: MazeGenerator,
        config: Config,
    ) -> None:
        """Initialize the graphics window and prepare the maze display.

        Args:
            title: Text shown in the window title bar.
            maze: Maze instance to display
            generator: Generator used when the maze is generated.
            config: Data for the MAZE INFO panel section.

        Returns:
            None.

        Raises:
            RuntimeError: If MiniLibX initialization or window creation fails.
        """
        self._maze = maze
        self.generator = generator
        self._config = config

        self._mlx = Mlx()
        self._mlx_ptr = self._mlx.mlx_init()

        if self._mlx_ptr is None:
            raise RuntimeError("Filed to initialise MLX")

        self.width, self.height = self._get_window_size()
        self._maze_size = self.height

        self._win_ptr = self._mlx.mlx_new_window(
            self._mlx_ptr,
            self.width,
            self.height,
            title,
        )

        if self._win_ptr is None:
            self._mlx.mlx_release(self._mlx_ptr)
            raise RuntimeError("Failed to create the window")

        self._closed: bool = False
        self._static: Surface | None = None
        self._frame: Surface | None = None
        self._target: Surface | None = None

        self._cell_size: float = 1.0
        self._border_size: float = 1.0
        self._maze_x: float = 0.0
        self._maze_y: float = 0.0
        self._grid_width: float = 0.0
        self._grid_height: float = 0.0

        self._stone_scaled_image: Surface | None = None
        self._floor_scaled_image: Surface | None = None
        self._mark_scaled_image: Surface | None = None
        self._mark_down_scaled_image: Surface | None = None
        self._mark_right_scaled_image: Surface | None = None
        self._mark_left_scaled_image: Surface | None = None
        self._entry_scaled_image: Surface | None = None
        self._exit_scaled_image: Surface | None = None

        self._maze_dog_front_scaled_image: Surface | None = None
        self._maze_dog_left_scaled_image: Surface | None = None
        self._maze_dog_right_scaled_image: Surface | None = None
        self._maze_dog_back_scaled_image: Surface | None = None

        self._maze_dog_exit_1_scaled_image: Surface | None = None
        self._maze_dog_exit_2_scaled_image: Surface | None = None
        self._maze_dog_exit_3_scaled_image: Surface | None = None

        self._panel_scaled_image: Surface | None = None
        self._panel_dog_start_scaled_image: Surface | None = None
        self._panel_dog_1_scaled_image: Surface | None = None
        self._panel_dog_2_scaled_image: Surface | None = None
        self._panel_dog_3_scaled_image: Surface | None = None
        self._panel_dog_4_scaled_image: Surface | None = None

        self._maze_dog_front_image: object | None = None
        self._maze_dog_front_width: int = 0
        self._maze_dog_front_height: int = 0
        self._maze_dog_left_image: object | None = None
        self._maze_dog_left_width: int = 0
        self._maze_dog_left_height: int = 0
        self._maze_dog_right_image: object | None = None
        self._maze_dog_right_width: int = 0
        self._maze_dog_right_height: int = 0
        self._maze_dog_back_image: object | None = None
        self._maze_dog_back_width: int = 0
        self._maze_dog_back_height: int = 0

        self._panel_image: object | None = None

        self._panel_dog_start_image: object | None = None
        self._panel_dog_start_width: int = 0
        self._panel_dog_start_height: int = 0
        self._panel_dog_1_image: object | None = None
        self._panel_dog_1_width: int = 0
        self._panel_dog_1_height: int = 0
        self._panel_dog_2_image: object | None = None
        self._panel_dog_2_width: int = 0
        self._panel_dog_2_height: int = 0
        self._panel_dog_3_image: object | None = None
        self._panel_dog_3_width: int = 0
        self._panel_dog_3_height: int = 0
        self._panel_dog_4_image: object | None = None
        self._panel_dog_4_width: int = 0
        self._panel_dog_4_height: int = 0

        self._wall_vertical_image: Surface | None = None
        self._wall_horizontal_image: Surface | None = None
        self._brick_top_image: Surface | None = None
        self._brick_bottom_image: Surface | None = None
        self._brick_left_image: Surface | None = None
        self._brick_right_image: Surface | None = None
        self._brick_top_left_image: Surface | None = None
        self._brick_top_right_image: Surface | None = None
        self._brick_bottom_left_image: Surface | None = None
        self._brick_bottom_right_image: Surface | None = None

        self._wall_thickness: int = 1
        self._wall_length: int = 1
        self._wall_overhang: int = 0
        self._show_path: bool = False
        self._animation: MazeAnimation = MazeAnimation(self._maze)
        self._theme_index: int = 0

        self._load_textures()
        self._calculate_geometry()
        self._rebuild_scaled_images()
        self._create_buffers()
        self._render_static()
        self._register_events()

        self._draw()

    def _load_textures(self) -> None:
        """Load source XPM textures and store their handles and dimensions.

        Returns:
            None.

        Raises:
            RuntimeError: If any required texture cannot be loaded.
        """
        stone_path: str = str(ASSETS_DIR / "stone.xpm")
        floor_path: str = str(ASSETS_DIR / "floor.xpm")
        wall_path: str = str(ASSETS_DIR / "wall.xpm")
        brick_path: str = str(ASSETS_DIR / "brick.xpm")
        mark_path: str = str(ASSETS_DIR / "mark.xpm")
        entry_path: str = str(ASSETS_DIR / "entry.xpm")
        exit_path: str = str(ASSETS_DIR / "exit.xpm")
        panel_path: str = str(ASSETS_DIR / "panel.xpm")
        panel_dog_start_path: str = str(ASSETS_DIR / "panel_dog_start.xpm")
        panel_dog_1_path: str = str(ASSETS_DIR / "panel_dog_1.xpm")
        panel_dog_2_path: str = str(ASSETS_DIR / "panel_dog_2.xpm")
        panel_dog_3_path: str = str(ASSETS_DIR / "panel_dog_3.xpm")
        panel_dog_4_path: str = str(ASSETS_DIR / "panel_dog_4.xpm")
        maze_dog_front_path: str = str(ASSETS_DIR / "maze_dog_front.xpm")
        maze_dog_left_path: str = str(ASSETS_DIR / "maze_dog_left.xpm")
        maze_dog_right_path: str = str(ASSETS_DIR / "maze_dog_right.xpm")
        maze_dog_back_path: str = str(ASSETS_DIR / "maze_dog_back.xpm")
        maze_dog_exit_1_path: str = str(ASSETS_DIR / "maze_dog_exit_1.xpm")
        maze_dog_exit_2_path: str = str(ASSETS_DIR / "maze_dog_exit_2.xpm")
        maze_dog_exit_3_path: str = str(ASSETS_DIR / "maze_dog_exit_3.xpm")

        stone_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            stone_path,
        )
        floor_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            floor_path,
        )
        mark_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            mark_path,
        )
        entry_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            entry_path,
        )
        exit_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            exit_path,
        )
        panel_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            panel_path,
        )
        panel_dog_start_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            panel_dog_start_path,
        )
        panel_dog_1_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            panel_dog_1_path,
        )
        panel_dog_2_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            panel_dog_2_path,
        )
        panel_dog_3_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            panel_dog_3_path,
        )
        panel_dog_4_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            panel_dog_4_path,
        )
        maze_dog_front_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            maze_dog_front_path,
        )
        maze_dog_left_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            maze_dog_left_path,
        )
        maze_dog_right_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            maze_dog_right_path,
        )
        maze_dog_back_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            maze_dog_back_path,
        )
        maze_dog_exit_1_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            maze_dog_exit_1_path,
        )
        maze_dog_exit_2_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            maze_dog_exit_2_path,
        )
        maze_dog_exit_3_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            maze_dog_exit_3_path,
        )
        wall_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            wall_path,
        )
        brick_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            brick_path,
        )

        if stone_result[0] is None:
            raise RuntimeError(f"Failed to load texture: {stone_path}")
        if floor_result[0] is None:
            raise RuntimeError(f"Failed to load texture: {floor_path}")
        if mark_result[0] is None:
            raise RuntimeError(f"Failed to load testure: {mark_path}")
        if entry_result[0] is None:
            raise RuntimeError(f"Failed to load texture: {entry_path}")
        if exit_result[0] is None:
            raise RuntimeError(f"Failed to load texture: {exit_path}")
        if panel_result[0] is None:
            raise RuntimeError(f"Failed to load texture: {panel_path}")
        if panel_dog_start_result[0] is None:
            raise RuntimeError(
                f"Failed to load texture: {panel_dog_start_path}"
            )
        if panel_dog_1_result[0] is None:
            raise RuntimeError(f"Failed to load texture: {panel_dog_1_path}")
        if panel_dog_2_result[0] is None:
            raise RuntimeError(f"Failed to load texture: {panel_dog_2_path}")
        if panel_dog_3_result[0] is None:
            raise RuntimeError(f"Failed to load texture: {panel_dog_3_path}")
        if panel_dog_4_result[0] is None:
            raise RuntimeError(f"Failed to load texture: {panel_dog_4_path}")
        if maze_dog_front_result[0] is None:
            raise RuntimeError(
                f"Failed to load texture: {maze_dog_front_path}"
            )
        if maze_dog_left_result[0] is None:
            raise RuntimeError(
                f"Failed to load texture: {maze_dog_left_path}"
            )
        if maze_dog_right_result[0] is None:
            raise RuntimeError(
                f"Failed to load texture: {maze_dog_right_path}"
            )
        if maze_dog_back_result[0] is None:
            raise RuntimeError(
                f"Failed to load texture: {maze_dog_back_path}"
            )
        if maze_dog_exit_1_result[0] is None:
            raise RuntimeError(
                f"Failed to load texture: {maze_dog_exit_1_path}"
            )
        if maze_dog_exit_2_result[0] is None:
            raise RuntimeError(
                f"Failed to load texture: {maze_dog_exit_2_path}"
            )
        if maze_dog_exit_3_result[0] is None:
            raise RuntimeError(
                f"Failed to load texture: {maze_dog_exit_3_path}"
            )
        if wall_result[0] is None:
            raise RuntimeError(f"Failed to load texture: {wall_path}")
        if brick_result[0] is None:
            raise RuntimeError(f"Failed to load texture: {brick_path}")

        self._stone_image = stone_result[0]
        self._stone_width = int(stone_result[1])
        self._stone_height = int(stone_result[2])

        self._floor_image = floor_result[0]
        self._floor_width = int(floor_result[1])
        self._floor_height = int(floor_result[2])

        self._mark_image = mark_result[0]
        self._mark_width = int(mark_result[1])
        self._mark_height = int(mark_result[2])

        self._entry_image = entry_result[0]
        self._entry_width = int(entry_result[1])
        self._entry_height = int(entry_result[2])

        self._exit_image = exit_result[0]
        self._exit_width = int(exit_result[1])
        self._exit_height = int(exit_result[2])

        self._panel_image = panel_result[0]
        self._panel_width = int(panel_result[1])
        self._panel_height = int(panel_result[2])

        self._panel_dog_start_image = panel_dog_start_result[0]
        self._panel_dog_start_width = int(panel_dog_start_result[1])
        self._panel_dog_start_height = int(panel_dog_start_result[2])

        self._panel_dog_1_image = panel_dog_1_result[0]
        self._panel_dog_1_width = int(panel_dog_1_result[1])
        self._panel_dog_1_height = int(panel_dog_1_result[2])

        self._panel_dog_2_image = panel_dog_2_result[0]
        self._panel_dog_2_width = int(panel_dog_2_result[1])
        self._panel_dog_2_height = int(panel_dog_2_result[2])

        self._panel_dog_3_image = panel_dog_3_result[0]
        self._panel_dog_3_width = int(panel_dog_3_result[1])
        self._panel_dog_3_height = int(panel_dog_3_result[2])

        self._panel_dog_4_image = panel_dog_4_result[0]
        self._panel_dog_4_width = int(panel_dog_4_result[1])
        self._panel_dog_4_height = int(panel_dog_4_result[2])

        self._maze_dog_front_image = maze_dog_front_result[0]
        self._maze_dog_front_width = int(maze_dog_front_result[1])
        self._maze_dog_front_height = int(maze_dog_front_result[2])

        self._maze_dog_left_image = maze_dog_left_result[0]
        self._maze_dog_left_width = int(maze_dog_left_result[1])
        self._maze_dog_left_height = int(maze_dog_left_result[2])

        self._maze_dog_right_image = maze_dog_right_result[0]
        self._maze_dog_right_width = int(maze_dog_right_result[1])
        self._maze_dog_right_height = int(maze_dog_right_result[2])

        self._maze_dog_back_image = maze_dog_back_result[0]
        self._maze_dog_back_width = int(maze_dog_back_result[1])
        self._maze_dog_back_height = int(maze_dog_back_result[2])

        self._maze_dog_exit_1_image = maze_dog_exit_1_result[0]
        self._maze_dog_exit_1_width = int(maze_dog_exit_1_result[1])
        self._maze_dog_exit_1_height = int(maze_dog_exit_1_result[2])

        self._maze_dog_exit_2_image = maze_dog_exit_2_result[0]
        self._maze_dog_exit_2_width = int(maze_dog_exit_2_result[1])
        self._maze_dog_exit_2_height = int(maze_dog_exit_2_result[2])

        self._maze_dog_exit_3_image = maze_dog_exit_3_result[0]
        self._maze_dog_exit_3_width = int(maze_dog_exit_3_result[1])
        self._maze_dog_exit_3_height = int(maze_dog_exit_3_result[2])

        self._wall_image = wall_result[0]
        self._wall_width = int(wall_result[1])
        self._wall_height = int(wall_result[2])

        self._brick_image = brick_result[0]
        self._brick_width = int(brick_result[1])
        self._brick_height = int(brick_result[2])

    def run(self) -> None:
        """Start the MiniLibX event loop.

        Returns:
            None.
        """
        self._mlx.mlx_loop(self._mlx_ptr)

    def close(self) -> None:
        """Release image, window, and MiniLibX resources exactly once.

        Returns:
            None.
        """
        if self._closed:
            return

        self._closed = True
        self._mlx.mlx_loop_exit(self._mlx_ptr)

        self._destroy_scaled_images()
        for surface in (self._static, self._frame):
            if surface is not None:
                self._mlx.mlx_destroy_image(self._mlx_ptr, surface.image)
        self._static = None
        self._frame = None

        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._stone_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._floor_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._mark_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._entry_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._exit_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._panel_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._panel_dog_start_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._panel_dog_1_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._panel_dog_2_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._panel_dog_3_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._panel_dog_4_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._maze_dog_front_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._maze_dog_left_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._maze_dog_right_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._maze_dog_back_image
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._maze_dog_exit_1_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._maze_dog_exit_2_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._maze_dog_exit_3_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._wall_image,
        )
        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._brick_image,
        )
        self._mlx.mlx_destroy_window(
            self._mlx_ptr,
            self._win_ptr,
        )
        self._mlx.mlx_release(self._mlx_ptr)

    def _get_window_size(self) -> tuple[int, int]:
        """Calculate a window size scaled to the avaliable screen.

        Returns:
            A tuple containing the window width an height in pixels.

        Raises:
            RuntimeError: If the screen size cannot be retrieved or is invalid.
        """
        result: int
        screen_width: int
        screen_height: int

        result, screen_width, screen_height = (
            self._mlx.mlx_get_screen_size(self._mlx_ptr)
        )

        if result != 0:
            raise RuntimeError("Failed to get screen size")
        if screen_width <= 0 or screen_height <= 0:
            raise RuntimeError("Invalid screen size")

        scale_x: float = screen_width / self.REFERENCE_SCREEN_WIDTH
        scale_y: float = screen_height / self.REFERENCE_SCREEN_HEIGHT
        scale: float = min(scale_x, scale_y)

        window_width: int = max(1, round(self.REFERENCE_WINDOW_WIDTH * scale))
        window_height: int = max(1, round(window_width / self.GOLDEN_RATIO))

        return window_width, window_height

    def _calculate_geometry(self) -> None:
        """Calculate cell dimensions and the maze's drawing position.

        The cell size is selected from the maze dimensions and available
        window space. The resulting grid dimensions and offsets are stored
        on the instance for use by drawing methods.

        Returns:
            None.
        """
        rows: int = self._maze.height
        columns: int = self._maze.width
        largest_dimension: int = max(rows, columns)

        reference_canvas_size: float = 742.0
        reference_cell_size: float = 16.0

        if largest_dimension <= 15:
            reference_cell_size = 40.0
        elif largest_dimension <= 25:
            reference_cell_size = 24.0

        if largest_dimension <= 35:
            scale: float = self._maze_size / reference_canvas_size
            self._cell_size = reference_cell_size * scale
        else:
            available_size: float = self._maze_size * 0.9
            denominator: int = largest_dimension + 1
            self._cell_size = available_size / denominator

        self._border_size = self._cell_size * 0.5
        self._grid_width = columns * self._cell_size
        self._grid_height = rows * self._cell_size

        total_width: float = self._grid_width + self._border_size * 2
        total_height: float = self._grid_height + self._border_size * 2

        self._maze_x = (
            self._maze_size - total_width
        ) / 2 + self._border_size
        self._maze_y = (
            self._maze_size - total_height
        ) / 2 + self._border_size

    def _register_events(self) -> None:
        """Register keyboard and window-close event callbacks.

        Returns:
            None.
        """
        self._mlx.mlx_key_hook(
            self._win_ptr,
            self._on_key,
            self,
        )
        self._mlx.mlx_hook(
            self._win_ptr,
            self.CLOSE_EVENT,
            0,
            self._on_close,
            self,
        )
        self._mlx.mlx_loop_hook(
            self._mlx_ptr,
            self._on_loop,
            self,
        )

    @staticmethod
    def _on_key(keycode: int, param: object) -> None:
        """Dispath supported keyboard shortcuts.

        Args:
            keycode: Key code received from MiniLibX.
            param: Callback context; ignored unless it is a Window instance.

        Returns:
            None.
        """
        if not isinstance(param, Window):
            return

        if keycode == param.ESC_KEYCODE:
            param.close()
        elif keycode == param.REGENERATE_KEYCODE:
            param._regenerate()
        elif keycode == param.PATH_KEYCODE:
            param._toggle_path()
        elif keycode == param.THEME_KEYCODE:
            param._change_theme()
        elif keycode == param.ANIMATE_KEYCODE:
            param._start_animation()

    @staticmethod
    def _on_close(param: object) -> None:
        """Handle a window-close event.

        Args:
            param: Callback context; ignored unless it is a Window instance.

        Returns:
            None.
        """
        if not isinstance(param, Window):
            return
        param.close()

    @staticmethod
    def _on_loop(param: object) -> None:
        """Update animations and redraw the window when a frame changes."""
        if not isinstance(param, Window):
            return

        if param._animation.update():
            param._draw()
        else:
            sleep(0.005)

    def _regenerate(self) -> None:
        """Generate a replacement maze and redraw the window.

        The current dimensions, entry and exit are preserved.

        Returns:
            None.
        """
        new_maze: Maze = Maze(
            self._maze.width,
            self._maze.height,
            self._maze.entry,
            self._maze.exit,
        )

        self.generator.generate(new_maze)
        self._maze = new_maze
        self._show_path = False
        self._animation.reset_maze(self._maze)

        # Width/height are preserved, so geometry and scaled textures are
        # still valid. Only the static layer (walls, 42...) must be redone.
        self._render_static()
        self._draw()

    def _create_buffers(self) -> None:
        """Create the static layer and the frame buffer (window sized).

        Returns:
            None.

        Raises:
            RuntimeError: If an image cannot be allocated.
        """
        self._static = self._new_surface(self.width, self.height, "static")
        self._frame = self._new_surface(self.width, self.height, "frame")

    def _new_surface(self, width: int, height: int, label: str) -> Surface:
        """Allocate a blank MiniLibX image and wrap it in a Surface."""
        image = self._mlx.mlx_new_image(self._mlx_ptr, width, height)
        if image is None:
            raise RuntimeError(f"Failed to create {label} image")
        data = self._mlx.mlx_get_data_addr(image)
        return Surface(
            image,
            data[0],
            width,
            height,
            int(data[1]) // 8,
            int(data[2]),
            int(data[3]),
        )

    def _render_static(self) -> None:
        """Redraw everything that only changes with the maze or theme.

        Floor, 42 logo, walls, brick frame and the panel background are
        drawn once into the static layer, not on every frame.

        Returns:
            None.
        """
        if self._static is None:
            return

        self._static.clear()
        self._target = self._static
        self._draw_floor()
        self._draw_cells()
        self._draw_walls()
        self._draw_bricks()
        self._draw_panel_background()

    def _draw(self) -> None:
        """Compose one frame off-screen and send it to the window once.

        The frame starts as a copy of the static layer; only the dynamic
        elements (path or trail, entry/exit, dogs) are blitted on top.
        There is no ``mlx_clear_window``, so nothing can flicker.

        Returns:
            None.
        """
        if self._static is None or self._frame is None:
            return

        self._frame.copy_from(self._static)
        self._target = self._frame

        if self._show_path:
            self._draw_solution_path()
        else:
            self._draw_animation_trail()

        self._draw_entry_exit()
        self._draw_animated_dog()
        self._draw_panel_dog()

        self._draw_panel_text()
        self._mlx.mlx_put_image_to_window(
            self._mlx_ptr,
            self._win_ptr,
            self._frame.image,
            0,
            0,
        )
        # self._mlx.mlx_do_sync(self._mlx_ptr)

    def _start_animation(self) -> None:
        """Start the dog trip and hide the static shortest path."""
        self._show_path = False
        self._animation.start()
        self._draw()

    def _toggle_path(self) -> None:
        """Toggle shortest_path visibility and redraw the window.

        Returns:
            None.
        """
        self._show_path = not self._show_path
        self._draw()

    def _change_theme(self) -> None:
        """Advance to the next visual theme and redraw the window.

        Returns:
            None.
        """
        self._theme_index = (self._theme_index + 1) % len(self.THEME_NAMES)
        self._rebuild_scaled_images()
        self._render_static()
        self._draw()

    def _rebuild_scaled_images(self) -> None:
        """Recreate scaled textures for the current geometry and wall tint.

        Previously scaled images are destroyed before their replacements
        are created.

        Returns:
            None.
        """
        self._destroy_scaled_images()
        theme: dict[str, int | None] = self.THEMES[
            self.THEME_NAMES[self._theme_index]
        ]

        cell_size: int = max(1, round(self._cell_size))

        self._wall_thickness = max(
            1,
            round(
                self.WALL_REFERENCE_WIDTH
                * self._cell_size
                / self.WALL_REFERENCE_CELL_SIZE
            ),
        )
        self._wall_length = max(cell_size, 1)
        self._wall_overhang = 0

        brick_size: int = cell_size
        brick_half_size: int = max(1, round(cell_size / 2))

        self._floor_scaled_image = self._create_scaled_image(
            self._floor_image,
            self._floor_width,
            self._floor_height,
            cell_size,
            cell_size,
            False,
            "floor",
            tint_color=theme["floor"]
        )

        self._mark_scaled_image = self._create_scaled_image(
            self._mark_image,
            self._mark_width,
            self._mark_height,
            cell_size,
            cell_size,
            False,
            "mark",
        )

        self._mark_down_scaled_image = self._create_scaled_image(
            self._mark_image,
            self._mark_width,
            self._mark_height,
            cell_size,
            cell_size,
            False,
            "mark down",
            rotation_degrees=180,
        )

        self._mark_right_scaled_image = self._create_scaled_image(
            self._mark_image,
            self._mark_width,
            self._mark_height,
            cell_size,
            cell_size,
            False,
            "mark right",
            rotation_degrees=90,
        )

        self._mark_left_scaled_image = self._create_scaled_image(
            self._mark_image,
            self._mark_width,
            self._mark_height,
            cell_size,
            cell_size,
            False,
            "mark left",
            rotation_degrees=270,
        )

        self._entry_scaled_image = self._create_scaled_image(
            self._entry_image,
            self._entry_width,
            self._entry_height,
            cell_size,
            cell_size,
            False,
            "entry",
        )

        self._exit_scaled_image = self._create_scaled_image(
            self._exit_image,
            self._exit_width,
            self._exit_height,
            cell_size,
            cell_size,
            False,
            "exit",
        )

        panel_scale: float = (self._maze_size / self.PANEL_REFERENCE_HEIGHT)        
        art_scale: float = panel_scale / self.ASSET_SCALE

        panel_width: int = max(1, round(self._panel_width * art_scale))

        panel_height: int = max(1, round(self._panel_height * art_scale))

        self._panel_scaled_image = self._create_scaled_image(
            self._panel_image,
            self._panel_width,
            self._panel_height,
            panel_width,
            panel_height,
            False,
            "panel",
            tint_color=theme["panel"],
        )

        dog_width: int = max(
            1, round(self._panel_dog_start_width * art_scale)
        )
        dog_height: int = max(
            1, round(self._panel_dog_start_height * art_scale)
        )

        self._panel_dog_start_scaled_image = self._create_scaled_image(
            self._panel_dog_start_image,
            self._panel_dog_start_width,
            self._panel_dog_start_height,
            dog_width,
            dog_height,
            False,
            "panel_dog_start",
        )

        self._panel_dog_1_scaled_image = self._create_scaled_image(
            self._panel_dog_1_image,
            self._panel_dog_1_width,
            self._panel_dog_1_height,
            dog_width,
            dog_height,
            False,
            "panel_dog_1",
        )

        self._panel_dog_2_scaled_image = self._create_scaled_image(
            self._panel_dog_2_image,
            self._panel_dog_2_width,
            self._panel_dog_2_height,
            dog_width,
            dog_height,
            False,
            "panel_dog_2"
        )

        self._panel_dog_3_scaled_image = self._create_scaled_image(
            self._panel_dog_3_image,
            self._panel_dog_3_width,
            self._panel_dog_3_height,
            dog_width,
            dog_height,
            False,
            "panel_dog_3",
        )

        self._panel_dog_4_scaled_image = self._create_scaled_image(
            self._panel_dog_4_image,
            self._panel_dog_4_width,
            self._panel_dog_4_height,
            dog_width,
            dog_height,
            False,
            "panel_dog_4",
        )

        self._stone_scaled_image = self._create_scaled_image(
            self._stone_image,
            self._stone_width,
            self._stone_height,
            cell_size,
            cell_size,
            False,
            "stone",
            tint_color=theme["logo42"],
        )

        self._wall_vertical_image = self._create_scaled_image(
            self._wall_image,
            self._wall_width,
            self._wall_height,
            self._wall_thickness,
            self._wall_length,
            False,
            "wall vertical",
            tint_color=theme["wall"],
        )

        self._wall_horizontal_image = self._create_scaled_image(
            self._wall_image,
            self._wall_width,
            self._wall_height,
            self._wall_length,
            self._wall_thickness,
            True,
            "wall horizontal",
            tint_color=theme["wall"],
        )

        self._brick_top_image = self._create_scaled_image(
            self._brick_image,
            self._brick_width,
            self._brick_height,
            brick_size,
            brick_half_size,
            False,
            "brick top",
            tint_color=theme["border"]
        )

        self._brick_bottom_image = self._create_scaled_image(
            self._brick_image,
            self._brick_width,
            self._brick_height,
            brick_size,
            brick_half_size,
            False,
            "brick bottom",
            tint_color=theme["border"]
        )

        self._brick_left_image = self._create_scaled_image(
            self._brick_image,
            self._brick_width,
            self._brick_height,
            brick_half_size,
            brick_size,
            True,
            "brick left",
            tint_color=theme["border"]
        )

        self._brick_right_image = self._create_scaled_image(
            self._brick_image,
            self._brick_width,
            self._brick_height,
            brick_half_size,
            brick_size,
            True,
            "brick right",
            tint_color=theme["border"]
        )

        self._brick_top_left_image = self._create_scaled_image(
            self._brick_image,
            self._brick_width,
            self._brick_height,
            brick_half_size,
            brick_half_size,
            False,
            "brick top left",
            crop_width_ratio=0.5,
            crop_height_ratio=1.0,
            crop_x_start_ratio=0.0,
            crop_y_start_ratio=0.0,
            tint_color=theme["border"]
        )

        self._brick_top_right_image = self._create_scaled_image(
            self._brick_image,
            self._brick_width,
            self._brick_height,
            brick_half_size,
            brick_half_size,
            False,
            "brick top right",
            crop_width_ratio=0.5,
            crop_height_ratio=1.0,
            crop_x_start_ratio=0.0,
            crop_y_start_ratio=0.0,
            tint_color=theme["border"]
        )

        self._brick_bottom_left_image = self._create_scaled_image(
            self._brick_image,
            self._brick_width,
            self._brick_height,
            brick_half_size,
            brick_half_size,
            False,
            "brick bottom left",
            crop_width_ratio=0.5,
            crop_height_ratio=1.0,
            crop_x_start_ratio=0.0,
            crop_y_start_ratio=0.0,
            tint_color=theme["border"]
        )

        self._brick_bottom_right_image = self._create_scaled_image(
            self._brick_image,
            self._brick_width,
            self._brick_height,
            brick_half_size,
            brick_half_size,
            False,
            "brick bottom right",
            crop_width_ratio=0.5,
            crop_height_ratio=1.0,
            crop_x_start_ratio=0.0,
            crop_y_start_ratio=0.0,
            tint_color=theme["border"]
        )

        self._maze_dog_front_scaled_image = self._create_scaled_image(
            self._maze_dog_front_image,
            self._maze_dog_front_width,
            self._maze_dog_front_height,
            cell_size,
            cell_size,
            False,
            "maze dog front"
        )

        self._maze_dog_left_scaled_image = self._create_scaled_image(
            self._maze_dog_left_image,
            self._maze_dog_left_width,
            self._maze_dog_left_height,
            cell_size,
            cell_size,
            False,
            "maze dog left",
        )

        self._maze_dog_right_scaled_image = self._create_scaled_image(
            self._maze_dog_right_image,
            self._maze_dog_right_width,
            self._maze_dog_right_height,
            cell_size,
            cell_size,
            False,
            "maze dog right",
        )

        self._maze_dog_back_scaled_image = self._create_scaled_image(
            self._maze_dog_back_image,
            self._maze_dog_back_width,
            self._maze_dog_back_height,
            cell_size,
            cell_size,
            False,
            "maze dog back",
        )

        self._maze_dog_exit_1_scaled_image = self._create_scaled_image(
            self._maze_dog_exit_1_image,
            self._maze_dog_exit_1_width,
            self._maze_dog_exit_1_height,
            cell_size,
            cell_size,
            False,
            "maze dog exit 1",
        )

        self._maze_dog_exit_2_scaled_image = self._create_scaled_image(
            self._maze_dog_exit_2_image,
            self._maze_dog_exit_2_width,
            self._maze_dog_exit_2_height,
            cell_size,
            cell_size,
            False,
            "maze dog exit 2",
        )

        self._maze_dog_exit_3_scaled_image = self._create_scaled_image(
            self._maze_dog_exit_3_image,
            self._maze_dog_exit_3_width,
            self._maze_dog_exit_3_height,
            cell_size,
            cell_size,
            False,
            "maze dog exit 3",
        )

    def _create_scaled_image(
        self,
        source_image: object,
        source_width: int,
        source_height: int,
        target_width: int,
        target_height: int,
        rotate_clockwise: bool,
        label: str,
        crop_width_ratio: float = 1.0,
        crop_height_ratio: float = 1.0,
        crop_x_start_ratio: float = 0.0,
        crop_y_start_ratio: float = 0.0,
        tint_color: int | None = None,
        rotation_degrees: int | None = None,
    ) -> Surface:
        """Resize an image, optionally cropping, rotating, or tinting it.

        Args:
            source_image: Source MiniLibX image handle.
            source_width: Width of the source image in pixels.
            source_height: Height of the source image in pixels.
            target_width: Desired output width in pixels.
            target_height: Desired output height in pixels.
            rotate_clockwise: Whether to rotate the image 90 degrees clocwise
                when ``rotation_degrees`` is not provided.
            label: Name used in error messages.
            crop_width_ratio: Fraction of source width to retain.
            crop_height_ratio: Fraction of source height to retain.
            crop_x_start_ratio: Horizontal crop offset ratio.
            crop_y_start_ratio: Vertical crop offset ratio.
            tint_color: Optional RGB color in 0xRRGGBB format.
                ``None`` preserves the original pixel colors.
            rotation_degrees: Optional rotation in degrees: 0, 90, 180 or 270.

        Returns:
            The handle of the newly created scaled image.

        Raise:
            RuntimeError: If image allocation or pixel-format validation
            fails.
        """
        target_width = max(1, target_width)
        target_height = max(1, target_height)

        scaled_image = self._mlx.mlx_new_image(
            self._mlx_ptr,
            target_width,
            target_height,
        )
        if scaled_image is None:
            raise RuntimeError(f"Failed to create scaled {label} image")

        source_data = self._mlx.mlx_get_data_addr(source_image)
        destination_data = self._mlx.mlx_get_data_addr(scaled_image)

        source_buffer: memoryview = source_data[0]
        source_bits_per_pixel: int = int(source_data[1])
        source_size_line: int = int(source_data[2])
        source_format: int = int(source_data[3])

        destination_buffer: memoryview = destination_data[0]
        destination_bits_per_pixel: int = int(destination_data[1])
        destination_size_line: int = int(destination_data[2])
        destination_format: int = int(destination_data[3])

        if source_bits_per_pixel != destination_bits_per_pixel:
            self._mlx.mlx_destroy_image(self._mlx_ptr, scaled_image)
            raise RuntimeError(f"{label} texture pixel formats differ")

        if source_format != destination_format:
            self._mlx.mlx_destroy_image(self._mlx_ptr, scaled_image)
            raise RuntimeError(f"{label} texture image formats differ")

        bytes_per_pixel: int = source_bits_per_pixel // 8
        if bytes_per_pixel <= 0:
            self._mlx.mlx_destroy_image(self._mlx_ptr, scaled_image)
            raise RuntimeError(f"Invalid {label} texture pixel size")

        crop_width_ratio = min(1.0, max(0.0, crop_width_ratio))
        crop_height_ratio = min(1.0, max(0.0, crop_height_ratio))

        crop_width: int = max(1, round(source_width * crop_width_ratio))
        crop_height: int = max(1, round(source_height * crop_height_ratio))
        crop_x_offset: int = round(
            (source_width - crop_width) * crop_x_start_ratio
        )
        crop_y_offset: int = round(
            (source_height - crop_height) * crop_y_start_ratio
        )

        rotation: int = (
            (90 if rotate_clockwise else 0)
            if rotation_degrees is None
            else rotation_degrees % 360
        )

        for destination_y in range(target_height):
            y_ratio: float = (
                destination_y / max(1, target_height - 1)
            )

            for destination_x in range(target_width):
                x_ratio: float = (
                    destination_x / max(1, target_width - 1)
                )

                if rotation == 90:
                    source_x = (
                        crop_x_offset
                        + round(y_ratio * (crop_width - 1))
                    )
                    source_y = (
                        crop_y_offset
                        + round(
                            (1.0 - x_ratio) * (crop_height - 1)
                        )
                    )
                elif rotation == 180:
                    source_x = (
                        crop_x_offset
                        + round((1.0 - x_ratio) * (crop_width - 1))
                    )
                    source_y = (
                        crop_y_offset
                        + round((1.0 - y_ratio) * (crop_height - 1))
                    )
                elif rotation == 270:
                    source_x = (
                        crop_x_offset
                        + round((1.0 - y_ratio) * (crop_width - 1))
                    )
                    source_y = (
                        crop_y_offset
                        + round(x_ratio * (crop_height - 1))
                    )
                else:
                    source_x = (
                        crop_x_offset
                        + round(x_ratio * (crop_width - 1))
                    )
                    source_y = (
                        crop_y_offset
                        + round(y_ratio * (crop_height - 1))
                    )

                source_offset: int = (
                    source_y * source_size_line
                    + source_x * bytes_per_pixel
                )
                destination_offset: int = (
                    destination_y * destination_size_line
                    + destination_x * bytes_per_pixel
                )

                if tint_color is None or bytes_per_pixel < 3:
                    destination_buffer[
                        destination_offset:
                        destination_offset + bytes_per_pixel
                    ] = source_buffer[
                        source_offset:
                        source_offset + bytes_per_pixel
                    ]
                    continue

                byte_order: Literal["little", "big"] = (
                    "little" if source_format == 0 else "big"
                )
                source_pixel = int.from_bytes(
                    bytes(
                        source_buffer[
                            source_offset:
                            source_offset + bytes_per_pixel
                        ]
                    ),
                    byteorder=byte_order,
                )

                red = (source_pixel >> 16) & 0xFF
                green = (source_pixel >> 8) & 0xFF
                blue = source_pixel & 0xFF
                brightness = (red + green + blue) // 3

                target_red = (tint_color >> 16) & 0xFF
                target_green = (tint_color >> 8) & 0xFF
                target_blue = tint_color & 0xFF

                tinted_pixel = (source_pixel & ~0xFFFFFF)
                tinted_pixel |= (target_red * brightness // 255) << 16
                tinted_pixel |= (target_green * brightness // 255) << 8
                tinted_pixel |= target_blue * brightness // 255

                destination_buffer[
                    destination_offset:
                    destination_offset + bytes_per_pixel
                ] = tinted_pixel.to_bytes(
                    bytes_per_pixel,
                    byteorder=byte_order,
                )

        return Surface(
            scaled_image,
            destination_buffer,
            target_width,
            target_height,
            bytes_per_pixel,
            destination_size_line,
            destination_format,
        )

    def _destroy_scaled_images(self) -> None:
        """Destroy every scaled image owned by the window.

        Each corresponding instance attribute is reset to ``None``.

        Returns:
            None.
        """
        scaled_images = (
            "_stone_scaled_image",
            "_floor_scaled_image",
            "_mark_scaled_image",
            "_mark_down_scaled_image",
            "_mark_right_scaled_image",
            "_mark_left_scaled_image",
            "_entry_scaled_image",
            "_exit_scaled_image",
            "_maze_dog_front_scaled_image",
            "_maze_dog_left_scaled_image",
            "_maze_dog_right_scaled_image",
            "_maze_dog_back_scaled_image",
            "_maze_dog_exit_1_scaled_image",
            "_maze_dog_exit_2_scaled_image",
            "_maze_dog_exit_3_scaled_image",
            "_panel_scaled_image",
            "_panel_dog_start_scaled_image",
            "_panel_dog_1_scaled_image",
            "_panel_dog_2_scaled_image",
            "_panel_dog_3_scaled_image",
            "_panel_dog_4_scaled_image",
            "_wall_vertical_image",
            "_wall_horizontal_image",
            "_brick_top_image",
            "_brick_bottom_image",
            "_brick_left_image",
            "_brick_right_image",
            "_brick_top_left_image",
            "_brick_top_right_image",
            "_brick_bottom_left_image",
            "_brick_bottom_right_image",
        )

        for name in scaled_images:
            image = getattr(self, name)
            if image is not None:
                self._mlx.mlx_destroy_image(
                    self._mlx_ptr,
                    image.image,
                )
                setattr(self, name, None)

    def _put_image(
        self,
        image: Surface | None,
        x: float,
        y: float,
    ) -> None:
        """Blit a scaled image into the current target surface.

        Args:
            image: Surface to draw, or ``None`` to skip drawing.
            x: Horizontal drawing coordinate in pixels.
            y: Vertical drawing coordinate in pixels.

        Returns:
            None.
        """
        if image is None or self._target is None:
            return

        self._target.blit(image, round(x), round(y))

    def _draw_floor(self) -> None:
        """Draw floor tiles for all cells except the 42 pattern.

        Returns:
            None.
        """
        if self._floor_scaled_image is None:
            return

        for row in self._maze.grid:
            for cell in row:
                if cell.logo42:
                    continue

                x: float = self._maze_x + cell.column * self._cell_size
                y: float = self._maze_y + cell.row * self._cell_size
                self._put_image(
                    self._floor_scaled_image,
                    x,
                    y,
                )

    def _draw_cells(self) -> None:
        """Draw stone tiles for cells marked as part of the 42 pattern.

        Returns:
            None.
        """
        if self._stone_scaled_image is None:
            return

        for row in self._maze.grid:
            for cell in row:
                if not cell.logo42:
                    continue

                x: float = (
                    self._maze_x + cell.column * self._cell_size
                )
                y: float = (
                    self._maze_y + cell.row * self._cell_size
                )
                self._put_image(
                    self._stone_scaled_image,
                    x,
                    y,
                )

    def _draw_entry_exit(self) -> None:
        """Draw the entry maker, dog and current exit image.

        The front-facing dog overlays the entry maker. When the shortest
        path is visible, the exit bone is replaced by the first
        exit-dog sprite.

        Returns:
            None.
        """
        if (
            self._entry_scaled_image is None
            or self._exit_scaled_image is None
        ):
            return

        entry_x: float = (
            self._maze_x
            + self._maze.entry[0] * self._cell_size
        )
        entry_y: float = (
            self._maze_y
            + self._maze.entry[1] * self._cell_size
        )

        exit_x: float = (
            self._maze_x
            + self._maze.exit[0] * self._cell_size
        )
        exit_y: float = (
            self._maze_y
            + self._maze.exit[1] * self._cell_size
        )

        # Draw the entry marker first.
        self._put_image(
            self._entry_scaled_image,
            entry_x,
            entry_y,
        )
        # Show the front_facing dog over the entry while the path is hidden.
        if (
            not self._show_path
            and self._animation.maze_state == "idle"
            and self._maze_dog_front_scaled_image is not None
        ):
            self._put_image(
                self._maze_dog_front_scaled_image,
                entry_x,
                entry_y,
            )

        # Select the exit image according to the current state.
        exit_image = self._exit_scaled_image

        if (
            self._show_path
            and self._maze_dog_exit_1_scaled_image is not None
        ):
            exit_image = self._maze_dog_exit_1_scaled_image

        elif self._animation.exit_frame is not None:
            exit_images: dict[int, Surface | None] = {
                1: self._maze_dog_exit_1_scaled_image,
                2: self._maze_dog_exit_2_scaled_image,
                3: self._maze_dog_exit_3_scaled_image,
            }

            current_exit_image = exit_images[self._animation.exit_frame]

            if current_exit_image is not None:
                exit_image = current_exit_image

        self._put_image(
            exit_image,
            exit_x,
            exit_y,
        )

    def _draw_walls(self) -> None:
        """Draw the internal east and south walls defined by maze cells.

        Returns:
            None.
        """
        if (
            self._wall_vertical_image is None
            or self._wall_horizontal_image is None
        ):
            return

        last_row: int = self._maze.height - 1
        last_column: int = self._maze.width - 1

        for row in self._maze.grid:
            for cell in row:
                x0: float = (
                    self._maze_x
                    + cell.column * self._cell_size
                )
                x1: float = (
                    self._maze_x
                    + (cell.column + 1) * self._cell_size
                )
                y0: float = (
                    self._maze_y
                    + cell.row * self._cell_size
                )
                y1: float = (
                    self._maze_y
                    + (cell.row + 1) * self._cell_size
                )

                if cell.east and cell.column < last_column:
                    self._put_image(
                        self._wall_vertical_image,
                        x1 - self._wall_thickness / 2,
                        y0,
                    )

                if cell.south and cell.row < last_row:
                    self._put_image(
                        self._wall_horizontal_image,
                        x0,
                        y1 - self._wall_thickness / 2,
                    )

    def _draw_solution_path(self) -> None:
        """Draw directional markers along the maze's shortest path.

        The markers are oriented to match each move from the entry to the exit.

        Returns:
            None.
        """
        if (
            self._mark_scaled_image is None
            or self._mark_down_scaled_image is None
            or self._mark_right_scaled_image is None
            or self._mark_left_scaled_image is None
        ):
            return

        path: str = self._maze.shortest_path()
        column: int = self._maze.entry[0]
        row: int = self._maze.entry[1]

        entry: tuple[int, int] = self._maze.entry
        exit_cell: tuple[int, int] = self._maze.exit

        for direction in path:
            if (column, row) not in (entry, exit_cell):
                if direction == "N":
                    mark_image = self._mark_scaled_image
                elif direction == "E":
                    mark_image = self._mark_right_scaled_image
                elif direction == "S":
                    mark_image = self._mark_down_scaled_image
                else:
                    mark_image = self._mark_left_scaled_image

                x: float = self._maze_x + column * self._cell_size
                y: float = self._maze_y + row * self._cell_size

                self._put_image(mark_image, x, y)

            if direction == "N":
                row -= 1
            elif direction == "E":
                column += 1
            elif direction == "S":
                row += 1
            elif direction == "W":
                column -= 1

    def _draw_bricks(self) -> None:
        """Draw the decorative brick frame around the maze.

        Returns:
            None.
        """
        if (
            self._brick_top_image is None
            or self._brick_bottom_image is None
            or self._brick_left_image is None
            or self._brick_right_image is None
            or self._brick_top_left_image is None
            or self._brick_top_right_image is None
            or self._brick_bottom_left_image is None
            or self._brick_bottom_right_image is None
        ):
            return

        for column in range(self._maze.width):
            x: float = (
                self._maze_x
                + column * self._cell_size
            )
            self._put_image(
                self._brick_top_image,
                x,
                self._maze_y - self._cell_size / 2,
            )
            self._put_image(
                self._brick_bottom_image,
                x,
                self._maze_y
                + self._grid_height,
            )

        for row in range(self._maze.height):
            y: float = (
                self._maze_y
                + row * self._cell_size
            )

            self._put_image(
                self._brick_left_image,
                self._maze_x - self._cell_size / 2,
                y,
            )
            self._put_image(
                self._brick_right_image,
                self._maze_x
                + self._grid_width,
                y,
            )

        self._put_image(
            self._brick_top_left_image,
            self._maze_x - self._cell_size / 2,
            self._maze_y - self._cell_size / 2,
        )
        self._put_image(
            self._brick_top_right_image,
            self._maze_x
            + self._grid_width,
            self._maze_y - self._cell_size / 2,
        )
        self._put_image(
            self._brick_bottom_left_image,
            self._maze_x - self._cell_size / 2,
            self._maze_y + self._grid_height
        )
        self._put_image(
            self._brick_bottom_right_image,
            self._maze_x
            + self._grid_width,
            self._maze_y
            + self._grid_height,
        )

    def _panel_layout(self) -> tuple[float, int, int, int, int]:
        """Return panel scale, x, y, bottom y and dog area size."""
        panel_scale: float = self._maze_size / self.PANEL_REFERENCE_HEIGHT
        panel_x: int = self._maze_size + round(
            self.PANEL_GRAPHIC_LEFT_MARGIN * panel_scale
        )
        panel_y: int = round(self.PANEL_GRAPHIC_TOP_MARGIN * panel_scale)
        bottom_y: int = panel_y + round(
            (self._panel_height / self.ASSET_SCALE - 283.0) * panel_scale
        )
        dog_area_size: int = round(self.PANEL_DOG_AREA_SIZE * panel_scale)
        return panel_scale, panel_x, panel_y, bottom_y, dog_area_size

    def _draw_panel_background(self) -> None:
        """Draw the panel background (static, done once)."""
        _, panel_x, panel_y, _, _ = self._panel_layout()
        self._put_image(self._panel_scaled_image, panel_x, panel_y)

    def _draw_panel_dog(self) -> None:
        """Draw the current frame of the panel dog (dynamic)."""
        if self._panel_dog_start_scaled_image is None:
            return

        panel_scale, panel_x, _, bottom_y, dog_area_size = (
            self._panel_layout()
        )
        art_scale: float = panel_scale / self.ASSET_SCALE
        dog_width: int = max(
            1, round(self._panel_dog_start_width * panel_scale)
        )
        dog_height: int = max(
            1, round(self._panel_dog_start_height * panel_scale)
        )
        dog_x: int = panel_x + max(0, (dog_area_size - dog_width) // 2) + 30
        dog_y: int = bottom_y + max(0, (dog_area_size - dog_height) // 2) + 100
        panel_dogs: dict[str, Surface | None] = {
            "start": self._panel_dog_start_scaled_image,
            "1": self._panel_dog_1_scaled_image,
            "2": self._panel_dog_2_scaled_image,
            "3": self._panel_dog_3_scaled_image,
            "4": self._panel_dog_4_scaled_image,
        }
        self._put_image(panel_dogs[self._animation.panel_frame], dog_x, dog_y)

    def _draw_panel_text(self) -> None:
        """Draw the maze info texts inside the frame image."""
        panel_scale, panel_x, _, bottom_y, dog_area_size = (
            self._panel_layout()
        )
        info_x: int = panel_x + dog_area_size + round(25 * panel_scale)
        info_y: int = bottom_y + round(40 * panel_scale)
        line_step: int = max(18, round(24 * panel_scale))

        config: Config = self._config
        seed = config.seed if config.seed is not None else "random"
        algorithm = self.generator.algorithm.name
        # display = (
        #     config.display_mode.name if config.display_mode else "default"
        # )

        lines: tuple[str, ...] = (
            f"Size: {self._maze.width} x {self._maze.height}",
            f"Path: {'ON' if self._show_path else 'OFF'}",
            f"Perfect: {self._config.perfect}",
            f"Seed: {seed}",
            f"Algorithm: {algorithm}",
            # f"Display: {display}",
        )

        if self._frame is None:
            return

        for index, text in enumerate(lines, start=1):
            draw_text(
                self._frame,
                info_x,
                info_y + line_step * index,
                text if len(text) <= 21 else text[:18] + "...",
                self.TEXT_COLOR,
                panel_scale,
            )

    def _draw_animation_trail(self) -> None:
        """Draw the directional footprints left during the animated trip."""
        mark_images: dict[str, Surface | None] = {
            "N": self._mark_scaled_image,
            "E": self._mark_right_scaled_image,
            "S": self._mark_down_scaled_image,
            "W": self._mark_left_scaled_image,
        }

        for cell, direction in self._animation.trail:
            column, row = cell
            x = self._maze_x + column * self._cell_size
            y = self._maze_y + row * self._cell_size
            self._put_image(mark_images[direction], x, y)

    def _draw_animated_dog(self) -> None:
        """Draw the single moving dog while it is walking."""
        if self._animation.maze_state != "walking":
            return

        images: dict[str, Surface | None] = {
            "N": self._maze_dog_back_scaled_image,
            "E": self._maze_dog_right_scaled_image,
            "S": self._maze_dog_front_scaled_image,
            "W": self._maze_dog_left_scaled_image,
        }

        direction = self._animation.dog_direction or "S"
        column, row = self._animation.dog_cell

        x = self._maze_x + column * self._cell_size
        y = self._maze_y + row * self._cell_size

        self._put_image(images[direction], x, y)
