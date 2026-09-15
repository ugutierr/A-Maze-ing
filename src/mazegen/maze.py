import logging
from collections import deque

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

    def get_bitmap(self) -> str:
        return "\n".join(
            [
                "".join([format(cell.get_bit(), "x") for cell in row])
                for row in self.grid
            ]
        )

    def shortest_path(self) -> str:
        for row in self.grid:  # habria que replantearlo
            for cell in row:
                cell.visited = False
        parent: dict[Cell, None | tuple[Cell, int]] = {self.entry_cell: None}
        self.entry_cell.visited = True

        queue = deque([self.entry_cell])
        while queue:
            prev = queue.popleft()
            if prev == self.exit_cell:
                break
            for i, cell in enumerate(self.neighbors(prev)):
                if cell is None or cell.visited or prev.get_bit() & (1 << i):
                    continue
                parent[cell] = (prev, i)
                cell.visited = True
                queue.append(cell)
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
        elif cell2 == self.east_cell(cell1):
            cell1.east = False
            cell2.west = False
        elif cell2 == self.south_cell(cell1):
            cell1.south = False
            cell2.north = False
        elif cell2 == self.west_cell(cell1):
            cell1.west = False
            cell2.east = False
        else:
            raise ValueError(
                "Cannot remove walls between non neighboring cells"
            )
