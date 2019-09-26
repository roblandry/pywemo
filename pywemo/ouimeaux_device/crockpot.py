"""Representation of a WeMo CrockPot device."""
from xml.etree import cElementTree as et
import sys
from pywemo.ouimeaux_device.api.xsd.device import quote_xml
from .switch import Switch

import logging

LOG = logging.getLogger(__name__)


if sys.version_info[0] < 3:

    class IntEnum:
        """Enum class."""

        pass


else:
    from enum import IntEnum


# These enums were derived from the
# CrockPot.basicevent.GetAttributeList() service call
# Thus these names/values were not chosen randomly
# and the numbers have meaning.
class CrockPotMode(IntEnum):
    """Enum to map WeMo modes to human-readable strings."""

    Off = 0
    Warm = 50
    Low = 51
    High = 52


MODE_NAMES = {
    CrockPotMode.Off: "Off",
    CrockPotMode.Warm: "Warm",
    CrockPotMode.Low: "Low",
    CrockPotMode.High: "High",
}


def attribute_values_to_int(attributes):
    """Return integer value of attributes."""
    result = {}
    for attribute in attributes:
        if len(attribute) >= 2:
            try:
                result[attribute] = int(attributes[attribute])
            except ValueError:
                pass
    return result


class CrockPot(Switch):
    """Representation of a WeMo CofeeMaker device."""

    def __init__(self, *args, **kwargs):
        """Create a WeMo CrockPot device."""
        Switch.__init__(self, *args, **kwargs)
        self._attributes = {}

    def __repr__(self):
        """Return a string representation of the device."""
        return '<WeMo "{name}">'.format(name=self.name)

    def update_attributes(self):
        """Request state from device."""
        # pylint: disable=maybe-no-member
        resp = self.basicevent.GetCrockpotState()
        self._attributes = attribute_values_to_int(resp)
        self._state = self.mode

    def subscription_update(self, _type, _params):
        """Handle reports from device."""
        LOG.debug("subscription_update %s %s", _type, _params)

        # TODO: This most likely does nothing as attributeList doesnt exist
        if _type == "attributeList":
            self._attributes.update(attribute_values_to_int(_params))
            self._state = self.mode
            return True

        return Switch.subscription_update(self, _type, _params)

    @property
    def device_type(self):
        """Return what kind of WeMo this device is."""
        return "CrockPot"

    @property
    def mode(self):
        """Return the mode of the device."""
        return self._attributes.get("mode")

    @property
    def mode_string(self):
        """Return the mode of the device as a string."""
        return MODE_NAMES.get(self.mode, "Unknown")

    @property
    def attributes(self):
        """Return the mode of the device."""
        return self._attributes

    def get_state(self, force_update=False):
        """Return 0 if off and 1 if on."""
        # The base implementation using GetBinaryState doesn't
        # work for CrockPot (always returns 0), so use mode instead.
        if force_update or self._state is None:
            self.update_attributes()

        # Consider the CrockPot to be "on" if it's not off.
        return int(self._state != CrockPotMode.Off)

    def set_state(self, state, time=0):
        """
        Set the mode of this device (as int index of the Mode IntEnum).

        Provided for compatibility with the Switch base class.
        """
        self.set_mode(state, time)

    def set_mode(self, mode_state, time_state):
        """
        Set the mode of this device (as int index of the Mode IntEnum).

        Provided for compatibility with the Switch base class.
        """
        # Make sure we have a value for time to send to device.
        if not time_state:
            time_state = 0
        # Send the attribute list to the device
        # pylint: disable=maybe-no-member
        self.basicevent.SetCrockpotState(mode=int(mode_state),time=int(time_state))

        # Refresh the device state
        self.get_state(True)
