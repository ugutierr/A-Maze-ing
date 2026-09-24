import math

from mlx import Mlx

from mazegen import Maze, MazeGenerator


class Window:
    ESC_KEYCODE: int = 65307
    REGENERATE_KEYCODE: int = 114
    PATH_KEYCODE: int = 112
    COLOR_KEYCODE: int = 99

    CLOSE_EVENT: int = 33

    BACKGROUND_COLOR: int = 0x101014
    PANEL_COLOR: int = 0x18181F
    WALL_COLOR: int = 0xFFFFFF
    WALL_COLOR_2: int = 0xFF8B5A2B
    ENTRY_COLOR: int = 0x00FF3355
    EXIT_COLOR: int = 0xFF3355
    PATH_COLOR: int = 0xFFD43B
    LOGO_COLOR: int = 0x9B59FF
    TEXT_COLOR: int = 0xFFFFFF
    MUTED_TEXT_COLOR: int = 0xAAAAAA

    REFERENCE_SCREEN_WIDTH: int = 1920
    REFERENCE_SCREEN_HEIGHT: int = 1080

    REFERENCE_WINDOW_WIDTH: int = 1200

    GOLDEN_RATIO: float = (1 + math.sqrt(5)) / 2

    def __init__(
        self,
        title: str,
        maze: Maze,
        generator: MazeGenerator,
    ) -> None:
        self.maze = maze
        self.generator = generator

        self._mlx = Mlx()
        self._mlx_ptr = self._mlx.mlx_init()

        if self._mlx_ptr is None:
            raise RuntimeError("Failed to initialise MLX")

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

        self._image = self._mlx.mlx_new_image(
            self._mlx_ptr,
            self.width,
            self.height,
        )

        if self._image is None:
            self._mlx.mlx_destroy_window(
                self._mlx_ptr,
                self._win_ptr,
            )
            self._mlx.mlx_release(self._mlx_ptr)
            raise RuntimeError("Failed to created the image")

        self._image_data = self._mlx.mlx_get_data_addr(self._image)

        self._image_buffer = self._image_data[0]
        self._bits_per_pixel = self._image_data[1]
        self._size_line = self._image_data[2]

        self._show_path: bool = False
        self._wall_color: int = self.WALL_COLOR
        self._closed: bool = False

        self._cell_size: float = 1.0
        self._border_size: float = 1.0
        self._maze_x: float = 0.0
        self._maze_y: float = 0.0
        self._grid_width: float = 0.0
        self._grid_height: float = 0.0

        self._calculate_geometry()
        self._register_events()

        self._draw()

    def run(self) -> None:
        self._mlx.mlx_loop(self._mlx_ptr)

    def close(self) -> None:
        if self._closed:
            return

        self._closed = True

        self._mlx.mlx_loop_exit(self._mlx_ptr)
        self._mlx.mlx_destroy_window(self._mlx_ptr, self._win_ptr)
        self._mlx.mlx_release(self._mlx_ptr)

    def _get_window_size(self) -> tuple[int, int]:
        result: int
        screen_width: int
        screen_height: int

        result, screen_width, screen_height = self._mlx.mlx_get_screen_size(
            self._mlx_ptr
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
        rows: int = self.maze.height
        columns: int = self.maze.width
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

        self._maze_x = (self._maze_size - total_width) / 2 + self._border_size

        self._maze_y = (self._maze_size - total_height) / 2 + self._border_size

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
            self.maze.width,
            self.maze.height,
            self.maze.entry,
            self.maze.exit,
        )

        self.generator.generate(new_maze)
        self.maze = new_maze

        self._calculate_geometry()
        self._draw()

    def _toggle_path(self) -> None:
        self._show_path = not self._show_path
        self._draw()

    def _change_wall_color(self) -> None:
        if self._wall_color == self.WALL_COLOR:
            self._wall_color = self.WALL_COLOR_2
        else:
            self._wall_color = self.WALL_COLOR

        self._draw()

    def _draw(self) -> None:
        self._mlx.mlx_clear_window(
            self._mlx_ptr,
            self._win_ptr,
        )

        self._draw_walls()

        self._mlx.mlx_do_sync(self._mlx_ptr)

    def _draw_background(self) -> None:
        self._fill_rectangle(
            0,
            0,
            self._maze_size,
            self.height,
            self.BACKGROUND_COLOR,
        )

        self._fill_rectangle(
            self._maze_size,
            0,
            self.width - self._maze_size,
            self.height,
            self.PANEL_COLOR,
        )

    def _draw_border(self) -> None:
        border: int = max(1, int(self._border_size))

        self._fill_rectangle(
            int(self._maze_x - border),
            int(self._maze_y - border),
            int(self._grid_width + border * 2),
            border,
            self.WALL_COLOR,
        )

        self._fill_rectangle(
            int(self._maze_x - border),
            int(self._maze_y + self._grid_height),
            int(self._grid_width + border * 2),
            border,
            self.WALL_COLOR,
        )

        self._fill_rectangle(
            int(self._maze_x - border),
            int(self._maze_y),
            border,
            int(self._grid_height),
            self.WALL_COLOR,
        )

        self._fill_rectangle(
            int(self._maze_x + self._grid_width),
            int(self._maze_y),
            border,
            int(self._grid_height),
            self.WALL_COLOR,
        )

    def _draw_cells(self) -> None:
        for row in self.maze.grid:
            for cell in row:
                if cell.logo42:
                    self._draw_cell(
                        cell.column,
                        cell.row,
                        self.LOGO_COLOR,
                    )

        self._draw_cell(
            self.maze.entry_cell.column,
            self.maze.entry_cell.row,
            self.ENTRY_COLOR,
        )

        self._draw_cell(
            self.maze.exit_cell.column,
            self.maze.exit_cell.row,
            self.EXIT_COLOR,
        )

    def _draw_cell(
        self,
        column: int,
        row: int,
        color: int,
    ) -> None:
        x: int = int(self._maze_x + column * self._cell_size)
        y: int = int(self._maze_y + row * self._cell_size)
        size: int = max(1, int(self._cell_size))

        self._fill_rectangle(x, y, size, size, color)

    def _draw_walls(self) -> None:
        color: int = self.WALL_COLOR_2

        for row in self.maze.grid:
            for cell in row:
                x0: int = round(self._maze_x + cell.column * self._cell_size)
                x1: int = round(
                    self._maze_x + (cell.column + 1) * self._cell_size
                )
                y0: int = round(self._maze_y + cell.row * self._cell_size)
                y1: int = round(
                    self._maze_y + (cell.row + 1) * self._cell_size
                )

                if cell.north:
                    for x in range(x0, x1 + 1):
                        self._mlx.mlx_pixel_put(
                            self._mlx_ptr,
                            self._win_ptr,
                            x,
                            y0,
                            color,
                        )

                if cell.west:
                    for y in range(y0, y1 + 1):
                        self._mlx.mlx_pixel_put(
                            self._mlx_ptr,
                            self._win_ptr,
                            x0,
                            y,
                            color,
                        )

                if cell.row == self.maze.height - 1 and cell.south:
                    for x in range(x0, x1 + 1):
                        self._mlx.mlx_pixel_put(
                            self._mlx_ptr,
                            self._win_ptr,
                            x,
                            y1,
                            color,
                        )

                if cell.column == self.maze.width - 1 and cell.east:
                    for y in range(y0, y1 + 1):
                        self._mlx.mlx_pixel_put(
                            self._mlx_ptr,
                            self._win_ptr,
                            x1,
                            y,
                            color,
                        )

    def _draw_solution_path(self) -> None:
        path: str = self.maze.shortest_path()

        column: int = self.maze.entry[0]
        row: int = self.maze.entry[1]

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
                + column * self._cell_size
                + self._cell_size / 2
                - size / 2
            )

            self._fill_rectangle(
                x,
                y,
                size,
                size,
                self.PATH_COLOR,
            )

    def _draw_panel(self) -> None:
        x: int = self._maze_size + 30

        self._mlx.mlx_string_put(
            self._mlx_ptr, self._win_ptr, x, 55, self.TEXT_COLOR, "A-MAZE-ING"
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
            f"Size: {self.maze.width} x {self.maze.height}",
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

    def _fill_rectangle(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: int,
    ) -> None:
        if width <= 0 or height <= 0:
            return

        for current_y in range(y, y + height):
            for current_x in range(x, x + width):
                self._mlx.mlx_pixel_put(
                    self._mlx_ptr,
                    self._win_ptr,
                    current_x,
                    current_y,
                    color,
                )
