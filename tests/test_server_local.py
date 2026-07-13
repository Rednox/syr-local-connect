import importlib.util
import socket
import sys
import threading
import types
import warnings
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


@pytest.mark.asyncio
async def test_unapproved_tlsv1_tuple_does_not_create_device(http_client, server_instance, syr_modules, monkeypatch):
    server_instance.legacy_tls_allowed_tuples.clear()
    monkeypatch.setattr(server_instance, "_get_tls_version", lambda request: "TLSV1")
    monkeypatch.setattr(server_instance, "_get_source_ip", lambda request: "192.168.2.200")

    properties = _mock_device_properties(getSRN="SYR-LEGACY-0001")
    request_xml = _xml_from(syr_modules.protocol, properties)

    first = await http_client.post(syr_modules.const.ENDPOINT_ALL, data={"xml": request_xml})
    assert first.status == 200

    assert server_instance.get_device(properties["getSRN"]) is None
    assert properties["getSRN"] not in server_instance.get_all_devices()


def test_legacy_tls_tuple_discovery_and_allowlist(syr_modules):
    server = syr_modules.server.SyrConnectServer(
        http_port=8081,
        legacy_tls_allowed_tuples=[],
    )

    tuple_key = server._discover_legacy_tuple("192.168.1.10", "AA:BB:CC:DD:EE:FF")
    assert tuple_key == "192.168.1.10|aa:bb:cc:dd:ee:ff"
    assert tuple_key in server.get_legacy_tls_discovered_tuples()

    assert server._is_legacy_tuple_allowed("192.168.1.10", "AA:BB:CC:DD:EE:FF") is False

    server.legacy_tls_allowed_tuples.add("192.168.1.10|aa:bb:cc:dd:ee:ff")
    assert server._is_legacy_tuple_allowed("192.168.1.10", "AA:BB:CC:DD:EE:FF") is True


def test_legacy_tls_unknown_mac_allowed_by_ip_prefix(syr_modules):
    server = syr_modules.server.SyrConnectServer(
        http_port=8081,
        legacy_tls_allowed_tuples=["192.168.1.11|11:22:33:44:55:66"],
    )

    assert server._is_legacy_tuple_allowed("192.168.1.11", None) is True
    assert server._is_legacy_tuple_allowed("192.168.1.12", None) is False


def test_legacy_tls_mac_fallback_ignores_docker_gateway_ip(syr_modules):
    """Allowlist entries should match by MAC even when the IP is a Docker gateway."""
    server = syr_modules.server.SyrConnectServer(
        http_port=8081,
        legacy_tls_allowed_tuples=["192.168.88.138|aa:bb:cc:dd:ee:ff"],
    )

    # Exact IP|MAC match still works.
    assert server._is_legacy_tuple_allowed("192.168.88.138", "AA:BB:CC:DD:EE:FF") is True

    # Wrong IP (Docker gateway) with correct MAC is allowed via MAC fallback.
    assert server._is_legacy_tuple_allowed("172.18.0.1", "AA:BB:CC:DD:EE:FF") is True

    # Wrong MAC is still rejected.
    assert server._is_legacy_tuple_allowed("172.18.0.1", "AA:BB:CC:DD:EE:00") is False

    # No MAC provided falls back to IP-only matching.
    assert server._is_legacy_tuple_allowed("192.168.88.138", None) is True
    assert server._is_legacy_tuple_allowed("172.18.0.1", None) is False


def test_legacy_tls_bootstrap_accepts_once_and_discovers_tuple(syr_modules):
    server = syr_modules.server.SyrConnectServer(
        http_port=8081,
        legacy_tls_allowed_tuples=[],
    )

    first_blocked = server._should_block_legacy_tls(
        source_ip="192.168.2.10",
        mac="AA:BB:CC:DD:EE:11",
        path=syr_modules.const.ENDPOINT_ALL,
        tls_version="TLSv1",
    )

    second_blocked = server._should_block_legacy_tls(
        source_ip="192.168.2.10",
        mac="AA:BB:CC:DD:EE:11",
        path=syr_modules.const.ENDPOINT_ALL,
        tls_version="TLSv1",
    )

    assert first_blocked is False
    assert second_blocked is True
    tuple_key = "192.168.2.10|aa:bb:cc:dd:ee:11"
    assert tuple_key in server.get_legacy_tls_discovered_tuples()
    assert tuple_key in server.legacy_tls_bootstrapped_tuples


def test_modern_tls_does_not_auto_add_to_allowlist(syr_modules):
    server = syr_modules.server.SyrConnectServer(
        http_port=8081,
        legacy_tls_allowed_tuples=[],
    )

    blocked = server._should_block_legacy_tls(
        source_ip="192.168.2.50",
        mac="AA:BB:CC:DD:EE:55",
        path=syr_modules.const.ENDPOINT_ALL,
        tls_version="TLSv1.2",
    )

    assert blocked is False
    assert server._format_legacy_tuple("192.168.2.50", "AA:BB:CC:DD:EE:55") not in server.legacy_tls_allowed_tuples


def test_legacy_tls_strict_mode_blocks_unknown_tuple(syr_modules):
    server = syr_modules.server.SyrConnectServer(
        http_port=8081,
        legacy_tls_allowed_tuples=[],
    )

    first_blocked = server._should_block_legacy_tls(
        source_ip="192.168.2.11",
        mac="AA:BB:CC:DD:EE:22",
        path=syr_modules.const.ENDPOINT_ALL,
        tls_version="TLSv1",
    )

    blocked = server._should_block_legacy_tls(
        source_ip="192.168.2.11",
        mac="AA:BB:CC:DD:EE:22",
        path=syr_modules.const.ENDPOINT_ALL,
        tls_version="TLSv1",
    )

    assert first_blocked is False
    assert blocked is True
    assert "192.168.2.11|aa:bb:cc:dd:ee:22" in server.get_legacy_tls_discovered_tuples()


def test_tls12_tuple_is_auto_allowed_even_in_strict_mode(syr_modules):
    server = syr_modules.server.SyrConnectServer(
        http_port=8081,
        legacy_tls_allowed_tuples=[],
    )

    blocked = server._should_block_legacy_tls(
        source_ip="192.168.2.12",
        mac="AA:BB:CC:DD:EE:33",
        path=syr_modules.const.ENDPOINT_ALL,
        tls_version="TLSv1.2",
    )

    assert blocked is False
    assert server.tls_tuple_max_version["192.168.2.12|aa:bb:cc:dd:ee:33"] == "TLSv1.2"


def test_tls_policy_defaults_to_tlsv1_floor(syr_modules):
    ssl_context = syr_modules.server.ssl.create_default_context(syr_modules.server.ssl.Purpose.CLIENT_AUTH)

    syr_modules.server.SyrConnectServer._apply_tls_policy(ssl_context)

    assert ssl_context.minimum_version == syr_modules.server.ssl.TLSVersion.TLSv1
    assert ssl_context.maximum_version == syr_modules.server.ssl.TLSVersion.TLSv1_3


def test_tlsv1_handshake_succeeds_with_applied_policy(syr_modules):
    """Verify that TLSv1.0 actually negotiates after applying the TLS policy.

    On OpenSSL 3.x, TLSv1.0/1.1 are disabled by default (security level 1).
    Merely setting minimum_version is not enough; _apply_tls_policy must also
    lower the cipher security level. This is a regression test for that issue.
    """
    repo_root = Path(__file__).resolve().parents[1]
    cert_file = repo_root / "homeassistant" / "config" / "syr_cert.pem"
    key_file = repo_root / "homeassistant" / "config" / "syr_key.pem"

    server = syr_modules.server.SyrConnectServer(
        http_port=8081,
        use_https=True,
        cert_file=str(cert_file),
        key_file=str(key_file),
    )
    ssl_context = server._create_ssl_context()

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("127.0.0.1", 0))
    server_sock.listen(1)
    port = server_sock.getsockname()[1]

    result: dict[str, object] = {}

    def server_thread() -> None:
        conn, _ = server_sock.accept()
        try:
            tls_conn = ssl_context.wrap_socket(conn, server_side=True)
            result["server_version"] = tls_conn.version()
            tls_conn.close()
        except Exception as exc:  # pragma: no cover - surfaced via result
            result["server_error"] = exc
        finally:
            server_sock.close()

    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()

    try:
        client_ctx = syr_modules.server.ssl.SSLContext(syr_modules.server.ssl.PROTOCOL_TLS_CLIENT)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            client_ctx.minimum_version = syr_modules.server.ssl.TLSVersion.TLSv1
            client_ctx.maximum_version = syr_modules.server.ssl.TLSVersion.TLSv1
        client_ctx.set_ciphers("DEFAULT:@SECLEVEL=0")
        client_ctx.check_hostname = False
        client_ctx.verify_mode = syr_modules.server.ssl.CERT_NONE

        with socket.create_connection(("127.0.0.1", port), timeout=5) as sock:
            with client_ctx.wrap_socket(sock, server_hostname="localhost") as tls_sock:
                result["client_version"] = tls_sock.version()
    except Exception as exc:  # pragma: no cover - surfaced via result
        result["client_error"] = exc

    thread.join(timeout=5)

    assert "client_version" in result, f"TLSv1 client handshake failed: {result.get('client_error')}"
    assert "server_version" in result, f"TLSv1 server handshake failed: {result.get('server_error')}"
    assert result["client_version"] == "TLSv1"
    assert result["server_version"] == "TLSv1"


def test_tls_version_tracking_keeps_highest_seen(syr_modules):
    server = syr_modules.server.SyrConnectServer(http_port=8081)

    tuple_key = "192.168.2.13|aa:bb:cc:dd:ee:44"
    server._remember_tls_version_for_tuple(tuple_key, "TLSv1")
    server._remember_tls_version_for_tuple(tuple_key, "TLSv1.2")
    server._remember_tls_version_for_tuple(tuple_key, "TLSv1.1")

    assert server.tls_tuple_max_version[tuple_key] == "TLSv1.2"


def test_source_ip_fallback_to_transport_peername_for_discovery(syr_modules):
    class _Transport:
        @staticmethod
        def get_extra_info(name):
            if name == "peername":
                return ("10.10.10.7", 443)
            return None

    class _Request:
        remote = None
        transport = _Transport()
        headers = {}

    ip = syr_modules.server.SyrConnectServer._get_source_ip(_Request())
    assert ip == "10.10.10.7"

    server = syr_modules.server.SyrConnectServer(http_port=8081)
    tuple_key = server._discover_legacy_tuple(ip, None)
    assert tuple_key == "10.10.10.7|unknown"
    assert tuple_key in server.get_legacy_tls_discovered_tuples()


def test_source_ip_prefers_x_forwarded_for_over_remote_peer(syr_modules):
    """X-Forwarded-For should win so Docker/proxy gateway IPs are not used."""

    class _Transport:
        @staticmethod
        def get_extra_info(name):
            if name == "peername":
                return ("172.18.0.1", 443)
            return None

    class _Request:
        def __init__(self, remote, xff):
            self.remote = remote
            self.transport = _Transport()
            self.headers = {}
            if xff is not None:
                self.headers["X-Forwarded-For"] = xff

    # XFF present -> use the forwarded IP, ignore Docker gateway.
    req_with_xff = _Request(remote="172.18.0.1", xff="192.168.88.138")
    assert syr_modules.server.SyrConnectServer._get_source_ip(req_with_xff) == "192.168.88.138"

    # XFF chain -> use the leftmost (client) IP.
    req_chain = _Request(remote="172.18.0.1", xff="192.168.88.138, 10.0.0.5")
    assert syr_modules.server.SyrConnectServer._get_source_ip(req_chain) == "192.168.88.138"

    # No XFF -> fall back to request.remote.
    req_no_xff = _Request(remote="192.168.88.138", xff=None)
    assert syr_modules.server.SyrConnectServer._get_source_ip(req_no_xff) == "192.168.88.138"

    # No XFF and no request.remote -> fall back to transport peername.
    req_peer_only = _Request(remote=None, xff=None)
    assert syr_modules.server.SyrConnectServer._get_source_ip(req_peer_only) == "172.18.0.1"


def test_legacy_tls_blocking_toggle_off_allows_tlsv1(syr_modules):
    server = syr_modules.server.SyrConnectServer(http_port=8081, legacy_tls_allowed_tuples=[])

    first_blocked = server._should_block_legacy_tls(
        source_ip="192.168.2.22",
        mac="AA:BB:CC:DD:EE:66",
        path=syr_modules.const.ENDPOINT_ALL,
        tls_version="TLSv1",
    )
    second_blocked = server._should_block_legacy_tls(
        source_ip="192.168.2.22",
        mac="AA:BB:CC:DD:EE:66",
        path=syr_modules.const.ENDPOINT_ALL,
        tls_version="TLSv1",
    )

    assert first_blocked is False
    assert second_blocked is True


def test_legacy_tls_only_defers_until_allowlisted(syr_modules):
    server = syr_modules.server.SyrConnectServer(
        http_port=8081,
        legacy_tls_allowed_tuples=[],
    )

    first_blocked = server._should_block_legacy_tls(
        source_ip="192.168.2.21",
        mac="AA:BB:CC:DD:EE:55",
        path=syr_modules.const.ENDPOINT_ALL,
        tls_version="TLSv1",
    )
    second_blocked = server._should_block_legacy_tls(
        source_ip="192.168.2.21",
        mac="AA:BB:CC:DD:EE:55",
        path=syr_modules.const.ENDPOINT_ALL,
        tls_version="TLSv1",
    )

    assert first_blocked is False
    assert second_blocked is True
    assert "192.168.2.21|aa:bb:cc:dd:ee:55" in server.get_legacy_tls_discovered_tuples()
