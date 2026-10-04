"""Independent behavioural probes: no author fixtures, network, or live files."""
import asyncio
import copy
import json
import os
from pathlib import Path
import socket
import sys
from types import SimpleNamespace
from unittest.mock import patch

REPO = Path.cwd().resolve()
ROOT = Path(__file__).resolve().parent
HOME = ROOT / ("fixture-home-" + REPO.name)
HOME.mkdir(exist_ok=True)
os.environ["HERMES_HOME"] = str(HOME)
os.environ["HERMES_KANBAN_HOME"] = str(HOME / "kanban")
sys.path.insert(0, str(REPO))

_real_connect = socket.socket.connect

def no_connect(sock, address, *args, **kwargs):
    # Windows asyncio builds a local self-pipe via stdlib socketpair.
    # Permit only that internal caller, never a provider or live service.
    if sys._getframe(1).f_code.co_name == "_fallback_socketpair" and address[0] in {"127.0.0.1", "::1"}:
        return _real_connect(sock, address, *args, **kwargs)
    raise AssertionError("offline probe attempted external network")

def no_create_connection(*args, **kwargs):
    raise AssertionError("offline probe attempted external network")
socket.socket.connect = no_connect
socket.create_connection = no_create_connection

import pytest
from gateway.config import ChannelOverride, GatewayConfig, Platform, PlatformConfig
from gateway.run import GatewayRunner
from gateway.session import SessionSource
from gateway.session_identity import RoutingIdentity

DM = "1256122537"
FORUM = "-1004426332349"
BASE_MODEL = "gpt-6.1-sol"
BASE_PROVIDER = "openai-codex"
QWEN = ("qwen3.8-max", "custom", "https://qa-company.invalid/v1/")
TECH = ("qa-specialist/v2", "qa-tech", "https://qa-tech.invalid/v1/")
LAUNCH = ("qa-launch/v3", "qa-launcher", "https://qa-launch.invalid/v1/")
GLOBALS = (BASE_MODEL, BASE_PROVIDER, "https://qa-default.invalid/v1/")
ROUTES = {x[1]: x[2] for x in [QWEN, TECH, LAUNCH, GLOBALS]}
ROUTES["qa-next"] = "https://qa-next.invalid/v1/"


def config(rules, multiplex=True):
    return GatewayConfig(multiplex_profiles=multiplex, platforms={Platform.TELEGRAM: PlatformConfig(enabled=True, channel_overrides={key: ChannelOverride(model=value[0], provider=value[1]) for key, value in rules.items()})})


def source(profile="company", chat=DM, thread=None, identity=True, multiplex=True):
    s = SessionSource(platform=Platform.TELEGRAM, chat_id=chat, chat_type="group" if chat == FORUM else "dm", thread_id=thread, user_id="qa-user", profile=profile)
    if identity:
        home = HOME / (profile or "unknown")
        s._identity = RoutingIdentity("default", profile, home, home, multiplexed=multiplex)
    return s


def runner(primary="default", launch=None, served=None):
    r = object.__new__(GatewayRunner)
    r.config = launch if launch is not None else config({DM: LAUNCH, FORUM: LAUNCH})
    r._primary_profile_name = primary
    r._profile_configs = served if served is not None else {"company": config({DM: QWEN, FORUM: QWEN}), "tech": config({FORUM: TECH})}
    r._session_model_overrides = {}
    r._rehydrate_session_model_override = lambda key: None
    r._resolve_session_key_or_none = lambda s, key: key
    return r


def runtime(provider, model=None):
    return {"provider": provider, "api_key": "offline-fixture", "base_url": ROUTES[provider], "api_mode": "chat_completions", "request_overrides": {"qa_marker": True}}


@pytest.fixture
def offline():
    with patch("gateway.run._resolve_gateway_model", return_value=BASE_MODEL), patch("gateway.run._resolve_runtime_agent_kwargs", side_effect=lambda: runtime(BASE_PROVIDER)), patch("gateway.run._resolve_runtime_agent_kwargs_for_provider", side_effect=lambda p, target_model=None: runtime(p, target_model)) as providers, patch("gateway.run._credential_pool_for_provider", return_value=None), patch("gateway.run._load_gateway_config", return_value={"model": {"default": BASE_MODEL, "provider": BASE_PROVIDER, "base_url": GLOBALS[2]}, "platforms": {"telegram": {"channel_overrides": {DM: {"model": QWEN[0], "provider": QWEN[1]}, FORUM: {"model": QWEN[0], "provider": QWEN[1]}}}}}):
        yield providers


def turn(r, s, key=None):
    model, rt = r._resolve_session_agent_runtime(source=s, session_key=key, user_config={"model": {"default": BASE_MODEL}})
    actual = (model, rt.get("provider"), rt.get("base_url"))
    print("QA_ROUTE " + json.dumps({"chat": s.chat_id if s else None, "thread": s.thread_id if s else None, "source_profile": s.profile if s else None, "actual": actual}))
    return model, rt


def assert_route(r, s, expected, key=None):
    model, rt = turn(r, s, key)
    actual = (model, rt["provider"], rt["base_url"])
    assert actual == expected, {"expected": expected, "actual": actual}
    return model, rt


@pytest.mark.parametrize("chat,thread", [(DM, None), (FORUM, None), (FORUM, "qa-new-991"), (FORUM, "qa-new-992")], ids=["dm", "negative-forum", "new-topic-one", "new-topic-two"])
def test_fresh_company_entrypoint(offline, chat, thread):
    assert_route(runner(), source(chat=chat, thread=thread), QWEN)


@pytest.mark.parametrize("served,expected", [({"company": config({FORUM: QWEN}), "tech": config({FORUM: TECH})}, TECH), ({"company": config({FORUM: QWEN}), "tech": config({})}, GLOBALS)], ids=["own-rule", "own-global"])
def test_specialist_same_forum_isolation(offline, served, expected):
    assert_route(runner(served=served), source("tech", FORUM, "qa-new-993"), expected)


@pytest.mark.parametrize("s,served", [(source("ghost"), {"company": config({DM: QWEN})}), (source("ghost", identity=False), {"company": config({DM: QWEN})}), (source("company"), {}), (source("company"), None)], ids=["unknown-identity", "unknown-source", "unserved", "missing-cache"])
def test_unknown_and_unserved_fail_safe(offline, s, served):
    r = runner()
    r._profile_configs = served
    assert_route(r, s, GLOBALS)


def test_bare_routed_source_is_supported(offline):
    assert_route(runner(), source(identity=False), QWEN)


def test_authoritative_identity_beats_conflicting_source_profile(offline):
    s = source(chat=FORUM, thread="qa-id-991")
    s.profile = "tech"
    assert_route(runner(), s, QWEN)


@pytest.mark.parametrize("s", [source("default"), source(None, identity=False), source("company", multiplex=False)], ids=["primary", "unrouted", "standalone-identity"])
def test_primary_and_standalone_unchanged(offline, s):
    r = runner()
    if getattr(s, "_identity", None) and not s._identity.multiplexed:
        # Real standalone canonicalization clears the routed source column.
        s.profile = None
    assert_route(r, s, LAUNCH)


@pytest.mark.parametrize("pin", [("explicit-sol/v7", "openai-codex", "https://qa-pin.invalid/v1/"), ("explicit-astra/v7", "qa-astra", "https://qa-astra.invalid/v1/")], ids=["sol", "astra"])
def test_explicit_session_pin_has_priority(offline, pin):
    r = runner()
    key = "agent:company:telegram:qa-pin"
    r._session_state(key).conversation.model_override = {"model": pin[0], "provider": pin[1], "base_url": pin[2], "api_key": "offline-pin-fixture"}
    assert_route(r, source(), pin, key)
    offline.assert_not_called()


def test_ordinary_next_turn_and_signature_follow_cache_replacement(offline):
    r, s = runner(), source(chat=FORUM, thread="qa-warm-991")
    m1, rt1 = assert_route(r, s, QWEN)
    route1 = r._resolve_turn_agent_config("ordinary first message", m1, rt1)
    sig1 = r._agent_config_signature(m1, rt1, [], "stable-prompt")
    r._profile_configs["company"] = config({DM: ("qa-next/v8", "qa-next", ROUTES["qa-next"]), FORUM: ("qa-next/v8", "qa-next", ROUTES["qa-next"])})
    m2, rt2 = assert_route(r, s, ("qa-next/v8", "qa-next", ROUTES["qa-next"]))
    route2 = r._resolve_turn_agent_config("ordinary next message, no slash", m2, rt2)
    sig2 = r._agent_config_signature(m2, rt2, [], "stable-prompt")
    assert route1["signature"] != route2["signature"]
    assert sig1 != sig2
    assert route2["runtime"]["provider"] == "qa-next"


def test_a_b_a_no_mutation_or_config_borrowing(offline):
    r = runner()
    s = source(chat=FORUM)
    snapshot = copy.deepcopy(r._profile_configs)
    assert_route(r, s, QWEN)
    assert_route(r, source("tech", FORUM), TECH)
    assert_route(r, s, QWEN)
    assert r._profile_configs == snapshot
    assert s.profile == "company"


@pytest.mark.parametrize("s", [source(), source(chat=FORUM, thread="qa-slash-991")], ids=["dm", "forum"])
def test_slash_override_helper_matches_turn(offline, s):
    r = runner()
    ch = r._channel_override_for(s)
    model, rt = assert_route(r, s, QWEN)
    assert ch is not None
    assert (ch.model, ch.provider) == (model, rt["provider"])


@pytest.mark.parametrize("chat", [DM, FORUM], ids=["dm", "forum"])
def test_real_model_listing_agrees_with_effective_turn(offline, chat):
    # Drive the actual slash command and its actual read_config/listing path.
    # Only disk/provider catalogue/network/adapter resolution are fixture seams.
    r, s = runner(), source(chat=chat, thread="qa-list-991" if chat == FORUM else None)
    r._resolve_profile_home_for_source = lambda src: HOME / "company"
    r._normalize_source_for_session_key = lambda src: src
    r._session_key_for_source = lambda src: "agent:company:telegram:qa-list"
    r._delivery_adapter_for = lambda src: None
    event = SimpleNamespace(source=s, get_command_args=lambda: "")
    model, rt = turn(r, s)
    with patch("hermes_cli.model_switch.list_authenticated_providers", return_value=[]), patch("hermes_cli.providers.get_label", side_effect=lambda p: p), patch("gateway.slash_commands_model.t", side_effect=lambda key, **kw: key + " " + json.dumps(kw, sort_keys=True)):
        reply = asyncio.run(r._handle_model_command(event))
    print("QA_SLASH " + json.dumps({"turn": [model, rt["provider"]], "reply": reply}))
    assert model in reply and rt["provider"] in reply, {"turn": (model, rt["provider"]), "slash_reply": reply}


@pytest.mark.parametrize("chat", [DM, FORUM], ids=["dm", "forum"])
def test_real_telegram_picker_agrees_with_effective_turn(offline, chat):
    r, s = runner(), source(chat=chat, thread="qa-picker-991" if chat == FORUM else None)
    r._model_picker_context = {}
    r._resolve_profile_home_for_source = lambda src: HOME / "company"
    r._normalize_source_for_session_key = lambda src: src
    r._session_key_for_source = lambda src: "agent:company:telegram:qa-picker"
    captured = {}
    class OfflineAdapter:
        supports_model_picker = True
        async def send_model_picker(self, chat_id, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(success=True)
    r._delivery_adapter_for = lambda src: OfflineAdapter()
    r._thread_metadata_for_source = lambda src, anchor: None
    r._reply_anchor_for_event = lambda event: None
    event = SimpleNamespace(source=s, get_command_args=lambda: "")
    model, rt = turn(r, s)
    with patch("hermes_cli.model_switch.list_authenticated_providers", return_value=[]), patch("hermes_cli.model_switch_providers.list_picker_providers", return_value=[{"slug": "qa-offline", "models": []}]):
        reply = asyncio.run(r._handle_model_command(event))
    print("QA_PICKER " + json.dumps({"turn": [model, rt["provider"]], "picker": [captured.get("current_model"), captured.get("current_provider")], "reply": reply}))
    assert (captured.get("current_model"), captured.get("current_provider")) == (model, rt["provider"])


def test_system_prompt_legacy_scope_and_fallback_preserved(offline):
    r = runner()
    r.config.platforms[Platform.TELEGRAM].channel_overrides[DM].system_prompt = "  launcher channel prompt  "
    r._profile_configs["company"].platforms[Platform.TELEGRAM].channel_overrides[DM].system_prompt = "company channel prompt"
    r._load_ephemeral_system_prompt = lambda: "profile scoped fallback prompt"
    assert r._get_system_prompt_for_channel(Platform.TELEGRAM, DM) == "launcher channel prompt"
    assert r._get_system_prompt_for_channel(Platform.TELEGRAM, "not-in-rules") == "profile scoped fallback prompt"


def test_no_source_keeps_global_route(offline):
    assert_route(runner(), None, GLOBALS)


def test_status_entrypoint_scope_locator():
    # Locator only: not a status safety assertion or PASS evidence.
    print("QA_STATUS_MODULE " + GatewayRunner._handle_status_command.__module__)
    assert callable(GatewayRunner._handle_status_command)
