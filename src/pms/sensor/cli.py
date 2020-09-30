from csv import DictReader, DictWriter
from enum import Enum
from datetime import datetime
from pathlib import Path
from textwrap import wrap

from typing import Optional
from typer import Context, Option, Argument, echo, secho, colors, Abort

from pms import logger
from pms.sensor import Sensor, SensorReader


class Format(str, Enum):
    csv = "csv"
    pm = "pm"
    num = "num"
    raw = "raw"
    cf = "cf"
    atm = "atm"
    hcho = "hcho"
    bme = "bme"
    bsec = "bsec"


def serial(
    ctx: Context,
    format: Optional[Format] = Option(None, "--format", "-f", help="formatted output"),
):
    """Read sensor and print measurements"""
    with ctx.obj["reader"] as reader:
        if format:
            if format == "csv":
                obs = next(reader())
                echo(f"{obs:header}")
            for obs in reader():
                echo(f"{obs:{format}}")
        else:  # pragma: no cover
            for obs in reader():
                echo(str(obs))


def csv(
    ctx: Context,
    capture: bool = Option(False, "--capture", help="write raw messages instead of observations"),
    overwrite: bool = Option(False, "--overwrite", help="overwrite file, if already exists"),
    path: Path = Argument(Path(), help="csv formatted file", show_default=False),
):
    """Read sensor and print measurements"""
    if path.is_dir():
        path /= f"{datetime.now():%F}_pypms.csv"
    mode = "w" if overwrite else "a"
    logger.debug(f"open {path} on '{mode}' mode")
    with ctx.obj["reader"] as reader, path.open(mode) as csv:
        sensor_name = reader.sensor.name
        if not capture:
            logger.debug(f"capture {sensor_name} observations to {path}")
            # add header to new files
            if path.stat().st_size == 0:
                obs = next(reader())
                csv.write(f"{obs:header}\n")
            for obs in reader():
                csv.write(f"{obs:csv}\n")
        else:
            logger.debug(f"capture {sensor_name} messages to {path}")
            writer = DictWriter(csv, fieldnames="time sensor hex".split())
            # add header to new files
            if path.stat().st_size == 0:
                writer.writeheader()
            for raw in reader(raw=True):
                writer.writerow(
                    dict(
                        time=int(datetime.now().timestamp()),
                        sensor=sensor_name,
                        hex=raw.hex(),  # type: ignore
                    )
                )


def _decode(sensor: Sensor, path: Path):
    secho(f"decode {sensor.name} messages from {path}", fg=colors.GREEN, bold=True)
    if not path.is_file():  # pragma: no cover
        secho(f"{path} is not a capture file", fg=colors.RED)
        echo(f"try something like\n\tpms -s PMS_CAPTURE_FILE.csv -m PMS_SENSOR raw --decode")
        Abort()
    with path.open() as csv:
        reader = DictReader(csv)
        for row in reader:
            if row["sensor"] != sensor.name:  # pragma: no cover
                continue
            echo(sensor.decode(bytes.fromhex(row["hex"]), time=int(row["time"])))


def raw(
    ctx: Context,
    decode: bool = Option(False, "--decode", help="process messages from file"),
    hexdump: bool = Option(False, "--hexdump", help="print in hexdump format"),
    path: Optional[Path] = Option(None, "--test-file", hidden=True),
):
    """Capture raw sensor messages"""
    reader = ctx.obj["reader"]
    if decode:
        _decode(reader.sensor, path or Path(reader.serial.port))
    elif hexdump:  # pragma: no cover
        table = bytes.maketrans(
            bytes(range(0x20)) + bytes(range(0x7E, 0x100)), b"." * (0x20 + 0x100 - 0x7E)
        )
        with reader:
            for n, raw in enumerate(reader(raw=True)):
                msg = " ".join(wrap(raw.hex(), 2))  # raw.hex(" ") in python3.8+
                prt = raw.translate(table).decode()
                echo(f"{n*len(raw):08x}: {msg}  {prt}")
    else:
        with reader:
            for raw in reader(raw=True):
                echo(raw.hex())
