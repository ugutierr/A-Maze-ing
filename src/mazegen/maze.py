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
        return self.north * 8 + self.east * 4 + self.south * 2 + self.west


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

    def get_bitmap(self) -> str:
        return "\n".join(
            [
                "".join([format(cell.get_bit(), "x") for cell in row])
                for row in self.grid
            ]
        )

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

    def neighbors(self, cell: Cell) -> list[Cell]:
        nbrs = [
            self.north_cell(cell),
            self.east_cell(cell),
            self.south_cell(cell),
            self.west_cell(cell),
        ]
        return [cell for cell in nbrs if cell is not None]

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
