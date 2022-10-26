"""Helper functions for enums."""

from __future__ import annotations

from enum import IntEnum


def intenum_to_string(
    bitfield: int,
    namespace: type[IntEnum] | IntEnum,
    with_numeric_bitfield: bool = True,
) -> str:
    """Return a string representing the enum's bits based on the namespace.

    >>> from homeassistant.components.media_player import MediaPlayerEntityFeature
    >>> feats = MediaPlayerEntityFeature.PLAY | MediaPlayerEntityFeature.PAUSE
    >>> intenum_to_string(feats, MediaPlayerEntityFeature, False)
    <PAUSE,PLAY>
    """
    fields = []
    for feat in dir(namespace):
        val = getattr(namespace, feat)
        if not isinstance(val, int):
            continue
        if bitfield & val:
            fields.append(feat)
    joinedfields = ",".join(fields)
    if with_numeric_bitfield:
        return f"<{bitfield}: {joinedfields}>"
    return f"<{joinedfields}>"
