from mazegen.maze import Maze
import random
from enum import Enum


class AlgorithmType(str, Enum):
    DFS = "DFS"
    PRIM = "PRIM"


class MazeGenerator:
    def __init__(
        self, seed: None | str, perfect: bool, algorithm: None | AlgorithmType
    ) -> None:
        self.seed = seed
        self.perfect = perfect
        self.algorithm = algorithm

    def generate(self, maze: Maze) -> None:
        random.seed(self.seed)
        match (self.perfect, self.algorithm):
            case (True, None | AlgorithmType.DFS) | (
                None,
                AlgorithmType.DFS,
            ):
                self.dfs_generator(maze)
            case (True, AlgorithmType.PRIM) | (
                None,
                AlgorithmType.PRIM,
            ):
                self.prim_generator(maze)

    def dfs_generator(self, maze: Maze) -> None:
        start = random.choice(random.choice(maze.grid))
        start.visited = True
        stack = [start]
        while stack:
            nbrs = [
                cell
                for cell in maze.neighbors(stack[-1])
                if not cell.visited and not cell.logo42
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

    def prim_generator(self, maze: Maze) -> None:
        start = random.choice(random.choice(maze.grid))
        start.visited = True
        stack = [
            (cell, start)
            for cell in maze.neighbors(start)
            if not cell.visited and not cell.logo42
        ]
        while stack:
            next = random.choice(stack)
            next[0].visited = True
            maze.remove_wall(*next)
            stack += [(cell, next[0]) for cell in maze.neighbors(next[0])]
            stack = [
                tup
                for tup in stack
                if not tup[0].visited and not tup[0].logo42
            ]
