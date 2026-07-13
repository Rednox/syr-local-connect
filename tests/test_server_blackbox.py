import os
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import pytest

ENDPOINT_BASIC = "/WebServices/SyrConnectLimexWebService.asmx/GetBasicCommands"
ENDPOINT_ALL = "/WebServices/SyrConnectLimexWebService.asmx/GetAllCommands"
ENDPOINT_BASIC_ALT = "/GetBasicCommands"
ENDPOINT_ALL_ALT = "/GetAllCommands"

BASIC_COMMANDS = {"getSRN", "getVER", "getFIR", "getTYP", "getCNA"}


@pytest.fixture(scope="module")
def blackbox_config():
    return {
        "enabled": os.getenv("RUN_BLACKBOX", "0") == "1",
        "host": os.getenv("SYR_TEST_HOST", "localhost"),
        "http_port": int(os.getenv("SYR_TEST_HTTP_PORT", "80")),
        "https_port": int(os.getenv("SYR_TEST_HTTPS_PORT", "443")),
    }


@pytest.fixture(scope="module")
def require_blackbox(blackbox_config):
    if not blackbox_config["enabled"]:
        pytest.skip("Set RUN_BLACKBOX=1 to run black-box tests")


@pytest.fixture(scope="module")
def base_http_url(require_blackbox, blackbox_config):
    host = blackbox_config["host"]
    port = blackbox_config["http_port"]
    if not _tcp_open(host, port):
        pytest.skip(f"HTTP endpoint not reachable at {host}:{port}")
    return f"http://{host}:{port}"


def _tcp_open(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _post_form(url: str, form_data: dict[str, str], insecure_https: bool = False) -> tuple[int, str]:
    data = urllib.parse.urlencode(form_data).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")

    context = None
    if insecure_https:
        context = ssl._create_unverified_context()

    try:
        with urllib.request.urlopen(request, timeout=5, context=context) as response:
            return response.getcode(), response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        return err.code, body


def _parse_xml_properties(xml_body: str) -> dict[str, str]:
    root = ET.fromstring(xml_body)
    device = root.find("d")
    if device is None:
        return {}

    out: dict[str, str] = {}
    for cmd in device.findall("c"):
        name = cmd.get("n")
        if name:
            out[name] = cmd.get("v") or ""
    return out


def _mock_device_xml(
    token: str = "token-blackbox",
    serial: str = "SYR-BLACKBOX-0001",
) -> str:
    properties = {
        "getSRN": serial,
        "getVER": "1.9.0",
        "getFIR": "SLPS",
        "getTYP": "80",
        "getCNA": "LEX Plus Test",
        "getCDE": token,
        "getMAC": "AA:BB:CC:DD:EE:01",
        "getALM": "0",
        "getSTA": "OK",
        "getFLO": "9",
        "getPRS": "30",
        "getRPD": "4",
    }

    root = ET.Element("sc", version="1.0")
    d_elem = ET.SubElement(root, "d")
    for key, value in properties.items():
        ET.SubElement(d_elem, "c", n=key, v=value)

    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="unicode")


@pytest.mark.blackbox
def test_blackbox_basic_commands_main_endpoint(base_http_url):
    status, body = _post_form(base_http_url + ENDPOINT_BASIC, {})
    assert status == 200

    props = _parse_xml_properties(body)
    assert BASIC_COMMANDS.issubset(set(props.keys()))


@pytest.mark.blackbox
def test_blackbox_basic_commands_alt_endpoint(base_http_url):
    status, body = _post_form(base_http_url + ENDPOINT_BASIC_ALT, {})
    assert status == 200

    props = _parse_xml_properties(body)
    assert BASIC_COMMANDS.issubset(set(props.keys()))


@pytest.mark.blackbox
def test_blackbox_device_identification_and_status_commands(base_http_url):
    xml = _mock_device_xml()
    status, body = _post_form(base_http_url + ENDPOINT_ALL, {"xml": xml})
    assert status == 200

    props = _parse_xml_properties(body)

    # The server should ask for regular polling getters, including status/alarm.
    assert "getALM" in props
    assert "getSTA" in props
    assert "getSRN" in props
    assert "getVER" in props


@pytest.mark.blackbox
def test_blackbox_status_commands_on_alt_all_endpoint(base_http_url):
    xml = _mock_device_xml(token="token-blackbox-alt", serial="SYR-BLACKBOX-0002")
    status, body = _post_form(base_http_url + ENDPOINT_ALL_ALT, {"xml": xml})
    assert status == 200

    props = _parse_xml_properties(body)
    assert "getALM" in props
    assert "getSTA" in props


@pytest.mark.blackbox
def test_blackbox_rejects_changed_token_for_same_serial(base_http_url):
    serial = "SYR-BLACKBOX-AUTH-0001"
    xml_first = _mock_device_xml(token="token-auth-ok", serial=serial)
    xml_changed = _mock_device_xml(token="token-auth-changed", serial=serial)

    first_status, _ = _post_form(base_http_url + ENDPOINT_ALL, {"xml": xml_first})
    assert first_status == 200

    second_status, second_body = _post_form(base_http_url + ENDPOINT_ALL, {"xml": xml_changed})
    assert second_status == 403
    assert "forbidden" in second_body.lower()


@pytest.mark.blackbox
def test_blackbox_https_basic_commands_if_available(require_blackbox, blackbox_config):
    host = blackbox_config["host"]
    port = blackbox_config["https_port"]
    if not _tcp_open(host, port):
        pytest.skip(f"HTTPS endpoint not reachable at {host}:{port}")

    base_https_url = f"https://{host}:{port}"
    status, body = _post_form(base_https_url + ENDPOINT_BASIC, {}, insecure_https=True)
    assert status == 200

    props = _parse_xml_properties(body)
    assert BASIC_COMMANDS.issubset(set(props.keys()))
