from datetime import datetime
from typing import Dict, Union, Callable, NamedTuple
from paho.mqtt import client
from typer import Context, Option
from .. import logger


def client_pub(
    *, topic: str, host: str, port: int, username: str, password: str
) -> Callable[[Dict[str, Union[int, str]]], None]:
    c = client.Client(topic)
    c.enable_logger(logger)
    if username:
        c.username_pw_set(username, password)

    c.on_connect = lambda client, userdata, flags, rc: client.publish(
        f"{topic}/$online", "true", 1, True
    )
    c.will_set(f"{topic}/$online", "false", 1, True)
    c.connect(host, port, 60)
    c.loop_start()

    def pub(data: Dict[str, Union[int, str]]) -> None:
        for k, v in data.items():
            c.publish(f"{topic}/{k}", v, 1, True)

    return pub


class Data(NamedTuple):
    time: int
    location: str
    measurement: str
    value: float

    @staticmethod
    def now() -> int:
        """current time as seconds since epoch"""
        return int(datetime.now().timestamp())

    @classmethod
    def decode(cls, topic: str, payload: str, *, time: int = None) -> "Data":
        """Decode a MQTT message

        For example
        >>> decode("homie/test/pm10/concentration", "27")
        >>> Data(now(), "test", "pm10", 27)
        """
        if not time:
            time = cls.now()

        fields = topic.split("/")
        if len(fields) != 4:
            raise UserWarning(f"topic total length: {len(fields)}")
        if any([f.startswith("$") for f in fields]):
            raise UserWarning(f"system topic: {topic}")
        location, measurement = fields[1:3]

        try:
            value = float(payload)
        except ValueError:
            raise UserWarning(f"non numeric payload: {payload}")
        else:
            return cls(time, location, measurement, value)


def client_sub(
    topic: str,
    host: str,
    port: int,
    username: str,
    password: str,
    *,
    on_sensordata: Callable[[Data], None],
) -> None:
    def on_message(client, userdata, msg):
        try:
            data = Data.decode(msg.topic, msg.payload)
        except UserWarning as e:
            logger.debug(e)
        else:
            on_sensordata(data)

    c = client.Client(topic)
    c.enable_logger(logger)
    if username:
        c.username_pw_set(username, password)

    c.on_connect = lambda client, userdata, flags, rc: client.subscribe(topic)
    c.on_message = on_message
    c.connect(host, port, 60)
    c.loop_forever()


def mqtt(
    ctx: Context,
    topic: str = Option("homie/test", "--topic", "-t", help="mqtt root/topic"),
    host: str = Option("mqtt.eclipse.org", "--mqtt-host", help="mqtt server"),
    port: int = Option(1883, "--mqtt-port", help="server port"),
    user: str = Option("", "--mqtt-user", help="server username", show_default=False),
    word: str = Option("", "--mqtt-pass", help="server password", show_default=False),
):
    """Read sensor and push PM measurements to a MQTT server"""
    pub = client_pub(topic=topic, host=host, port=port, username=user, password=word)
    for k, v in {"pm01": "PM1", "pm25": "PM2.5", "pm10": "PM10"}.items():
        pub(
            {
                f"{k}/$type": v,
                f"{k}/$properties": "sensor,unit,concentration",
                f"{k}/sensor": ctx.obj["reader"].sensor.name,
                f"{k}/unit": "ug/m3",
            }
        )
    with ctx.obj["reader"] as reader:
        for obs in reader():
            pub({f"{k}/concentration": v for k, v in obs.subset("pm").items()})