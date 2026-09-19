from amz.mazegen import Maze, MazeGenerator
from amz.mlx.mlx import Mlx


class Window:
    ESC_KEYCODE: int = 65307
    REGENERATE_KEYCODE: int = 114
    PATH_KEYCODE: int = 112
    COLOR_KEYCODE: int = 99

    CLOSE_EVENT: int = 17

    BACKGROUND_COLOR: int = 0x101014
    PANEL_COLOR: int = 0x18181F
    WALL_COLOR: int = 0xFFFFFF
    WALL_COLOR_2: int = 0x00D9FF
    ENTRY_COLOR: int = 0x00FF3355
    EXIT_COLOR: int = 0xFF3355
    PATH_COLOR: int = 0xFFD43B
    LOGO_COLOR: int = 0x9B59FF
    TEXT_COLOR: int = 0xFFFFFF
    MUTED_TEXT_COLOR: int = 0xAAAAAA

    def __init__(
        self,
        width: int,
        height: int,
        title: str,
        maze_size: int,
        maze: Maze,
        generator: MazeGenerator,
    ) -> None:
        self.width = width
        self.height = height
        self.maze_size = maze_size
        self.maze = maze
        self.generator = generator

        self._mlx = Mlx()
        self._mlx_ptr = self._mlx.mlx_init()

        if self._mlx_ptr is None:
            raise RuntimeError("Filed to initialise MLX")

        self._win_ptr = self._mlx.mlx_new_window(
            self._mlx_ptr,
            self.width,
            self.height,
            title,
        )

        self._image = self._mlx.mlx_new_image(
            self._mlx_ptr,
            self.width,
            self.height,
        )

        self._image_data = self._mlx.mlx_get_data_addr(
            self._image,
        )

        if self._win_ptr is None:
            self._mlx.mlx_release(self._mlx_ptr)
            raise RuntimeError("Failed to create the window")

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
        print("ANTES DE DRAW")
        self._draw()
        print("DESPUES DE DRAW")

    def run(self) -> None:
        print("ENTRANDO EN MLX LOOP")
        self._mlx.mlx_loop(self._mlx_ptr)
        print("SALIENDO DE MLX LOOP:", result)

    def close(self) -> None:
        if self._closed:
            return

        self._closed = True

        self._mlx.mlx_destroy_window(self._mlx_ptr, self._mlx_ptr)
        self._mlx.mlx_release(self._mlx_ptr)

    def _calculate_geometry(self) -> None:
        rows: int = self.maze.height
        columns: int = self.maze.width

        if rows <= 15 and columns <= 15:
            self._cell_size = 32.0
        elif rows <= 35 and columns <= 35:
            self._cell_size = 16.0
        else:
            available_size: float = self.maze_size * 0.9

            width_size: float = available_size / (columns + 1)
            height_size: float = available_size / (rows + 1)

            self._cell_size = min(width_size, height_size)

            if self._cell_size < 2.0:
                self._cell_size = 2.0

        self._border_size = self._cell_size * 0.5

        self._grid_width = columns * self._cell_size
        self._grid_height = rows * self._cell_size

        total_width: float = (self._grid_width + self._border_size * 2)
        total_height: float = (self._grid_height + self._border_size * 2)

        self._maze_x = (
            self.maze_size - total_width
        ) / 2 + self._border_size

        self._maze_y = (
            self.maze_size - total_height
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
        new_maze: Maze = Maze(
            self.maze.width,
            self.maze.height,
            self.maze.entry,
            self.maze.exit,
        )

        self.generator.generate(new_maze)
        self.maze = new_maze
        self._show_path = False

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

    """
    def _draw(self) -> None:
        self._mlx.mlx_clear_window(
            self._mlx_ptr,
            self._mlx_ptr,
        )

        self._draw_background()
        self._draw_border()
        self._draw_cells()
        self._draw_walls()

        if self._show_path:
            self._draw_solution_path()

        self._draw_panel()
    """
    def _draw(self) -> None:
        """Redraw the complete window."""
        print("DRAW 1")

        self._mlx.mlx_clear_window(
            self._mlx_ptr,
            self._win_ptr,
        )

        print("DRAW 2")
        self._draw_background()

        print("DRAW 3")
        self._draw_border()

        print("DRAW 4")
        self._draw_cells()

        print("DRAW 5")
        self._draw_walls()

        print("DRAW 6")
        if self._show_path:
            self._draw_solution_path()

        print("DRAW 7")
        self._draw_panel()

        print("DRAW 8")

    def _draw_background(self) -> None:
        self._fill_rectangle(
            0,
            0,
            self.maze_size,
            self.height,
            self.BACKGROUND_COLOR,
        )

        self._fill_rectangle(
            self.maze_size,
            0,
            self.width - self.maze_size,
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
        thickness: int = max(1, int(self._cell_size * 0.08))

        for row in self.maze.grid:
            for cell in row:
                x: int = int(self._maze_x + cell.column * self._cell_size)
                y: int = int(self._maze_y + cell.row * self._cell_size)
                size: int = int(self._cell_size)

                if cell.north:
                    self._fill_rectangle(
                        x,
                        y,
                        size,
                        thickness,
                        self._wall_color,
                    )

                if cell.east:
                    self._fill_rectangle(
                        x + size - thickness,
                        y,
                        thickness,
                        size,
                        self._wall_color,
                    )

                if cell.south:
                    self._fill_rectangle(
                        x,
                        y + size - thickness,
                        size,
                        thickness,
                        self._wall_color,
                    )

                if cell.west:
                    self._fill_rectangle(
                        x,
                        y,
                        thickness,
                        size,
                        self._wall_color,
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
        x: int = self.maze_size + 30

        self._mlx.mlx_string_put(
            self._mlx_ptr,
            self._win_ptr,
            x,
            55,
            self.TEXT_COLOR,
            "A-MAZE-ING"
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
            "P Show / hide path"
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
