# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2019 Lionel Ott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import ctypes
import enum
import os

from gremlin.error import GremlinError


class VJoyState(enum.Enum):

    """Enumeration of the possible VJoy device states."""

    Owned = 0       # The device is owned by the current application
    Free = 1        # The device is not owned by any application
    Bust = 2        # The device is owned by another application
    Missing = 3     # The device is not present
    Unknown = 4     # Unknown type of error


class FFBPType(enum.Enum):

    """Enumeration of ffb"""

    # Write
    PT_EFFREP = 0x01,  # // Usage Set Effect Report
    PT_ENVREP = 0x02,  # // Usage Set Envelope Report
    PT_CONDREP = 0x03,  # // Usage Set Condition Report
    PT_PRIDREP = 0x04,  # // Usage Set Periodic Report
    PT_CONSTREP = 0x05,  # // Usage Set Constant Force Report
    PT_RAMPREP = 0x06,  # // Usage Set Ramp Force Report
    PT_CSTMREP = 0x07,  # // Usage Custom Force Data Report
    PT_SMPLREP = 0x08,  # // Usage Download Force Sample
    PT_EFOPREP = 0x0A,  # // Usage Effect Operation Report
    PT_BLKFRREP = 0x0B,  # // Usage PID Block Free Report
    PT_CTRLREP = 0x0C,  # // Usage PID Device Control
    PT_GAINREP = 0x0D,  # // Usage Device Gain Report
    PT_SETCREP = 0x0E,  # // Usage Set Custom Force Report

    # // Feature
    PT_NEWEFREP = 0x01+0x10,  # // Usage Create New Effect Report
    PT_BLKLDREP = 0x02+0x10,  # // Usage Block Load Report
    PT_POOLREP = 0x03+0x10,  # // Usage PID Pool Report

    @staticmethod
    def from_ctype(value):
        """Returns the enum type corresponding to the provided value.

        Parameters
        ==========
        value : int
            The integer value

        Returns
        =======
        InputType
            Enum value representing the correct ffb
        """
        if value == 0x01:
            return FFBPType.PT_EFFREP
        elif value == 0x02:
            return FFBPType.PT_ENVREP
        elif value == 0x03:
            return FFBPType.PT_CONDREP
        elif value == 0x04:
            return FFBPType.PT_PRIDREP
        elif value == 0x05:
            return FFBPType.PT_CONSTREP
        elif value == 0x06:
            return FFBPType.PT_RAMPREP
        elif value == 0x07:
            return FFBPType.PT_CSTMREP
        elif value == 0x08:
            return FFBPType.PT_SMPLREP
        elif value == 0x0A:
            return FFBPType.PT_EFOPREP
        elif value == 0x0B:
            return FFBPType.PT_BLKFRREP
        elif value == 0x0C:
            return FFBPType.PT_CTRLREP
        elif value == 0x0D:
            return FFBPType.PT_GAINREP
        elif value == 0x0E:
            return FFBPType.PT_SETCREP
        elif value == 0x01+0x10:
            return FFBPType.PT_NEWEFREP
        elif value == 0x02+0x10:
            return FFBPType.PT_BLKLDREP
        elif value == 0x03+0x10:
            return FFBPType.PT_POOLREP
        else:
            raise GremlinError("Invalid ffb type value {:d}".format(value))


class _FFB_DATA(ctypes.Structure):

    """Mapping for the vJOY FFB_DATA C structure."""

    _fields_ = [
        ("size", ctypes.c_ulong),
        ("cmd", ctypes.c_ulong),
        ("data", ctypes.c_char_p)
    ]


C_FFB_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)


class VJoyInterface:

    """Allows low level interaction with VJoy devices via ctypes."""

    # Attempt to find the correct location of the dll for development
    # and installed use cases.
    dev_path = os.path.join(os.path.dirname(__file__), "vJoyInterface.dll")
    if os.path.isfile("vJoyInterface.dll"):
        dll_path = "vJoyInterface.dll"
    elif os.path.isfile(dev_path):
        dll_path = dev_path
    else:
        raise GremlinError("Unable to locate vjoy dll")

    vjoy_dll = ctypes.cdll.LoadLibrary(dll_path)

    # ffb callback
    ffb_callback_fn = None

    # Declare argument and return types for all the functions
    # exposed by the dll
    api_functions = {
        # General vJoy information
        "GetvJoyVersion": {
            "arguments": [],
            "returns": ctypes.c_short
        },
        "vJoyEnabled": {
            "arguments": [],
            "returns": ctypes.c_bool
        },
        "GetvJoyProductString": {
            "arguments": [],
            "returns": ctypes.c_wchar_p
        },
        "GetvJoyManufacturerString": {
            "arguments": [],
            "returns": ctypes.c_wchar_p
        },
        "GetvJoySerialNumberString": {
            "arguments": [],
            "returns": ctypes.c_wchar_p
        },

        # Device properties
        "GetVJDButtonNumber": {
            "arguments": [ctypes.c_uint],
            "returns": ctypes.c_int
        },
        "GetVJDDiscPovNumber": {
            "arguments": [ctypes.c_uint],
            "returns": ctypes.c_int
        },
        "GetVJDContPovNumber": {
            "arguments": [ctypes.c_uint],
            "returns": ctypes.c_int
        },
        # API claims this should return a bool, however, this is untrue and
        # is an int, see:
        # http://vjoystick.sourceforge.net/site/index.php/forum/5-Discussion/1026-bug-with-getvjdaxisexist
        "GetVJDAxisExist": {
            "arguments": [ctypes.c_uint, ctypes.c_uint],
            "returns": ctypes.c_int
        },
        "GetVJDAxisMax": {
            "arguments": [ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p],
            "returns": ctypes.c_bool
        },
        "GetVJDAxisMin": {
            "arguments": [ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p],
            "returns": ctypes.c_bool
        },

        # Device management
        "GetOwnerPid": {
            "arguments": [ctypes.c_uint],
            "returns": ctypes.c_int
        },
        "AcquireVJD": {
            "arguments": [ctypes.c_uint],
            "returns": ctypes.c_bool
        },
        "RelinquishVJD": {
            "arguments": [ctypes.c_uint],
            "returns": None,
        },
        "UpdateVJD": {
            "arguments": [ctypes.c_uint, ctypes.c_void_p],
            "returns": ctypes.c_bool
        },
        "GetVJDStatus": {
            "arguments": [ctypes.c_uint],
            "returns": ctypes.c_int
        },

        # Reset functions
        "ResetVJD": {
            "arguments": [ctypes.c_uint],
            "returns": ctypes.c_bool
        },
        "ResetAll": {
            "arguments": [],
            "returns": None
        },
        "ResetButtons": {
            "arguments": [ctypes.c_uint],
            "returns": ctypes.c_bool
        },
        "ResetPovs": {
            "arguments": [ctypes.c_uint],
            "returns": ctypes.c_bool
        },

        # Set values
        "SetAxis": {
            "arguments": [ctypes.c_long, ctypes.c_uint, ctypes.c_uint],
            "returns": ctypes.c_bool
        },
        "SetBtn": {
            "arguments": [ctypes.c_bool, ctypes.c_uint, ctypes.c_ubyte],
            "returns": ctypes.c_bool
        },
        "SetDiscPov": {
            "arguments": [ctypes.c_int, ctypes.c_uint, ctypes.c_ubyte],
            "returns": ctypes.c_bool
        },
        "SetContPov": {
            "arguments": [ctypes.c_ulong, ctypes.c_uint, ctypes.c_ubyte],
            "returns": ctypes.c_bool
        },

        # FFB Functions
        "FfbStart": { # DEPRICATED
            "arguments": [ctypes.c_uint],
            "returns": ctypes.c_bool
        },
        "FfbStop": { # DEPRICATED
            "arguments": [ctypes.c_uint],
            "returns": ctypes.c_bool
        },
        "IsDeviceFfb": {
            "arguments": [ctypes.c_uint],
            "returns": ctypes.c_bool
        },

        "FfbRegisterGenCB": {
            "arguments": [C_FFB_CALLBACK, ctypes.c_void_p],
            "returns": None
        },

        "Ffb_h_Type": {
            "arguments": [ctypes.c_void_p, ctypes.c_void_p],
            "returns": ctypes.c_uint32
        },
    }

    @staticmethod
    def set_ffb_event_callback(callback, vjoy_id):
        """Sets the callback function to use for input events.

        Parameters
        ==========
        callback : callable
            Function to execute when an ffb.
        """

        VJoyInterface.ffb_callback_fn = C_FFB_CALLBACK(callback)
        VJoyInterface.vjoy_dll.FfbRegisterGenCB(VJoyInterface.ffb_callback_fn, ctypes.byref(ctypes.c_uint(vjoy_id)))

    @classmethod
    def initialize(cls):
        """Initializes the functions as class methods."""
        for fn_name, params in cls.api_functions.items():
            dll_fn = getattr(cls.vjoy_dll, fn_name)
            if "arguments" in params:
                dll_fn.argtypes = params["arguments"]
            if "returns" in params:
                dll_fn.restype = params["returns"]
            setattr(cls, fn_name, dll_fn)


# Initialize the class
VJoyInterface.initialize()
