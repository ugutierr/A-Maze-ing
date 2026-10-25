"""Control the maze dog and panel dog animations."""

from random import uniform
from time import monotonic
from typing import Literal, TypeAlias

from mazegen import Maze

Direction: TypeAlias = Literal["N", "E", "S", "W"]
MazeState: TypeAlias = Literal["idle", "walking", "exit", "finished"]
PanelMode: TypeAlias = Literal["idle", "standby", "end"]
PanelFrame: TypeAlias = Literal["start", "1", "2", "3", "4"]


class MazeAnimation:
    """Manage the maze dog movement and panel dog sequences."""

    MAZE_STEP_INTERVAL: float = 0.22
    MAZE_EXIT_INTERVAL: float = 0.18

    PANEL_STANDBY_INTERVAL: float = 0.20
    PANEL_END_INTERVAL: float = 0.05

    PANEL_MIN_WAIT: float = 60.0
    PANEL_MAX_WAIT: float = 90.0

    EXIT_FRAMES: tuple[int, ...] = (1, 2, 3, 2, 3, 2, 2, 3, 2, 1)

    PANEL_STANDBY_FRAMES: tuple[PanelFrame, ...] = (
        "start", "1", "2", "3", "4", "3", "2", "3", "4", "3", "2", "3",
        "4", "3", "2", "1", "start",
    )
    PANEL_END_FRAMES: tuple[PanelFrame, ...] = (
        "start", "1", "2", "3", "4", "3", "2", "3", "4", "3", "2", "3",
        "4", "3", "2", "1", "start", "1", "2", "3", "4", "3", "2", "1",
        "2", "3", "4", "3", "2", "1", "start",
    )

    def __init__(self, maze: Maze) -> None:
        """Initialize the animation state and standby timer."""
        self._maze = maze
        self._path = maze.shortest_path()

        self._maze_state: MazeState = "idle"
        self._dog_cell: tuple[int, int] = maze.entry
        self._dog_direction: Direction | None = None
        self._path_index: int = 0

        self._trail: list[tuple[tuple[int, int], Direction]] = []

        self._exit_frame: int | None = None
        self._exit_sequence_index: int = 0
        self._next_maze_frame_at: float = 0.0

        self._panel_mode: PanelMode = "idle"
        self._panel_frame: PanelFrame = "start"
        self._panel_sequence: tuple[PanelFrame, ...] = ()
        self._panel_sequence_index: int = 0
        self._next_panel_frame_at: float = 0.0
        self._next_standby_at: float = (
            monotonic()
            + uniform(self.PANEL_MIN_WAIT, self.PANEL_MAX_WAIT)
        )

    @property
    def maze_state(self) -> MazeState:
        """Return the current maze animation state."""
        return self._maze_state

    @property
    def dog_cell(self) -> tuple[int, int]:
        """Return the moving dog's current cell."""
        return self._dog_cell

    @property
    def dog_direction(self) -> Direction | None:
        """Return the dog's current movement direction."""
        return self._dog_direction

    @property
    def trail(self) -> list[tuple[tuple[int, int], Direction]]:
        """Return the directional footprints left by the dog"""
        return self._trail

    @property
    def exit_frame(self) -> int | None:
        """Return the current exit animation frame, if active."""
        return self._exit_frame

    @property
    def panel_frame(self) -> PanelFrame:
        """Return the current panel dog frame."""
        return self._panel_frame

    def reset_maze(self, maze: Maze) -> None:
        """Reset the maze animation without interrumping the panel."""
        self._maze = maze
        self._path = maze.shortest_path()

        self._maze_state = "idle"
        self._dog_cell = maze.entry
        self._dog_direction = None
        self._path_index = 0
        self._trail.clear()

        self._exit_frame = None
        self._exit_sequence_index = 0
        self._next_maze_frame_at = 0.0

    def start(self) -> bool:
        """Start or restart the dog's trip from entry to exit."""
        self._path = self._maze.shortest_path()

        if not self._path:
            return False

        self._maze_state = "walking"
        self._dog_cell = self._maze.entry
        self._dog_direction = None
        self._path_index = 0
        self._trail.clear()

        self._exit_frame = None
        self._exit_sequence_index = 0
        self._next_maze_frame_at = (monotonic() + self.MAZE_STEP_INTERVAL)
        return True

    def update(self) -> bool:
        """Update animation states when their timers expire."""
        now = monotonic()
        maze_changed = self._update_maze(now)
        panel_changed = self._update_panel(now)
        return maze_changed or panel_changed

    def _update_maze(self, now: float) -> bool:
        """Advanced the dog or update its exit sequence."""
        if self._maze_state == "walking":
            if now < self._next_maze_frame_at:
                return False

            if self._path_index >= len(self._path):
                return False

            direction_char = self._path[self._path_index]

            if direction_char == "N":
                direction: Direction = "N"
            elif direction_char == "E":
                direction = "E"
            elif direction_char == "S":
                direction = "S"
            elif direction_char == "W":
                direction = "W"
            else:
                return False

            if self._dog_cell not in (
                self._maze.entry,
                self._maze.exit,
            ):
                self._trail.append((self._dog_cell, direction))

            column, row = self._dog_cell

            if direction == "N":
                row -= 1
            elif direction == "E":
                column += 1
            elif direction == "S":
                row += 1
            else:
                column -= 1

            self._dog_cell = (column, row)
            self._dog_direction = direction
            self._path_index += 1

            if self._dog_cell == self._maze.exit:
                self._maze_state = "exit"
                self._exit_sequence_index = 0
                self._exit_frame = self.EXIT_FRAMES[0]
                self._next_maze_frame_at = (
                    now + self.MAZE_EXIT_INTERVAL
                )
                self._start_panel_end(now)
            else:
                self._next_maze_frame_at = (
                    now + self.MAZE_STEP_INTERVAL
                )

            return True

        if self._maze_state == "exit":
            if now < self._next_maze_frame_at:
                return False

            self._exit_sequence_index += 1
            self._exit_frame = self.EXIT_FRAMES[self._exit_sequence_index]

            if (self._exit_sequence_index == len(self.EXIT_FRAMES) - 1):
                self._maze_state = "finished"
            else:
                self._next_maze_frame_at = (
                    now + self.MAZE_EXIT_INTERVAL
                )

            return True

        return False

    def _start_panel_end(self, now: float) -> None:
        """Interrupt stanby and start the faster end sequence."""
        self._panel_mode = "end"
        self._panel_sequence = self.PANEL_END_FRAMES
        self._panel_sequence_index = 0
        self._panel_frame = "start"
        self._next_panel_frame_at = now + self.PANEL_END_INTERVAL

    def _update_panel(self, now: float) -> bool:
        """Advance the panel dog animation without blocking the window."""
        if self._panel_mode == "idle":
            if now < self._next_standby_at:
                return False

            self._panel_mode = "standby"
            self._panel_sequence = self.PANEL_STANDBY_FRAMES
            self._panel_sequence_index = 0
            self._panel_frame = "start"
            self._next_panel_frame_at = (
                now + self.PANEL_STANDBY_INTERVAL
            )
            return True

        if now < self._next_panel_frame_at:
            return False

        self._panel_sequence_index += 1
        self._panel_frame = self._panel_sequence[
            self._panel_sequence_index
        ]

        if (self._panel_sequence_index == len(self._panel_sequence) - 1):
            self._panel_mode = "idle"
            self._next_standby_at = (
                now
                + uniform(self.PANEL_MIN_WAIT, self.PANEL_MAX_WAIT)
            )
        else:
            interval = (
                self.PANEL_STANDBY_INTERVAL
                if self._panel_mode == "standby"
                else self.PANEL_END_INTERVAL
            )
            self._next_panel_frame_at = now + interval

        return True
