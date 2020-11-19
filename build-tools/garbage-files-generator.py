#!/usr/bin/env python

import argparse
import logging
import math
import os
import pathlib
import re
from functools import reduce

from rich.progress import Progress


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)-8s - %(filename)s:%(lineno)d |> %(message)s",
)


OUTPUT_FOLDER = pathlib.Path("./data")


def main():
    args = _parse_args()
    generate_data(
        args.total_size,
        args.files_count,
        args.branching_factor,
    )


def generate_data(
    total_size: int,
    files_count: int,
    branching_factor: int,
):
    file_size_bytes = math.ceil(total_size / files_count)
    tree_depth = math.floor(math.log(files_count, branching_factor))
    name_length = len(str(branching_factor))
    logging.info(
        f"Generating {files_count} files {file_size_bytes} bytes each, "
        f"which in total: {total_size} bytes."
    )

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    created_files = 0
    folders_counter = 0
    with Progress() as progress:
        data_gen_task = progress.add_task(
            "[green]Generating data...", total=files_count
        )
        while created_files < files_count:
            files_count_z = str(folders_counter).zfill(name_length * tree_depth)

            split_path = []
            for level in range(tree_depth):
                split_path.append(
                    files_count_z[name_length * level : name_length * (level + 1)]
                )

            folder_path = reduce(
                lambda parent, child: parent / child, (OUTPUT_FOLDER, *split_path)
            )

            folder_path.mkdir(parents=True, exist_ok=True)
            folders_counter += 1

            for i in range(branching_factor):
                if created_files < files_count:
                    file_name = str(i).zfill(name_length)
                    full_file_name = folder_path / file_name
                    with full_file_name.open("wb") as file:
                        file.write(os.urandom(file_size_bytes))
                    created_files += 1
                    progress.advance(data_gen_task)
                else:
                    break
        logging.info("Data generation completed.")


def _parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser()
    parser.add_argument("files_count", type=int)
    parser.add_argument("total_size", type=_parse_size)
    parser.add_argument("--branching-factor", type=int, default=100)
    return parser.parse_args()


def _parse_size(size: str) -> int:
    units = {"B": 1, "KB": 2 ** 10, "MB": 2 ** 20, "GB": 2 ** 30, "TB": 2 ** 40}
    size = size.upper()
    # print("parsing size ", size)
    if not re.match(r" ", size):
        size = re.sub(r"([KMGT]?B)", r" \1", size)
    number, unit = [string.strip() for string in size.split()]
    return int(float(number) * units[unit])


if __name__ == "__main__":
    main()
