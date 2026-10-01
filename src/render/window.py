import math
from typing import Literal
from pathlib import Path

from mazegen import Maze, MazeGenerator
from mlx import Mlx  # type: ignore[import-untyped]


ASSETS_DIR: Path = Path(__file__).resolve().parents[2] / "assets"


class Window:
    ESC_KEYCODE: int = 65307
    REGENERATE_KEYCODE: int = 114
    PATH_KEYCODE: int = 112
    COLOR_KEYCODE: int = 99
    CLOSE_EVENT: int = 33

    PATH_COLOR: int = 0xFFD43B
    WALL_COLOR_2: int = 0x8B5A2B
    TEXT_COLOR: int = 0xFFFFFF
    MUTED_TEXT_COLOR: int = 0xAAAAAA

    REFERENCE_SCREEN_WIDTH: int = 1920
    REFERENCE_SCREEN_HEIGHT: int = 1080
    REFERENCE_WINDOW_WIDTH: int = 1200
    GOLDEN_RATIO: float = (1 + math.sqrt(5)) / 2

    WALL_REFERENCE_CELL_SIZE: float = 64.0
    WALL_REFERENCE_WIDTH: int = 6

    def __init__(
        self,
        title: str,
        maze: Maze,
        generator: MazeGenerator,
    ) -> None:
        self._maze = maze
        self.generator = generator

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

        self._load_textures()

        self._closed: bool = False

        self._cell_size: float = 1.0
        self._border_size: float = 1.0
        self._maze_x: float = 0.0
        self._maze_y: float = 0.0
        self._grid_width: float = 0.0
        self._grid_height: float = 0.0

        self._stone_scaled_image: object | None = None
        self._wall_vertical_image: object | None = None
        self._wall_horizontal_image: object | None = None
        self._brick_top_image: object | None = None
        self._brick_bottom_image: object | None = None
        self._brick_left_image: object | None = None
        self._brick_right_image: object | None = None
        self._brick_top_left_image: object | None = None
        self._brick_top_right_image: object | None = None
        self._brick_bottom_left_image: object | None = None
        self._brick_bottom_right_image: object | None = None

        self._wall_thickness: int = 1
        self._wall_length: int = 1
        self._wall_overhang: int = 0
        self._show_path: bool = False
        self._wall_color: int | None = None

        self._calculate_geometry()
        self._rebuild_scaled_images()
        self._register_events()

        self._draw()

    def _load_textures(self) -> None:
        stone_path: str = str(ASSETS_DIR / "stone.xpm")
        wall_path: str = str(ASSETS_DIR / "wall.xpm")
        brick_path: str = str(ASSETS_DIR / "brick.xpm")

        stone_result = self._mlx.mlx_xpm_file_to_image(
            self._mlx_ptr,
            stone_path,
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
        if wall_result[0] is None:
            raise RuntimeError(f"Failed to load texture: {wall_path}")
        if brick_result[0] is None:
            raise RuntimeError(f"Failed to load texture: {brick_path}")

        self._stone_image = stone_result[0]
        self._stone_width = int(stone_result[1])
        self._stone_height = int(stone_result[2])

        self._wall_image = wall_result[0]
        self._wall_width = int(wall_result[1])
        self._wall_height = int(wall_result[2])

        self._brick_image = brick_result[0]
        self._brick_width = int(brick_result[1])
        self._brick_height = int(brick_result[2])

    def run(self) -> None:
        self._mlx.mlx_loop(self._mlx_ptr)

    def close(self) -> None:
        if self._closed:
            return

        self._closed = True
        self._mlx.mlx_loop_exit(self._mlx_ptr)

        self._destroy_scaled_images()

        self._mlx.mlx_destroy_image(
            self._mlx_ptr,
            self._stone_image,
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

    @staticmethod
    def _on_key(keycode: int, param: object) -> None:
        if not isinstance(param, Window):
            return

        if keycode == param.ESC_KEYCODE:
            param.close()
        elif keycode == param.REGENERATE_KEYCODE:
            param._regenerate()
        elif keycode == param.PATH_KEYCODE:
            param._toggle_path()
        elif keycode == param.COLOR_KEYCODE:
            param._change_wall_color()

    @staticmethod
    def _on_close(param: object) -> None:
        if not isinstance(param, Window):
            return
        param.close()

    def _regenerate(self) -> None:
        new_maze: Maze = Maze(
            self._maze.width,
            self._maze.height,
            self._maze.entry,
            self._maze.exit,
        )

        self.generator.generate(new_maze)
        self._maze = new_maze

        self._calculate_geometry()
        self._rebuild_scaled_images()
        self._draw()

    def _draw(self) -> None:
        self._mlx.mlx_clear_window(
            self._mlx_ptr,
            self._win_ptr,
        )

        # Draw the 42 cells first so their images cannot cover the walls.
        self._draw_cells()
        # Draw walls afterwards so every wall remains visible.
        self._draw_walls()
        # Bricks are a decorative outer frame and stay on top of the wall.
        self._draw_bricks()

        if self._show_path:
            self._draw_solution_path()

        self._draw_panel()

        self._mlx.mlx_do_sync(self._mlx_ptr)

    def _toggle_path(self) -> None:
        self._show_path = not self._show_path
        self._draw()

    def _change_wall_color(self) -> None:
        if self._wall_color is None:
            self._wall_color = self.WALL_COLOR_2
        else:
            self._wall_color = None

        self._rebuild_scaled_images()
        self._draw()

    def _rebuild_scaled_images(self) -> None:
        self._destroy_scaled_images()

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

        self._stone_scaled_image = self._create_scaled_image(
            self._stone_image,
            self._stone_width,
            self._stone_height,
            cell_size,
            cell_size,
            False,
            "stone",
        )

        self._wall_vertical_image = self._create_scaled_image(
            self._wall_image,
            self._wall_width,
            self._wall_height,
            self._wall_thickness,
            self._wall_length,
            False,
            "wall vertical",
            tint_color=self._wall_color,
        )

        self._wall_horizontal_image = self._create_scaled_image(
            self._wall_image,
            self._wall_width,
            self._wall_height,
            self._wall_length,
            self._wall_thickness,
            True,
            "wall horizontal",
            tint_color=self._wall_color,
        )

        self._brick_top_image = self._create_scaled_image(
            self._brick_image,
            self._brick_width,
            self._brick_height,
            brick_size,
            brick_half_size,
            False,
            "brick top",
            crop_width_ratio=1.0,
            crop_height_ratio=0.5,
            crop_x_start_ratio=0.0,
            crop_y_start_ratio=0.0,
        )

        self._brick_bottom_image = self._create_scaled_image(
            self._brick_image,
            self._brick_width,
            self._brick_height,
            brick_size,
            brick_half_size,
            False,
            "brick bottom",
            crop_width_ratio=1.0,
            crop_height_ratio=0.5,
            crop_x_start_ratio=0.0,
            crop_y_start_ratio=0.5,
        )

        self._brick_left_image = self._create_scaled_image(
            self._brick_image,
            self._brick_width,
            self._brick_height,
            brick_half_size,
            brick_size,
            False,
            "brick left",
            crop_width_ratio=0.5,
            crop_height_ratio=1.0,
            crop_x_start_ratio=0.0,
            crop_y_start_ratio=0.0,
        )

        self._brick_right_image = self._create_scaled_image(
            self._brick_image,
            self._brick_width,
            self._brick_height,
            brick_half_size,
            brick_size,
            False,
            "brick right",
            crop_width_ratio=0.5,
            crop_height_ratio=1.5,
            crop_x_start_ratio=0.5,
            crop_y_start_ratio=0.0,
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
            crop_height_ratio=0.5,
            crop_x_start_ratio=0.0,
            crop_y_start_ratio=0.0,
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
            crop_height_ratio=0.5,
            crop_x_start_ratio=0.5,
            crop_y_start_ratio=0.0,
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
            crop_height_ratio=0.5,
            crop_x_start_ratio=0.0,
            crop_y_start_ratio=0.5,
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
            crop_height_ratio=0.5,
            crop_x_start_ratio=0.5,
            crop_y_start_ratio=0.5,
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
    ) -> object:
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

        for destination_y in range(target_height):
            y_ratio: float = (
                destination_y / max(1, target_height - 1)
            )

            for destination_x in range(target_width):
                x_ratio: float = (
                    destination_x / max(1, target_width - 1)
                )

                if rotate_clockwise:
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

        return scaled_image

    def _destroy_scaled_images(self) -> None:
        scaled_images = (
            "_stone_scaled_image",
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
                    image,
                )
                setattr(self, name, None)

    def _put_image(
        self,
        image: object | None,
        x: float,
        y: float,
    ) -> None:
        if image is None:
            return

        self._mlx.mlx_put_image_to_window(
            self._mlx_ptr,
            self._win_ptr,
            image,
            round(x),
            round(y),
        )

    def _draw_cells(self) -> None:
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

    def _draw_walls(self) -> None:
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
        path: str = self._maze.shortest_path()

        column: int = self._maze.entry[0]
        row: int = self._maze.entry[1]
        size: int = max(2, int(self._cell_size * 0.25))

        for direction in path:
            if direction == "N":
                row -= 1
            elif direction == "E":
                column += 1
            elif direction == "S":
                row += 1
            elif direction == "W":
                column -= 1

            x: int = int(
                self._maze_x
                + column * self._cell_size
                + self._cell_size / 2
                - size / 2
            )
            y: int = int(
                self._maze_y
                + row * self._cell_size
                + self._cell_size / 2
                - size / 2
            )

            for current_y in range(y, y + size):
                for current_x in range(x, x + size):
                    self._mlx.mlx_pixel_put(
                        self._mlx_ptr,
                        self._win_ptr,
                        current_x,
                        current_y,
                        self.PATH_COLOR,
                    )

    def _draw_bricks(self) -> None:
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

    def _draw_panel(self) -> None:
        x: int = self._maze_size + 30

        self._mlx.mlx_string_put(
            self._mlx_ptr,
            self._win_ptr,
            x,
            55,
            self.TEXT_COLOR,
            "A-MAZE-ING",
        )
        self._mlx.mlx_string_put(
            self._mlx_ptr,
            self._win_ptr,
            x,
            85,
            self.MUTED_TEXT_COLOR,
            "Maze controls",
        )
        self._mlx.mlx_string_put(
            self._mlx_ptr,
            self._win_ptr,
            x,
            180,
            self.TEXT_COLOR,
            "R Regenerate",
        )
        self._mlx.mlx_string_put(
            self._mlx_ptr,
            self._win_ptr,
            x,
            220,
            self.TEXT_COLOR,
            "P Show / hide path",
        )
        self._mlx.mlx_string_put(
            self._mlx_ptr,
            self._win_ptr,
            x,
            260,
            self.TEXT_COLOR,
            "C Change wall colour",
        )
        self._mlx.mlx_string_put(
            self._mlx_ptr,
            self._win_ptr,
            x,
            330,
            self.MUTED_TEXT_COLOR,
            f"Size: {self._maze.width} x {self._maze.height}",
        )
        self._mlx.mlx_string_put(
            self._mlx_ptr,
            self._win_ptr,
            x,
            360,
            self.MUTED_TEXT_COLOR,
            f"Path: {'ON' if self._show_path else 'OFF'}",
        )
        self._mlx.mlx_string_put(
            self._mlx_ptr,
            self._win_ptr,
            x,
            400,
            self.MUTED_TEXT_COLOR,
            "ESC Exit",
        )
