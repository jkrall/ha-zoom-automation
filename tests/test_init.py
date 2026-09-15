"""Test zoom init."""
import pytest

from homeassistant import config_entries
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import DATA_IMPLEMENTATIONS
from homeassistant.setup import async_setup_component

from custom_components.zoom.common import ZoomOAuth2Implementation
from custom_components.zoom.const import DOMAIN

from .const import MOCK_CONFIG, MOCK_ENTRY

BINARY_SENSOR_ENTITY_ID = "binary_sensor.zoom_test"


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_component_setup(hass: HomeAssistant) -> None:
    """Test component setup."""
    # CONFIG_SCHEMA expects a list of configs
    assert await async_setup_component(
        hass,
        DOMAIN,
        {DOMAIN: [MOCK_CONFIG]},
    )
    # Implementation is registered under the config's name ("test"), not DOMAIN
    assert (
        type(hass.data[DATA_IMPLEMENTATIONS][DOMAIN]["test"])
        == ZoomOAuth2Implementation
    )


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_component_setup_failure(hass: HomeAssistant) -> None:
    """Test component setup failure."""
    hass.config.external_url = None
    assert (
        await async_setup_component(
            hass,
            DOMAIN,
            {DOMAIN: [MOCK_CONFIG]},
        )
        is False
    )


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_entry_setup_and_unload(hass: HomeAssistant) -> None:
    """Test entry setup and unload."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(
        hass,
        DOMAIN,
        {},
    )
    assert MOCK_ENTRY.state == config_entries.ConfigEntryState.LOADED

    state = hass.states.get(BINARY_SENSOR_ENTITY_ID)
    assert state is not None
    assert not state.attributes.get("restored")

    assert await hass.config_entries.async_unload(MOCK_ENTRY.entry_id)
    await hass.async_block_till_done()
    assert MOCK_ENTRY.state == config_entries.ConfigEntryState.NOT_LOADED
    # Unloading the entry has to take its platforms with it, or the next setup
    # is refused because the platform is still registered against the entry.
    # A removed entity that is still in the registry is left behind as an
    # unavailable, restored placeholder.
    state = hass.states.get(BINARY_SENSOR_ENTITY_ID)
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes.get("restored")


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_entry_reload(hass: HomeAssistant, caplog) -> None:
    """Test an entry can be reloaded without leaving its platforms behind."""
    MOCK_ENTRY.add_to_hass(hass)
    assert await async_setup_component(
        hass,
        DOMAIN,
        {},
    )
    assert MOCK_ENTRY.state == config_entries.ConfigEntryState.LOADED

    caplog.clear()
    await hass.config_entries.async_reload(MOCK_ENTRY.entry_id)
    await hass.async_block_till_done()

    assert MOCK_ENTRY.state == config_entries.ConfigEntryState.LOADED
    assert hass.states.get(BINARY_SENSOR_ENTITY_ID) is not None
    assert "has already been setup" not in caplog.text
