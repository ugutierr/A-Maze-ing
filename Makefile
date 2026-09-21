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

MYPY_EXCLUDE = --exclude '(^|/)mlx|.venv/'

FLAKE8_FLAGS = --exclude=mlx,.venv

MODULE = mazegen-1.0.0-py3-none-any.whl



install: $(MODULE)
	uv sync

run: install
	uv run python3 a_maze_ing.py $(CONFIG)

$(MODULE):
	uv build

debug: install
	uv run python3 -m pdb a_maze_ing.py $(CONFIG)

clean:
	find . -type d \( -name "__pycache__" -o -name ".mypy_cache" \) \
  -not -path "./.venv/*" -prune -exec rm -rf {} +
	rm -f maze.txt
	rm -rf dist/

flake8:
	uv run flake8 . $(FLAKE8_FLAGS)

lint: install flake8
	uv run mypy . $(MYPY_FLAGS) $(MYPY_EXCLUDE)

lint-strict: install flake8
	uv run mypy . --strict $(MYPY_EXCLUDE)


test: install
	uv run pytest tests/
	uv run python3 tests/maze_analyzer.py maze.txt 

tree: 
	tree -a -I '.git|.venv'

kill:
	kill "$$(ps aux | grep "a_maze_ing" | awk 'NF {print $$2; exit}')"


.PHONY: install run debug lint lint-strict run clean flake8 tree
