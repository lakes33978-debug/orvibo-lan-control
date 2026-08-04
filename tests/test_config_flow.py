"""Production-path tests for configuration and family selection flows."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.orvibo_lan import config_flow
from custom_components.orvibo_lan.const import (
    CONF_FAMILY_ID,
    CONF_PASSWORD,
    CONF_SELECTED_DEVICE_IDS,
    CONF_USERNAME,
)


class FakeCloudClient:
    def __init__(self) -> None:
        self.family_list = [
            {"familyId": "family-1", "familyName": "Home"},
            {"familyId": "family-2", "familyName": "Office"},
        ]
        self.family_name = "Home"
        self.family_id = "family-1"
        self.user_id = "user-1"

    async def login(self) -> None:
        return None

    async def fetch_devices(self):
        return (
            [
                {
                    "deviceId": "device-1",
                    "deviceType": 1,
                    "uid": "gateway-1",
                    "deviceName": "Desk light",
                    "roomId": "room-1",
                }
            ],
            {"device-1": {"deviceId": "device-1", "value1": 0}},
            [],
            [{"roomId": "room-1", "roomName": "Office"}],
            {"gateway-1": "192.168.1.2"},
            object(),
        )


def test_selection_helpers_use_actual_production_functions() -> None:
    devices = [
        {"deviceId": "one", "deviceName": "Light", "roomName": "Office"},
        {"deviceId": "two", "deviceName": "Sensor", "roomName": ""},
    ]

    assert config_flow._device_label("one", "Light", "Office") == "Light [Office]"
    assert config_flow._validated_selection(["two", "missing"], devices) == ["two"]
    assert config_flow._validated_selection("one", devices) == []


def test_options_flow_keeps_config_entry_without_setting_read_only_property() -> None:
    entry = SimpleNamespace(
        data={
            CONF_USERNAME: "account",
            CONF_PASSWORD: "password",
            CONF_FAMILY_ID: "family-1",
        },
        options={CONF_SELECTED_DEVICE_IDS: ["device-1"]},
    )

    flow = config_flow.OrviboLanConfigFlow.async_get_options_flow(entry)

    assert flow._config_entry is entry


@pytest.mark.asyncio
async def test_options_flow_menu_exposes_reauth_and_devices() -> None:
    entry = SimpleNamespace(data={}, options={})
    flow = config_flow.OrviboLanOptionsFlow(entry)

    result = await flow.async_step_init()

    assert result["type"] == "menu"
    assert result["menu_options"] == ["reauth", "devices"]


@pytest.mark.asyncio
async def test_options_reauth_updates_same_entry_and_preserves_options() -> None:
    entry = SimpleNamespace(
        data={
            CONF_USERNAME: "account",
            CONF_PASSWORD: "old-password",
            CONF_FAMILY_ID: "family-1",
            "unrelated": "preserve-me",
        },
        options={CONF_SELECTED_DEVICE_IDS: ["device-1"]},
    )
    update_entry = MagicMock()
    flow = config_flow.OrviboLanOptionsFlow(entry)
    flow.hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_update_entry=update_entry)
    )
    original_options = dict(entry.options)

    with (
        patch.object(config_flow, "CloudClient", return_value=FakeCloudClient()),
        patch.object(config_flow, "async_get_clientsession", return_value=object()),
        patch.object(
            config_flow,
            "_load_devices",
            new=AsyncMock(return_value=([], {"gateway-1": "192.168.1.2"})),
        ),
        patch.object(
            config_flow,
            "_probe_gateway_credentials",
            new=AsyncMock(return_value=True),
        ),
    ):
        result = await flow.async_step_reauth({CONF_PASSWORD: "new-password"})

    assert result == {"type": "abort", "reason": "reauth_successful"}
    update_entry.assert_called_once()
    assert update_entry.call_args.args[0] is entry
    updated_data = update_entry.call_args.kwargs["data"]
    assert updated_data[CONF_PASSWORD] == "new-password"
    assert updated_data[CONF_FAMILY_ID] == "family-1"
    assert updated_data["unrelated"] == "preserve-me"
    assert entry.options == original_options


@pytest.mark.asyncio
async def test_options_reauth_rejection_does_not_modify_entry() -> None:
    entry = SimpleNamespace(
        data={
            CONF_USERNAME: "account",
            CONF_PASSWORD: "old-password",
            CONF_FAMILY_ID: "family-1",
        },
        options={CONF_SELECTED_DEVICE_IDS: ["device-1"]},
    )
    update_entry = MagicMock()
    flow = config_flow.OrviboLanOptionsFlow(entry)
    flow.hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_update_entry=update_entry)
    )

    with (
        patch.object(config_flow, "CloudClient", return_value=FakeCloudClient()),
        patch.object(config_flow, "async_get_clientsession", return_value=object()),
        patch.object(
            config_flow,
            "_load_devices",
            new=AsyncMock(return_value=([], {"gateway-1": "192.168.1.2"})),
        ),
        patch.object(
            config_flow,
            "_probe_gateway_credentials",
            new=AsyncMock(return_value=False),
        ),
    ):
        result = await flow.async_step_reauth({CONF_PASSWORD: "wrong"})

    assert result["type"] == "form"
    assert result["errors"] == {"base": "auth_failed"}
    update_entry.assert_not_called()


@pytest.mark.asyncio
async def test_user_flow_selects_family_devices_and_scopes_unique_id() -> None:
    client = FakeCloudClient()
    flow = config_flow.OrviboLanConfigFlow()
    flow.hass = SimpleNamespace()

    with (
        patch.object(config_flow, "CloudClient", return_value=client),
        patch.object(config_flow, "async_get_clientsession", return_value=object()),
        patch.object(
            config_flow.OrviboLanConfigFlow,
            "_probe_gateway_login",
            new=AsyncMock(return_value=True),
        ),
    ):
        result = await flow.async_step_user({CONF_USERNAME: "account", CONF_PASSWORD: "password"})
        assert result["step_id"] == "select_family"

        result = await flow.async_step_select_family({CONF_FAMILY_ID: "family-2"})
        assert result["step_id"] == "devices"

        result = await flow.async_step_devices({CONF_SELECTED_DEVICE_IDS: ["device-1"]})

    assert result["type"] == "create_entry"
    assert result["title"] == "account - Office"
    assert result["data"][CONF_FAMILY_ID] == "family-2"
    assert result["options"] == {CONF_SELECTED_DEVICE_IDS: ["device-1"]}
    assert flow.unique_id == "user-1:family-2"


@pytest.mark.asyncio
async def test_user_flow_rejects_empty_credentials() -> None:
    flow = config_flow.OrviboLanConfigFlow()
    flow.hass = SimpleNamespace()

    result = await flow.async_step_user({CONF_USERNAME: "", CONF_PASSWORD: ""})

    assert result["type"] == "form"
    assert result["errors"] == {"base": "empty_username_or_password"}
