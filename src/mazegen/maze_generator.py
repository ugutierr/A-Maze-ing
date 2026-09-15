from mazegen.maze import Maze, Cell
import random
from enum import Enum


class AlgorithmType(str, Enum):
    DFS = "DFS"
    PRIM = "PRIM"
    PACMAN = "PACMAN"


class MazeGenerator:
    def __init__(
        self, seed: None | str, perfect: bool, algorithm: None | AlgorithmType
    ) -> None:
        self.seed = seed
        self.perfect = perfect
        self.algorithm = algorithm

    def generate(self, maze: Maze) -> None:
        random.seed(self.seed)
        self._gen_42logo(maze)
        match (self.perfect, self.algorithm):
            case (True, None | AlgorithmType.DFS) | (
                None,
                AlgorithmType.DFS,
            ):
                self._dfs_generator(maze)
            case (True, AlgorithmType.PRIM) | (
                None,
                AlgorithmType.PRIM,
            ):
                self._prim_generator(maze)
            case (False, None | AlgorithmType.PACMAN):
                self._pacman_generator(maze)
            case _:
                raise ValueError("Could no determine generator algorithm")

    def _gen_42logo(self, maze: Maze) -> None:
        x, y = maze.width // 2, maze.height // 2
        logo4 = [
            (x - 1, y),
            (x - 2, y),
            (x - 3, y),
            (x + 3, y + 1),
            (x + 3, y + 2),
            (x + 1, y - 1),
            (x + 1, y - 2),
        ]
        logo2 = [
            (x + 3, y),
            (x + 2, y),
            (x + 1, y),
            (x + 3, y + 2),
            (x + 2, y + 2),
            (x + 1, y + 2),
            (x + 3, y - 2),
            (x + 2, y - 2),
            (x + 1, y - 2),
            (x + 1, y - 1),
            (x + 3, y + 1),
        ]
        for i, j in logo4 + logo2:
            maze.grid[j][i].logo42 = True

    def _dfs_generator(self, maze: Maze) -> None:
        start = random.choice(random.choice(maze.grid))
        start.visited = True
        stack = [start]
        while stack:
            nbrs = [
                cell
                for cell in maze.neighbors(stack[-1])
                if cell is not None and not cell.visited and not cell.logo42
            ]
            if not nbrs:
                stack.pop()
            else:
                next = random.choice(nbrs)
                next.visited = True
                maze.remove_wall(stack[-1], next)
                stack.append(next)
        for row in maze.grid:
            for cell in row:
                cell.visited = False

    def _prim_generator(self, maze: Maze) -> None:
        start = random.choice(random.choice(maze.grid))
        start.visited = True
        stack = [
            (cell, start)
            for cell in maze.neighbors(start)
            if cell is not None and not cell.visited and not cell.logo42
        ]
        while stack:
            next = random.choice(stack)
            next[0].visited = True
            maze.remove_wall(*next)
            stack += [
                (cell, next[0])
                for cell in maze.neighbors(next[0])
                if cell is not None
            ]
            stack = [
                tup
                for tup in stack
                if not tup[0].visited and not tup[0].logo42
            ]
        for row in maze.grid:
            for cell in row:
                cell.visited = False

    def _pacman_generator(self, maze: Maze) -> None:
        self._dfs_generator(maze)
        x = maze.width // 2
        y = maze.height // 2
        mandatory_corridors: list[tuple[Cell, Cell]] = [
            (maze.grid[0][0], maze.grid[0][1]),
            (maze.grid[0][0], maze.grid[1][0]),
            (maze.grid[maze.height - 1][0], maze.grid[maze.height - 2][0]),
            (maze.grid[maze.height - 1][0], maze.grid[maze.height - 1][1]),
            (
                maze.grid[maze.height - 1][maze.width - 1],
                maze.grid[maze.height - 2][maze.width - 1],
            ),
            (
                maze.grid[maze.height - 1][maze.width - 1],
                maze.grid[maze.height - 1][maze.width - 2],
            ),
            (maze.grid[0][maze.width - 1], maze.grid[0][maze.width - 2]),
            (maze.grid[0][maze.width - 1], maze.grid[1][maze.width - 1]),
            (maze.grid[y][x], maze.grid[y + 1][x]),
            (maze.grid[y][x], maze.grid[y - 1][x]),
        ]
        for cell1, cell2 in mandatory_corridors:
            maze.remove_wall(cell1, cell2)
        dead_ends = [
            cell
            for row in maze.grid
            for cell in row
            if not cell.logo42 and cell.degree() == 1
        ]
        while dead_ends:
            dead_end = random.choice(dead_ends)
            nbrs = [
                cell
                for i, cell in enumerate(maze.neighbors(dead_end))
                if cell is not None
                and not cell.logo42
                and dead_end.get_bit() & 1 << i
            ]
            if nbrs:
                maze.remove_wall(dead_end, random.choice(nbrs))
            dead_ends.remove(dead_end)
