# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    Makefile                                           :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: ugutierr <ugutierr@student.42.fr>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/11 15:01:02 by ugutierr          #+#    #+#              #
#    Updated: 2026/09/19 14:30:20 by ugutierr         ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

CONFIG ?= config.example.txt

MYPY_FLAGS = \
	--warn-return-any \
	--warn-unused-ignores \
	--ignore-missing-imports \
	--disallow-untyped-defs \
	--check-untyped-defs

MYPY_EXCLUDE = --exclude '(^|/)mlx/'

FLAKE8_FLAGS = --exclude=mlx


run: install
	uv run python3 a_maze_ing.py $(CONFIG)

install:
	uv sync

debug: install
	uv run python3 -m pdb a_maze_ing.py $(CONFIG)

clean:
	find . -type d -name "__pycache__" -not -path "./.venv/*"\
	-prune -exec rm -rf {} +
	rm -f maze.txt

flake8:
	uv run flake8 . $(FLAKE8_FLAGS)

lint: install flake8
	uv run mypy . $(MYPY_FLAGS) $(MYPY_EXCLUDE)

lint-strict: install flake8
	uv run mypy . --strict $(MYPY_EXCLUDE)


test: install
	uv run pytest tests/
	uv run python3 tests/maze_analyzer.py maze.txt 

.PHONY: install run debug lint lint-strict run clean flake8 
