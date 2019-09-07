"""
Choose one of the following strategies

Run pytest as a module
$ python3 -m pytest test/

Install locally before testing
$ pip install -e .
$ pytest test/
"""
import time
import pytest

try:
    from pms import SensorData
except ModuleNotFoundError as e:
    print(__doc__)
    raise


def test_format():
    sec, raw = 1567198523, tuple(range(9))
    obs = SensorData(sec, *raw)

    _time = time.strftime("%F %T", time.localtime(sec))
    assert obs.timestamp() == _time, "format: timestamp"

    for fmt in ["", "4", "04"]:
        _fmt = "{:" + fmt + "d}"

        _obs = f"{obs:{fmt}csv}"
        _raw = ", ".join(map(_fmt.format, raw))
        assert _obs == f"{sec}, {_raw}", f"format: '{fmt}csv'"

        _obs = f"{obs:{fmt}pm}"
        _raw = f"PM1 {_fmt}, PM2.5 {_fmt}, PM10 {_fmt} ug/m3".format(*raw[:4])
        assert _obs == f"{_time}: {_raw}", f"format: '{fmt}pm'"

        _obs = f"{obs:{fmt}num}"
        _raw = (
            f"N0.3 {_fmt}, N0.5 {_fmt}, N1.0 {_fmt}, "
            f"N2.5 {_fmt}, N5.0 {_fmt}, N10 {_fmt} #/100cc"
        ).format(*raw[3:])
        assert _obs == f"{_time}: {_raw}", f"format: '{fmt}num'"


def test_decode():
    sec = 1567201793
    buffer = b"\x42\x4D\x00\x1c\x00\x05\x00\r\x00\x16\x00\x05\x00\r\x00\x16\x02\xfd\x00\xfc\x00\x1d\x00\x0f\x00\x06\x00\x06\x97\x00\x03\xc5"
    msg = (5, 13, 22, 765, 252, 29, 15, 6, 6)
    assert SensorData.decode(buffer, time=sec) == SensorData(sec, *msg)

    with pytest.raises(Exception) as e:
        msg_len = 10
        SensorData.decode(buffer[:msg_len], time=sec)
    assert str(e.value).startswith("message length")

    with pytest.raises(Exception) as e:
        buffer = b"\x42\x4D\x00\x04\xe1\x00\x01t\x42\x4D\x00\x1c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        SensorData.decode(buffer, time=sec)
    assert str(e.value).startswith("message header")

    with pytest.raises(Exception) as e:
        buffer = b"\x42\x4D\x00\x1c\x00\x05\x00\r\x00\x16\x00\x05\x00\r\x00\x16\x02\xfd\x00\xfc\x00\x1d\x00\x0f\x00\x06\x00\x06\x97\x00\x00\x00"
        SensorData.decode(buffer, time=sec)
    assert str(e.value).startswith("message checksum")
