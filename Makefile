# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    Makefile                                           :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: ugutierr <ugutierr@student.42.fr>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/11 15:01:02 by ugutierr          #+#    #+#              #
#    Updated: 2026/09/11 15:28:25 by ugutierr         ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

intall:
	uv sync

run: install
	uv run python3 a_maze_ing.py

debug:

clean:
	find . -type d -name "__pycache__" -not -path "./.venv/*"\
	-prune -exec rm -rf {} +
	rm -rf maze.txt

lint: install
	uv run flake8 .
	uv run mypy . --warn-return-any --warn-unused-ignores\
	--ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict: install
	uv run flake8 .
	uv run mypy . --strict


test: run
	python3 tests/maze_analyzer.py maze.txt 

.PHONY: install run debug lint lint-strict run
