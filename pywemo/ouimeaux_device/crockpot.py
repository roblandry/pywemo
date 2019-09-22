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


def attribute_xml_to_dict(xml_blob):
    """Return integer value of Mode from an attributesList blob, if present."""
    xml_blob = "<attributes>" + xml_blob + "</attributes>"
    xml_blob = xml_blob.replace("&gt;", ">")
    xml_blob = xml_blob.replace("&lt;", "<")
    result = {}
    attributes = et.fromstring(xml_blob)
    for attribute in attributes:
        # The coffee maker might also send unrelated xml blobs, e.g.:
        # <ruleID>coffee-brewed</ruleID>
        # <ruleMsg><![CDATA[Coffee's ready!]]></ruleMsg>
        # so be sure to check the length of attribute
        if len(attribute) >= 2:
            try:
                result[attribute[0].text] = int(attribute[1].text)
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
        return '<WeMo CrockPot "{name}">'.format(name=self.name)

    def update_attributes(self):
        """Request state from device."""
        # pylint: disable=maybe-no-member
        resp = self.basicevent.GetCrockpotState().get("attributeList")
        LOG.critical("Resp: %s" % resp)
        self._attributes = attribute_xml_to_dict(resp)
        self._state = self.mode

    def subscription_update(self, _type, _params):
        """Handle reports from device."""
        if _type == "attributeList":
            self._attributes.update(attribute_xml_to_dict(_params))
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
        return self._attributes.get("Mode")

    @property
    def mode_string(self):
        """Return the mode of the device as a string."""
        return MODE_NAMES.get(self.mode, "Unknown")

    def get_state(self, force_update=False):
        """Return 0 if off and 1 if on."""
        # The base implementation using GetBinaryState doesn't
        # work for CrockPot (always returns 0), so use mode instead.
        if force_update or self._state is None:
            self.update_attributes()

        # Consider the CrockPot to be "on" if it's not off.
        return int(self._state != CrockPotMode.Off)

    def set_state(self, state):
        """
        Set the mode of this device (as int index of the Mode IntEnum).

        Provided for compatibility with the Switch base class.
        """
        self.set_mode(state)

    def set_mode(self, mode):
        """
        Set the mode of this device (as int index of the Mode IntEnum).

        Provided for compatibility with the Switch base class.
        """
        # Send the attribute list to the device
        # pylint: disable=maybe-no-member
        self.basicevent.SetAttributes(attributeList=quote_xml(
            "<attribute><name>Mode</name><value>" +
            str(int(mode)) + "</value></attribute>"))

        # Refresh the device state
        self.get_state(True)
