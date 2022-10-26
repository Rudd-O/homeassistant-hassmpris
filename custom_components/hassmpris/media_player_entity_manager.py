"""Support for interfacing with the HASS MPRIS agent."""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from hassmpris.proto import mpris_pb2
import hassmpris_client

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_IDLE,
    STATE_OFF,
    STATE_PAUSED,
    STATE_PLAYING,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.util.dt as dt_util
from homeassistant.util.enum import intenum_to_string

from .const import ATTR_PLAYBACK_RATE, DOMAIN, LOGGER as _LOGGER

PLATFORM = "media_player"

SUPPORTED_MINIMAL = (
    MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.STOP
)
SUPPORTED_TURN_OFF = MediaPlayerEntityFeature.TURN_OFF
SUPPORTED_TURN_ON = MediaPlayerEntityFeature.TURN_ON

# Enable to remove clones (second / third, nth instances)
# of any player when the player exits.  Not enabled by
# default because events in the logbook disappear when
# the player goes away.
# Clones are always removed upon start or reload of the
# integration, since there is no value in keeping them
# around.
REMOVE_CLONES_WHILE_RUNNING = False


def _get_player_id(
    entity: er.RegistryEntry,
) -> str:
    return entity.unique_id.split("-", 1)[1]


class HASSMPRISEntity(MediaPlayerEntity):
    """This class represents an MPRIS media player entity."""

    _attr_device_class = MediaPlayerDeviceClass.TV
    _attr_supported_features = SUPPORTED_MINIMAL
    _attr_playback_rate: float = 1.0
    _attr_should_poll: bool = False

    def __init__(
        self,
        client: hassmpris_client.AsyncMPRISClient,
        integration_id: str,
        player_id: str,
        initial_state: str | None = None,
    ) -> None:
        """
        Initialize the entity.

        Parameters:
          client: the client to the remote agent
          integration_id: unique identifier of the integration
          player_id: the name / unique identifier of the player
        """
        super().__init__()
        self.client: hassmpris_client.AsyncMPRISClient | None = client
        self._client_host = self.client.host
        self.player_id = player_id
        self._integration_id = integration_id
        self._attr_available = True
        self._metadata: dict[str, Any] = {}
        if initial_state is not None:
            self._attr_state = initial_state

    async def set_unavailable(self):
        """Mark player as unavailable."""
        _LOGGER.debug("Marking %s as unavailable", self.name)
        self.client = None
        self._attr_available = False
        await self.update_state(STATE_UNKNOWN)

    async def set_available(
        self,
        client: hassmpris_client.AsyncMPRISClient,
    ):
        """
        Mark a player as available again.

        Parameters:
          client: the new client to use to talk to the agent
        """
        _LOGGER.debug("Marking %s as available", self.name)
        self.client = client
        self._client_host = self.client.host
        self._attr_available = True
        if self.hass:
            await self.async_update_ha_state(True)

    @property
    def unique_id(self) -> str:
        """Return the unique ID of this entity."""
        return self._integration_id + "-" + self.player_id

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        assert self.player_id
        return self.player_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information associated with the entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._integration_id)},
            name=f"MPRIS agent at {self._client_host}",
            manufacturer="Freedesktop",
        )

    async def async_added_to_hass(self) -> None:
        """Entity has been added to HASS."""
        _LOGGER.debug("Added to hass: %s", self)

    async def async_will_remove_from_hass(self) -> None:
        """Entity is about to be removed from HASS."""
        _LOGGER.debug("Will remove from hass: %s", self)
        self.client = None

    async def async_media_play(self) -> None:
        """Begin playback."""
        if self.client:
            await self.client.play(self.player_id)

    async def async_media_pause(self) -> None:
        """Pause playback."""
        if self.client:
            await self.client.pause(self.player_id)

    async def async_media_stop(self) -> None:
        """Stop playback."""
        if self.client:
            await self.client.stop(self.player_id)

    async def async_media_next_track(self) -> None:
        """Skip to next track."""
        if self.client:
            await self.client.next(self.player_id)

    async def async_media_previous_track(self) -> None:
        """Skip to previous track."""
        if self.client:
            await self.client.previous(self.player_id)

    async def async_media_seek(self, position: float) -> None:
        """Send seek command."""
        if self.client:
            trackid = self._metadata.get("mpris:trackid")
            if trackid:
                await self.client.set_position(
                    self.player_id,
                    trackid,
                    position,
                )

    async def update_state(
        self,
        new_state: str,
    ):
        """Update player state based on reports from the server."""
        if new_state == self._attr_state:
            return

        _LOGGER.debug(
            "Updating state from %s to %s",
            self._attr_state,
            new_state,
        )
        self._attr_state = new_state
        if self.hass:
            await self.async_update_ha_state(True)

    async def update_metadata(self, new_metadata: dict[str, Any]):
        """Update player metadata based on incoming metadata (a dict)."""
        self._metadata = new_metadata
        if "mpris:length" in self._metadata:
            length: int | None = round(
                float(self._metadata["mpris:length"]) / 1000 / 1000
            )
            if length is not None and length <= 0:
                length = None
        else:
            length = None

        self._attr_media_duration = length
        self._attr_media_position = 0 if length is not None else None
        self._attr_media_position_updated_at = dt_util.utcnow()

        _LOGGER.debug("Setting media duration to %s", self._attr_media_duration)
        _LOGGER.debug("Setting media position to %s", self._attr_media_position)

        if self.hass:
            await self.async_update_ha_state(True)

    async def update_position(self, new_position: float):
        """Update position."""
        self._attr_media_position_updated_at = dt_util.utcnow()
        self._attr_media_position = (
            round(new_position) if new_position is not None else None
        )
        _LOGGER.debug("Setting media position to %s", self._attr_media_position)
        if self.hass:
            await self.async_update_ha_state(True)

    async def update_mpris_properties(
        self,
        props: mpris_pb2.MPRISPlayerProperties,
    ):
        """Update player properties based on incoming MPRISPlayerProperties."""
        _LOGGER.debug("%s: new properties: %s", self.name, props)

        feats = self._attr_supported_features
        if props.HasField("CanControl"):
            if not props.CanControl:
                feats = 0
            else:
                feats = SUPPORTED_MINIMAL

        update_state = False

        for name, bitwisefield in {
            "CanPlay": MediaPlayerEntityFeature.PLAY,
            "CanPause": MediaPlayerEntityFeature.PAUSE,
            "CanSeek": MediaPlayerEntityFeature.SEEK,
            "CanGoNext": MediaPlayerEntityFeature.NEXT_TRACK,
            "CanGoPrevious": MediaPlayerEntityFeature.PREVIOUS_TRACK,
        }.items():
            if props.HasField(name):
                val = getattr(props, name)
                if val:
                    feats = feats | bitwisefield
                else:
                    feats = feats & ~bitwisefield

        if feats != self._attr_supported_features:
            _LOGGER.debug(
                "%s: new feature bitfield: %s",
                self.name,
                intenum_to_string(feats, MediaPlayerEntityFeature),
            )
            self._attr_supported_features = feats
            update_state = True

        if props.HasField("Rate") and props.Rate != self._attr_playback_rate:
            _LOGGER.debug("%s: new rate: %s", self.name, props.Rate)
            self._attr_playback_rate = props.Rate
            update_state = True

        if update_state and self.hass:
            await self.async_update_ha_state(True)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        if self.state == STATE_OFF:
            return {}
        return {ATTR_PLAYBACK_RATE: self._attr_playback_rate}


class EntityManager:
    """
    The entity manager manages MPRIS media player entities.

    This class is responsible for maintaining the known player entities
    in sync with the state as reported by the server, as well as keeping
    tabs of newly-appeared players and players that have gone.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        mpris_client: hassmpris_client.AsyncMPRISClient,
        async_add_entities: AddEntitiesCallback,
    ) -> None:
        """
        Initialize the entity manager.

        Parameters:
          hass: the HomeAssistant singleton
          config_entry: the configuration entry associated with
                        this component (or integration?)
          async_add_entities: callback to add entities async
        """
        self.hass = hass
        self.config_entry = config_entry
        self.async_add_entities = async_add_entities
        self._client = mpris_client
        self._players: dict[str, HASSMPRISEntity] = {}
        self._shutdown: asyncio.Future[bool] = asyncio.Future()
        self._started = False

    @property
    def players(self) -> dict[str, HASSMPRISEntity]:
        """Return the players known to this entity manager."""
        return self._players

    @property
    def client(self) -> hassmpris_client.AsyncMPRISClient:
        """Return the MPRIS client associated with this entity manager."""
        return self._client

    async def start(self):
        """Start the entity manager as a separate task."""
        self.hass.loop.create_task(self.run())

    async def run(self):
        """Run the entity manager."""
        if self._started:
            _LOGGER.debug("%X: Thread already started", id(self))
            return
        self._started = True
        _LOGGER.debug("%X: Streaming updates started", id(self))
        while not self._shutdown.done():
            try:
                try:
                    await self._monitor_updates()
                except Exception as exc:
                    if self._shutdown.done():
                        _LOGGER.debug(
                            "%X: Ignoring %s since we are shut down", id(self), exc
                        )
                        await self._shutdown
                        continue
                    raise
            except hassmpris_client.Unauthenticated:
                _LOGGER.error(
                    "We have been deauthorized -- no further updates "
                    "will occur until reauthentication"
                )
                self.config_entry.async_start_reauth(self.hass)
                await self.stop()
            except hassmpris_client.ClientException as exc:
                _LOGGER.error(
                    "%X: We lost connectivity (%s) -- reconnecting", id(self), exc
                )
                await asyncio.sleep(5)
            except Exception as exc:
                await self.stop(exception=exc)
                raise
        await self._shutdown
        _LOGGER.debug("%X: Streaming updates ended", id(self))

    async def stop(
        self,
        *unused_args: Any,
        exception: Exception | None = None,
    ) -> None:
        """Stop the loop."""
        try:
            if exception:
                _LOGGER.debug("Exceptional stop: %s", exception)
                self._shutdown.set_exception(exception)
            else:
                _LOGGER.debug("Normal stop")
                self._shutdown.set_result(True)
        except asyncio.InvalidStateError:
            pass

    async def _mark_all_entities_unavailable(self):
        for entity in self.players.values():
            await entity.set_unavailable()

    async def _mark_all_entities_available(self):
        for entity in self.players.values():
            await entity.set_available(self.client)

    def _add_player(
        self,
        player_id: str,
        initially_off: bool = False,
    ) -> HASSMPRISEntity:
        entity = HASSMPRISEntity(
            self.client,
            self.config_entry.entry_id,
            player_id,
            **({"initial_state": STATE_OFF} if initially_off else {}),
        )
        _LOGGER.debug(
            "%X: adding player %s",
            id(entity),
            player_id,
        )
        self.async_add_entities([entity])
        self.players[player_id] = entity
        return entity

    def _remove_player(
        self,
        player_id: str,
    ):
        reg = er.async_get(self.hass)
        player = self.players.get(player_id)
        if player:
            _LOGGER.debug(
                "%X: removing copy %s from directory",
                id(player),
                player_id,
            )
            del self.players[player_id]
            entity = player.registry_entry
        else:
            entity = None

        if not entity:
            matching = [
                e
                for e in self._player_registry_entries()
                if _get_player_id(e) == player_id
            ]
            entity = matching[0] if matching else None

        if entity:
            _LOGGER.debug(
                "%X: removing copy %s from registry (entity ID %s)",
                id(player) if player else 0,
                player_id,
                entity.entity_id,
            )
            reg.async_remove(entity.entity_id)

    def _player_registry_entries(self) -> list[er.RegistryEntry]:
        reg = er.async_get(self.hass)
        return [
            e
            for e in reg.entities.values()
            if e.config_entry_id == self.config_entry.entry_id
        ]

    async def _finish_initial_players_sync(self):
        """
        Sync know player and registry entry state.

        Called when the agent has sent us the full list of players it knows
        about, and we are ready to materialize players for entities in the
        registry but currently unknown to the agent.

        This is necessary so that Home Assistant can later request the agent
        turn on (spawn) a known player that is currently off.
        """
        # It is probably best to investigate using entity lifecycle hooks:
        # https://developers.home-assistant.io/docs/core/entity/#lifecycle-hooks

        all_player_entries = self._player_registry_entries()
        for player_id in [_get_player_id(e) for e in all_player_entries]:
            self._sync_player_presence(player_id)

    def _sync_player_presence(
        self,
        player_id: str,
    ):
        """Sync entity and config entry for the player.

        `player` will be None if the directory of known players does not
        contain it.  Else it will be defined.
        """

        def is_first_instance() -> bool:
            return not bool(re.match(".* [(]\\d+[)]", player_id))

        def is_off_or_absent() -> bool:
            player = self.players.get(player_id)
            if not player:
                return True  # It is absent.
            offstates = [STATE_OFF, STATE_UNKNOWN]
            return player.state in offstates

        if is_first_instance():
            # This is (by ID) the first instance of a player.
            if player_id not in self.players:
                # We do not have a player in our directory that represents
                # this entity in the registry.  So we "bring it back", in OFF
                # state.  We do this because it is possible, for some players,
                # to be turned on remotely (although currently this feature
                # is not implemented for most players).
                _LOGGER.debug("%X: resuscitating known player %s", id(self), player_id)
                self._add_player(player_id, initially_off=True)
        else:
            # This is a second instance of a player.
            # E.g. `VLC media player`` is not a second instance,
            # but `VLC media player 2`` is in fact a second instance.
            # Many media players can launch multiple instances, but we
            # don't necessarily want to keep all those instances around
            # if they are off or unknown.
            if is_off_or_absent():
                # The copycat player is in the directory, but its state is off
                # or unknown.  This means the agent knew about it at some
                # point, but it is now gone.  So we remove it from the list of
                # players we know about.
                #
                # Alternatively:
                #
                # The agent does not know about this player, or the player
                # is off / unknown.  That means we can remove its entity
                # record from the registry (to keep the record clean of
                # entities which may very well never reappear).
                self._remove_player(player_id)

    async def _monitor_updates(self):
        """Obtain a real-time feed of player updates."""
        try:
            started_syncing = False
            finished_syncing = False
            async for update in self.client.stream_updates():
                if not started_syncing:
                    # First update.  Mark entities available.
                    await self._mark_all_entities_available()
                    started_syncing = True
                if update.HasField("player"):
                    # There's a player update incoming.
                    await self._handle_update(update.player)
                elif not finished_syncing:
                    # Ah, this is the signal that all players known to the agent
                    # have had their information sent to Home Assistant.
                    await self._finish_initial_players_sync()
                    finished_syncing = True
        finally:
            # Whether due to error or request, we no longer get updates.
            # All entities are now unavailable from the standpoint of the
            # HASS MPRIS client, so we mark them as such.
            await self._mark_all_entities_unavailable()

    async def _handle_update(
        self,
        discovery_data: mpris_pb2.MPRISUpdateReply,
    ):
        """Handle a single player update."""
        _LOGGER.debug("%X: Handling update: %s", id(self), discovery_data)
        state = STATE_IDLE
        fire_status_update_observed = False
        table = {
            mpris_pb2.PlayerStatus.GONE: STATE_OFF,
            mpris_pb2.PlayerStatus.APPEARED: STATE_IDLE,
            mpris_pb2.PlayerStatus.PLAYING: STATE_PLAYING,
            mpris_pb2.PlayerStatus.PAUSED: STATE_PAUSED,
            mpris_pb2.PlayerStatus.STOPPED: STATE_IDLE,
        }
        if discovery_data.status != mpris_pb2.PlayerStatus.UNKNOWN:
            state = table[discovery_data.status]
            fire_status_update_observed = True

        fire_metadata_update_observed = False
        if discovery_data.json_metadata:
            fire_metadata_update_observed = True
            metadata = json.loads(discovery_data.json_metadata)

        fire_properties_update_observed = False
        if discovery_data.HasField("properties"):
            fire_properties_update_observed = True
            mpris_properties = discovery_data.properties
        fire_seeked_observed = False
        if discovery_data.HasField("seeked"):
            fire_seeked_observed = True
            position = discovery_data.seeked.position

        player_id = discovery_data.player_id

        if player_id in self.players:
            player: HASSMPRISEntity = self.players[player_id]
        else:
            player = self._add_player(player_id)

        if fire_status_update_observed:
            await player.update_state(state)
        if fire_metadata_update_observed:
            await player.update_metadata(metadata)
        if fire_properties_update_observed:
            await player.update_mpris_properties(mpris_properties)
        if fire_seeked_observed:
            await player.update_position(position)

        # Final hook to remove duplicates which are gone.
        if fire_status_update_observed and REMOVE_CLONES_WHILE_RUNNING:
            self._sync_player_presence(player_id)
