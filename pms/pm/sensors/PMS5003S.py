"""
Plantower PMS5003S sensors
- messages are 32b long
- 6 size bins (as PMS5003) and HCHO concentration
"""
from dataclasses import dataclass
from typing import Dict
from . import PMS3003, PMSx003


commands = PMSx003.commands


class Message(PMS3003.Message):
    """Messages from Plantower PMS5003S sensors"""

    data_records = slice(13)


@dataclass(frozen=False)
class ObsData(PMSx003.ObsData):
    """Observations from Plantower PMS5003S sensors
    
    time                                    measurement time [seconds since epoch]
    raw01, raw25, raw10                     cf=1 PM estimates [ug/m3]
    pm01, pm25, pm10                        PM1.0, PM2.5, PM10 [ug/m3]
    n0_3, n0_5, n1_0, n2_5, n5_0, n10_0     number concentrations under X.Y um [#/cm3]
    HCHO                                    formaldehyde concentration [ug/m3]
    """

    # datasheet says [1/1000 mg/m3], which is [ug/m3]
    HCHO: int

    def __format__(self, spec: str) -> str:
        if spec in ["pm", "raw", "cf", "num"]:
            return PMSx003.ObsData.__format__(self, spec)
        if spec == "csv":
            csv = PMSx003.ObsData.__format__(self, spec)
            return f"{csv}, {self.HCHO}"
        if spec == "hcho":
            return f"{self.date:%F %T}: HCHO {self.HCHO} ug/m3"
        raise ValueError(
            f"Unknown format code '{spec}' "
            f"for object of type '{__name__}.{self.__class__.__name__}'"
        )
