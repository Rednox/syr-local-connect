import importlib.util
import sys
import types
from pathlib import Path

import pytest
import pytest_asyncio
from aiohttp.test_utils import TestClient, TestServer


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module spec for {module_name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def syr_modules():
    """Load const/protocol/server without importing Home Assistant runtime."""
    repo_root = Path(__file__).resolve().parents[1]
    component_dir = repo_root / "custom_components" / "syr_connect_local"

    package_name = "syr_local_testpkg"
    package = types.ModuleType(package_name)
    package.__path__ = [str(component_dir)]
    sys.modules[package_name] = package

    const = _load_module(f"{package_name}.const", component_dir / "const.py")
    protocol = _load_module(f"{package_name}.protocol", component_dir / "protocol.py")
    server = _load_module(f"{package_name}.server", component_dir / "server.py")

    return types.SimpleNamespace(const=const, protocol=protocol, server=server)


@pytest.fixture
def server_instance(syr_modules):
    return syr_modules.server.SyrConnectServer(http_port=8081, enable_debug_endpoints=True)


@pytest_asyncio.fixture
async def http_client(server_instance):
    server = TestServer(server_instance.app)
    await server.start_server()
    client = TestClient(server)
    await client.start_server()
    try:
        yield client
    finally:
        await client.close()
        await server.close()


def _mock_device_properties(**overrides):
    data = {
        "getSRN": "SYR-TEST-0001",
        "getVER": "1.9.0",
        "getFIR": "SLPS",
        "getTYP": "80",
        "getCNA": "LEX Plus",
        "getCDE": "token-abc",
        "getMAC": "AA:BB:CC:DD:EE:FF",
        "getALM": "0",
        "getSTA": "OK",
        "getFLO": "12",
        "getPRS": "31",
        "getRPD": "4",
    }
    data.update(overrides)
    return data


def _xml_from(protocol_module, properties):
    return protocol_module.SyrProtocol.generate_xml(properties)


@pytest.mark.asyncio
async def test_get_basic_commands_returns_expected_commands(http_client, syr_modules):
    response = await http_client.post(syr_modules.const.ENDPOINT_BASIC, data={})
    assert response.status == 200

    response_xml = await response.text()
    returned = syr_modules.protocol.SyrProtocol.parse_xml(response_xml)

    for command in syr_modules.const.BASIC_COMMANDS:
        assert command in returned

    assert all(name.startswith("get") for name in returned)


@pytest.mark.asyncio
async def test_get_basic_commands_alt_endpoint_works(http_client, syr_modules):
    response = await http_client.post(syr_modules.const.ENDPOINT_BASIC_ALT, data={})
    assert response.status == 200

    response_xml = await response.text()
    returned = syr_modules.protocol.SyrProtocol.parse_xml(response_xml)

    assert set(syr_modules.const.BASIC_COMMANDS).issubset(set(returned))


@pytest.mark.asyncio
async def test_device_identification_and_status_endpoint(http_client, server_instance, syr_modules):
    properties = _mock_device_properties()
    request_xml = _xml_from(syr_modules.protocol, properties)

    response = await http_client.post(syr_modules.const.ENDPOINT_ALL, data={"xml": request_xml})
    assert response.status == 200

    device = server_instance.get_device(properties["getSRN"])
    assert device is not None
    assert device.is_identified is True

    status_response = await http_client.get("/status")
    assert status_response.status == 200

    status_payload = await status_response.json()
    assert status_payload["devices_count"] == 1
    assert status_payload["devices"][0]["serial"] == properties["getSRN"]
    assert status_payload["devices"][0]["identified"] is True
    assert status_payload["devices"][0]["last_seen_seconds_ago"] is not None


@pytest.mark.asyncio
async def test_status_commands_are_stored_from_mocked_device(http_client, server_instance, syr_modules):
    properties = _mock_device_properties(getALM="1", getSTA="WARNING", getPRS="29")
    request_xml = _xml_from(syr_modules.protocol, properties)

    response = await http_client.post(syr_modules.const.ENDPOINT_ALL_ALT, data={"xml": request_xml})
    assert response.status == 200

    device = server_instance.get_device(properties["getSRN"])
    assert device is not None
    assert device.properties.get("getALM") == "1"
    assert device.properties.get("getSTA") == "WARNING"
    assert device.properties.get("getPRS") == "29"


@pytest.mark.asyncio
async def test_queued_command_sent_once_then_cleared(http_client, server_instance, syr_modules):
    properties = _mock_device_properties()
    request_xml = _xml_from(syr_modules.protocol, properties)

    first = await http_client.post(syr_modules.const.ENDPOINT_ALL, data={"xml": request_xml})
    assert first.status == 200

    queued = server_instance.queue_command(properties["getSRN"], "setRPD", "3")
    assert queued is True

    second = await http_client.post(syr_modules.const.ENDPOINT_ALL, data={"xml": request_xml})
    assert second.status == 200
    second_payload = syr_modules.protocol.SyrProtocol.parse_xml(await second.text())
    assert second_payload.get("setRPD") == "3"

    third = await http_client.post(syr_modules.const.ENDPOINT_ALL, data={"xml": request_xml})
    assert third.status == 200
    third_payload = syr_modules.protocol.SyrProtocol.parse_xml(await third.text())
    assert "setRPD" not in third_payload


@pytest.mark.asyncio
async def test_rejects_request_with_wrong_token_after_bootstrap(http_client, syr_modules):
    valid_properties = _mock_device_properties(getCDE="token-good")
    invalid_properties = _mock_device_properties(getCDE="token-bad")

    valid_xml = _xml_from(syr_modules.protocol, valid_properties)
    invalid_xml = _xml_from(syr_modules.protocol, invalid_properties)

    first = await http_client.post(syr_modules.const.ENDPOINT_ALL, data={"xml": valid_xml})
    assert first.status == 200

    second = await http_client.post(syr_modules.const.ENDPOINT_ALL, data={"xml": invalid_xml})
    assert second.status == 403
