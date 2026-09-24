import logging
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)


class Cell:
    def __init__(self, row: int, column: int) -> None:
        self.row = row
        self.column = column
        self.north = True
        self.east = True
        self.south = True
        self.west = True
        self.visited = False
        self.logo42 = False

    def get_bit(self) -> int:
        return self.north * 1 + self.east * 2 + self.south * 4 + self.west * 8

    def degree(self) -> int:
        bit = self.get_bit()
        return 4 - sum((bit >> i) & 1 for i in range(4))


class Direction(Enum):
    NORTH = "N"
    EAST = "E"
    SOUTH = "S"
    WEST = "W"


class WallRemovalEvent:
    def __init__(
        self, c1: Cell, w1: Direction, c2: Cell, w2: Direction
    ) -> None:
        self.cell1 = (c1.column, c1.row)
        self.cell2 = (c2.column, c2.row)
        self.wall1 = w1
        self.wall2 = w2


class Maze:
    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int],
        exit: tuple[int, int],
    ) -> None:
        self.width = width
        self.height = height
        self.entry = entry
        self.exit = exit
        self.grid = [
            [Cell(row, col) for col in range(self.width)]
            for row in range(self.height)
        ]
        self.entry_cell = self.grid[self.entry[1]][self.entry[0]]
        self.exit_cell = self.grid[self.exit[1]][self.exit[0]]
        self.history: list[WallRemovalEvent] = []

    def get_bitmap(self) -> str:
        return "\n".join(
            [
                "".join([format(cell.get_bit(), "x") for cell in row])
                for row in self.grid
            ]
        )

    def shortest_path(self) -> str:
        parent: dict[Cell, tuple[Cell, int]] = {}
        self.entry_cell.visited = True

        queue = deque([self.entry_cell])
        while queue:
            prev = queue.popleft()
            if prev == self.exit_cell:
                break
            for i, c in enumerate(self.neighbors(prev)):
                if c is None or c.visited or prev.get_bit() & (1 << i):
                    continue
                parent[c] = (prev, i)
                c.visited = True
                queue.append(c)
        if not self.exit_cell.visited:
            logger.debug("Shortest path not found")
            return ""
        current = self.exit_cell
        path = []
        while current is not self.entry_cell:
            prev, direction = parent[current]
            path.append(["N", "E", "S", "W"][direction])
            current = prev
        for row in self.grid:
            for cell in row:
                cell.visited = False

        return "".join(reversed(path))

    def north_cell(self, cell: Cell) -> Cell | None:
        if cell.row == 0:
            return None
        return self.grid[cell.row - 1][cell.column]

    def south_cell(self, cell: Cell) -> Cell | None:
        if cell.row == self.height - 1:
            return None
        return self.grid[cell.row + 1][cell.column]

    def west_cell(self, cell: Cell) -> Cell | None:
        if cell.column == 0:
            return None
        return self.grid[cell.row][cell.column - 1]

    def east_cell(self, cell: Cell) -> Cell | None:
        if cell.column == self.width - 1:
            return None
        return self.grid[cell.row][cell.column + 1]

    def neighbors(self, cell: Cell) -> list[Cell | None]:
        return [
            self.north_cell(cell),
            self.east_cell(cell),
            self.south_cell(cell),
            self.west_cell(cell),
        ]

    def remove_wall(self, cell1: Cell, cell2: Cell) -> None:
        if cell2 == self.north_cell(cell1):
            cell1.north = False
            cell2.south = False
            self.history.append(
                WallRemovalEvent(
                    cell1, Direction.NORTH, cell2, Direction.SOUTH
                )
            )
        elif cell2 == self.east_cell(cell1):
            cell1.east = False
            cell2.west = False
            self.history.append(
                WallRemovalEvent(cell1, Direction.EAST, cell2, Direction.WEST)
            )
        elif cell2 == self.south_cell(cell1):
            cell1.south = False
            cell2.north = False
            self.history.append(
                WallRemovalEvent(
                    cell1, Direction.SOUTH, cell2, Direction.NORTH
                )
            )
        elif cell2 == self.west_cell(cell1):
            cell1.west = False
            cell2.east = False
            self.history.append(
                WallRemovalEvent(cell1, Direction.WEST, cell2, Direction.EAST)
            )
        else:
            raise ValueError(
                "Cannot remove walls between non neighboring cells"
            )
