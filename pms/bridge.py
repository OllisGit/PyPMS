"""
Bridge between MQTT server/topic and InfluxDB server/database

Usage:
    pms.bridge [options]

Options:
    --MQTT_topic <topic>        MQTT root/topic [default: homie/+/+/+]
    --MQTT_host <host>          MQTT host server [default: mqtt.eclipse.org]
    --MQTT_port <port>          MQTT host port [default: 1883]
    --MQTT_user <username>      MQTT username
    --MQTT_pass <password>      MQTT password
    --InfluxDB_database <db>    InfluxDB database [default: homie]
    --InfluxDB_tags <dict>      InfluxDB measurement tags [default: {}]
    --InfluxDB_host <host>      InfluxDB host server [default: influxdb]
    --InfluxDB_port <port>      InfluxDB host port [default: 8086]
    --InfluxDB_user <username>  InfluxDB username [default: root]
    --InfluxDB_pass <password>  InfluxDB password [default: root]
    --help                      display this help and exit


NOTE:
Environment variables take precedence over command line options
- PMS_MQTT_TOPIC    overrides --MQTT_topic
- PMS_MQTT_HOST     overrides --MQTT_host
- PMS_MQTT_PORT     overrides --MQTT_port
- PMS_MQTT_USER     overrides --MQTT_user
- PMS_MQTT_PASS     overrides --MQTT_pass
- PMS_INFLUX_DB     overrides --InfluxDB_database
- PMS_INFLUX_TAGS   overrides --InfluxDB_tags
- PMS_INFLUX_HOST   overrides --InfluxDB_host
- PMS_INFLUX_PORT   overrides --InfluxDB_port
- PMS_INFLUX_USER   overrides --InfluxDB_user
- PMS_INFLUX_PASS   overrides --InfluxDB_pass
"""

from typing import Dict, List, Optional, Union, Any
from docopt import docopt
from pms import logger, mqtt, influxdb as db


def parse_args(args: Dict[str, str]) -> Dict[str, Any]:
    """Extract options from docopt output"""

    def get_opts(start: str) -> Dict[str, str]:
        """Extract MQTT/InfluxDB keywords"""
        d = {k.replace(start, "--"): v for k, v in args.items() if k.startswith(start)}
        d.update({"--serial": "/dev/null", "--interval": "0"})  # dummy values
        return d

    return dict(
        mqtt_=mqtt.parse_args(get_opts("--MQTT_")),
        db_=db.parse_args(get_opts("--InfluxDB_")),
    )


def main(mqtt_: Dict[str, Any], db_: Dict[str, Any]) -> None:
    pub = db.client_pub(**db_)

    def on_sensordata(data: mqtt.Data) -> None:
        pub(
            time=data.time,
            tags={"location": data.location},
            data={data.measurement: data.value},
        )

    mqtt.client_sub(on_sensordata=on_sensordata, **mqtt_)


def cli(argv: Optional[List[str]] = None) -> None:
    args = parse_args(docopt(__doc__, argv))
    main(**args)


if __name__ == "__main__":
    cli()
