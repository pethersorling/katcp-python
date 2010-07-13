# testutils.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 SKA South Africa (http://ska.ac.za/)
# BSD license - see COPYING for details

"""Test utils for katcp package tests.
   """

import client
import logging
import re
import time
import Queue
from .katcp import Sensor, Message, DeviceMetaclass
from .server import DeviceServer, FailReply

class TestLogHandler(logging.Handler):
    """A logger for KATCP tests."""

    def __init__(self):
        """Create a TestLogHandler."""
        logging.Handler.__init__(self)
        self._records = []

    def emit(self, record):
        """Handle the arrival of a log message."""
        self._records.append(record)

    def clear(self):
        """Clear the list of remembered logs."""
        self._records = []


class DeviceTestSensor(Sensor):
    """Test sensor."""

    def __init__(self, sensor_type, name, description, units, params,
                 timestamp, status, value):
        super(DeviceTestSensor, self).__init__(
            sensor_type, name, description, units, params)
        self.set(timestamp, status, value)


class TestClientMetaclass(DeviceMetaclass):
    """Metaclass for test client classes.

       Adds a raw send method and methods for collecting all inform and
       reply messages received by the client.
       """
    def __init__(mcs, name, bases, dct):
        """Constructor for TestClientMetaclass.  Should not be used
           directly.

           @param mcs The metaclass instance
           @param name The metaclass name
           @param bases List of base classes
           @param dct Class dict
        """
        super(TestClientMetaclass, mcs).__init__(name, bases, dct)

        orig_init = mcs.__init__
        orig_handle_reply = mcs.handle_reply
        orig_handle_inform = mcs.handle_inform

        def __init__(self, *args, **kwargs):
            orig_init(self, *args, **kwargs)
            self.clear_messages()

        def handle_reply(self, msg):
            self._replies.append(msg)
            self._msgs.append(msg)
            return orig_handle_reply(self, msg)

        def handle_inform(self, msg):
            self._informs.append(msg)
            self._msgs.append(msg)
            return orig_handle_inform(self, msg)

        def raw_send(self, chunk):
            """Send a raw chunk of data to the server."""
            self._sock.send(chunk)

        def replies_and_informs(self):
            return self._replies, self._informs

        def messages(self):
            return self._msgs

        def clear_messages(self):
            self._replies = []
            self._informs = []
            self._msgs = []

        mcs.__init__ = __init__
        mcs.handle_reply = handle_reply
        mcs.handle_inform = handle_inform
        mcs.raw_send = raw_send
        mcs.replies_and_informs = replies_and_informs
        mcs.messages = messages
        mcs.clear_messages = clear_messages


class DeviceTestClient(client.DeviceClient):
    """Test client."""
    __metaclass__ = TestClientMetaclass


class CallbackTestClient(client.CallbackClient):
    """Test callback client."""
    __metaclass__ = TestClientMetaclass


class BlockingTestClient(client.BlockingClient):
    """Test blocking client."""
    __metaclass__ = TestClientMetaclass

    def __init__(self, test, *args, **kwargs):
        """Takes a TestCase class as an additional parameter."""
        self.test = test
        super(BlockingTestClient, self).__init__(*args, **kwargs)

    def _sensor_lag(self):
        """The expected lag before device changes are applied."""
        return getattr(self.test, "sensor_lag", 0)

    @staticmethod
    def expected_sensor_value_tuple(sensorname, value, sensortype=str, places=7):
        """Helper method for completing optional values in expected sensor value tuples.

        Parameters
        ----------
        sensorname : str
            The name of the sensor.
        value : obj
            The expected value of the sensor.  Type must match sensortype.
        sensortype : type, optional
            The type to use to convert the sensor value. Default: str.
        places : int, optional
            The number of places to use in a float comparison.  Has no effect if
            sensortype is not float. Default: 7.
        """

        return (sensorname, value, sensortype, places)

    # SENSOR VALUES

    def get_sensor_value(self, sensorname, sensortype=str):
        """Retrieve the value of a sensor.

        Parameters
        ----------
        sensorname : str
            The name of the sensor.
        sensortype : type, optional
            The type to use to convert the sensor value. Default: str.
        """

        reply, informs = self.blocking_request(Message.request("sensor-value", sensorname))
        self.test.assertTrue(reply.reply_ok(),
            "Could not retrieve value of sensor '%s': %s"
            % (sensorname, (reply.arguments[1] if len(reply.arguments) >= 2 else ""))
        )

        value = informs[0].arguments[4]

        if sensortype == bool:
            return bool(int(value))

        return sensortype(value)

    def get_sensor_status(self, sensorname):
        """Retrieve the status of a sensor.

        Parameters
        ----------
        sensorname : str
            The name of the sensor.
        """

        reply, informs = self.blocking_request(Message.request("sensor-value", sensorname))
        self.test.assertTrue(reply.reply_ok(),
            "Could not retrieve status of sensor '%s': %s"
            % (sensorname, (reply.arguments[1] if len(reply.arguments) >= 2 else ""))
        )

        return informs[0].arguments[3]

    def assert_sensor_equals(self, sensorname, expected, sensortype=str, msg=None, places=7):
        """Assert that a sensor's value is equal to the given value.

        Parameters
        ----------
        sensorname : str
            The name of the sensor.
        expected : obj
            The expected value of the sensor.  Type must match sensortype.
        sensortype : type, optional
            The type to use to convert the sensor value. Default: str.
        msg : str, optional
            A custom message to print if the assertion fails.  If the string
            contains %r, it will be replaced with the sensor's value. A default
            message is defined in this method.
        places : int, optional
            The number of places to use in a float comparison.  Has no effect if
            sensortype is not float. Default: 7.
        """

        if msg is None:
            places_msg = " (within %d decimal places)" % places if sensortype == float else ""
            msg = "Value of sensor '%s' is %%r. Expected %r%s." % (sensorname, expected, places_msg)

        got = self.get_sensor_value(sensorname, sensortype)
        if '%r' in msg:
            msg = msg % got

        if sensortype == float:
            self.test.assertAlmostEqual(got, expected, places, msg)
        else:
            self.test.assertEqual(got, expected, msg)

    def assert_sensor_status_equals(self, sensorname, expected_status, msg=None):
        """Assert that a sensor's status is equal to the given status.

        Parameters
        ----------
        sensorname : str
            The name of the sensor.
        expected_status : str
            The expected status of the sensor.
        msg : str, optional
            A custom message to print if the assertion fails.  If the string
            contains %r, it will be replaced with the sensor's value. A default
            message is defined in this method.
        """

        if msg is None:
            msg = "Status of sensor '%s' is %%r. Expected %r." % (sensorname, expected_status)

        got_status = self.get_sensor_status(sensorname)
        if '%r' in msg:
            msg = msg % got_status

        self.test.assertEqual(got_status, expected_status, msg)

    def assert_sensor_not_equal(self, sensorname, expected, sensortype=str, msg=None, places=7):
        """Assert that a sensor's value is not equal to the given value.

        Parameters
        ----------
        sensorname : str
            The name of the sensor.
        expected : obj
            The expected value of the sensor.  Type must match sensortype.
        sensortype : type, optional
            The type to use to convert the sensor value. Default: str.
        msg : str, optional
            A custom message to print if the assertion fails.  If the string
            contains %r, it will be replaced with the sensor's value. A default
            message is defined in this method.
        places : int, optional
            The number of places to use in a float comparison.  Has no effect if
            sensortype is not float. Default: 7.
        """

        if msg is None:
            places_msg = " (within %d decimal places)" % places if sensortype == float else ""
            msg = "Value of sensor '%s' is %%r. Expected a different value%s." % (sensorname, places_msg)

        got = self.get_sensor_value(sensorname, sensortype)
        if '%r' in msg:
            msg = msg % got

        if sensortype == float:
            self.test.assertNotAlmostEqual(got, expected, places, msg)
        else:
            self.test.assertNotEqual(got, expected, msg)

    def assert_sensors_equal(self, sensor_tuples, msg=None):
        """Assert that the values of several sensors are equal to the given values.

        Parameters
        ----------
        sensor_tuples : list of tuples
            A list of tuples specifying the sensor values to be checked.  See :meth:`expected_sensor_value_tuple`.
        msg : str, optional
            A custom message to print if the assertion fails.  If the string
            contains %r, it will be replaced with the sensor's value. A default
            message is defined in this method.
        """

        sensor_tuples = [self.expected_sensor_value_tuple(*t) for t in sensor_tuples]
        for sensorname, expected, sensortype, places in sensor_tuples:
            self.assert_sensor_equals(sensorname, expected, sensortype, msg=msg, places=places)

    def assert_sensors_not_equal(self, sensor_tuples, msg=None):
        """Assert that the values of several sensors are not equal to the given values.

        Parameters
        ----------
        sensor_tuples : list of tuples
            A list of tuples specifying the sensor values to be checked.  See :meth:`expected_sensor_value_tuple`.
        msg : str, optional
            A custom message to print if the assertion fails.  If the string
            contains %r, it will be replaced with the sensor's value. A default
            message is defined in this method.
        """

        sensor_tuples = [self.expected_sensor_value_tuple(*t) for t in sensor_tuples]
        for sensorname, expected, sensortype, places in sensor_tuples:
            self.assert_sensor_not_equal(sensorname, expected, sensortype, msg=msg, places=places)

    def wait_until_sensor_equals(self, timeout, sensorname, value, sensortype=str, places=7, pollfreq=0.1):
        """Wait until a sensor's value is equal to the given value, or time out.

        Parameters
        ----------
        timeout : float
            How long to wait before timing out, in seconds.
        sensorname : str
            The name of the sensor.
        value : obj
            The expected value of the sensor.  Type must match sensortype.
        sensortype : type, optional
            The type to use to convert the sensor value. Default: str.
        places : int, optional
            The number of places to use in a float comparison.  Has no effect if
            sensortype is not float. Default: 7.
        pollfreq : float, optional
            How frequently to poll for the sensor value. Default: 0.1.
        """

        stoptime = time.time() + timeout
        success = False

        if sensortype == float:
            cmpfun = lambda got, exp: abs(got-exp) < 10**-places
        else:
            cmpfun = lambda got, exp: got == exp

        lastval = None
        while time.time() < stoptime:
            lastval = self.get_sensor_value(sensorname, sensortype)
            if cmpfun(lastval, value):
                success = True
                break
            time.sleep(pollfreq)

        if not success:
            self.fail("Timed out while waiting %ss for %s sensor to become %s. Last value was %s." % (timeout, sensorname, value, lastval))

    # REQUEST PARAMETERS

    def test_sensor_list(self, expected_sensors, ignore_descriptions=False):
        """Test that the list of sensors on the device equals the provided list.

        Parameters
        ----------
        expected_sensors : list of tuples
            The list of expected sensors.  Each tuple contains the arguments
            returned by each sensor-list inform, as unescaped strings.
        ignore_descriptions : boolean, optional
            If this is true, sensor descriptions will be ignored in the
            comparison. Default: False.
        """

        def sensortuple(name, description, units, stype, *params):
            # ensure float params reduced to the same format
            if stype == "float":
                params = ["%g" % float(p) for p in params]
            return (name, description, units, stype) + tuple(params)

        reply, informs = self.blocking_request(Message.request("sensor-list"))

        expected_sensors = [sensortuple(*t) for t in expected_sensors]
        got_sensors = [sensortuple(*m.arguments) for m in informs]

        #print ",\n".join([str(t) for t in got_sensors])

        if ignore_descriptions:
            expected_sensors = [s[:1]+s[2:] for s in expected_sensors]
            got_sensors = [s[:1]+s[2:] for s in got_sensors]

        expected_set = set(expected_sensors)
        got_set = set(got_sensors)

        self.test.assertEqual(got_set, expected_set,
            "Sensor list differs from expected list.\nThese sensors are missing:\n%s\nFound these unexpected sensors:\n%s"
            % ("\n".join(sorted([str(t) for t in expected_set - got_set])), "\n".join(sorted([str(t) for t in got_set - expected_set])))
        )

    def assert_request_succeeds(self, requestname, *params):
        """Assert that the given request completes successfully when called with the given parameters.

        Parameters
        ----------
        requestname : str
            The name of the request.
        params : list of objects
            The parameters with which to call the request.
        """

        reply, informs = self.blocking_request(Message.request(requestname, *params))
        self.test.assertTrue(reply.reply_ok(),
            "Expected request '%s' called with parameters %r to succeed, but it failed %s."
            % (requestname, params, ("with error '%s'" % reply.arguments[1] if len(reply.arguments) >= 2 else "(with no error message)"))
        )

    def assert_request_fails(self, requestname, *params):
        """Assert that the given request fails when called with the given parameters.

        Parameters
        ----------
        requestname : str
            The name of the request.
        params : list of objects
            The parameters with which to call the request.
        """

        reply, informs = self.blocking_request(Message.request(requestname, *params))
        self.test.assertFalse(reply.reply_ok(),
            "Expected request '%s' called with parameters %r to fail, but it was successful."
            % (requestname, params)
        )

    def test_setter_request(self, requestname, sensorname, sensortype=str, good=(), bad=(), places=7):
        """Test a request which simply sets the value of a sensor.

        Parameters
        ----------
        requestname : str
            The name of the request.
        sensorname : str
            The name of the sensor.
        sensortype : type, optional
            The type to use to convert the sensor value. Default: str.
        good : list of objects
            A list of values to which this request can successfully set the
            sensor.  The object type should match sensortype.
        bad : list of objects
            A list of values to which this request cannot successfully set the
            sensor.  The object type should match sensortype.
        places : int, optional
            The number of places to use in a float comparison.  Has no effect if
            sensortype is not float. Default: 7.
        """

        for value in good:
            self.assert_request_succeeds(requestname, value)
            time.sleep(self._sensor_lag())

            self.assert_sensor_equals(
                sensorname, value, sensortype,
                "After request '%s' was called with parameter %r, value of sensor '%s' is %%r. Expected %r%s."
                % (requestname, value, sensorname, value, (" (within %d decimal places)" % places if sensortype == float else "")),
                places
            )

        for value in bad:
            self.assert_request_fails(requestname, value)

    def test_multi_setter_request(self, requestname, good=(), bad=()):
        """Test a request which causes several sensor values to change.

        Parameters
        ----------
        requestname : str
            The name of the request.
        good : list of tuples
            Each tuple contains a tuple of successful parameters, a tuple of
            expected sensor values (see :meth:`expected_sensor_value_tuple`), and
            optionally a dict of options. Permitted options are: "statuses" and
            a list of status tuples to check, or "delay" and a float in seconds
            specifying an additional delay before the sensors are expected to
            change.
        bad : list of tuples
            Each tuple is set of parameters which should cause the request to fail.
        """

        def testtuple(params, expected_values, options={}):
            return (params, expected_values, options)

        good = [testtuple(*t) for t in good]

        for params, expected_values, options in good:
            delay = options.get("delay", 0)
            expected_statuses = options.get("statuses", ())

            self.assert_request_succeeds(requestname, *params)
            time.sleep(self._sensor_lag() + delay)

            expected_values = [self.expected_sensor_value_tuple(*t) for t in expected_values]

            for sensorname, value, sensortype, places in expected_values:
                self.assert_sensor_equals(
                    sensorname, value, sensortype,
                    "After request '%s' was called with parameters %r, value of sensor '%s' is %%r. Expected %r%s."
                    % (requestname, params, sensorname, value, (" (within %d decimal places)" % places if sensortype == float else "")),
                    places
                )

            for sensorname, status in expected_statuses:
                self.assert_sensor_status_equals(
                    sensorname, status,
                    "After request '%s' was called with parameters %r, status of sensor '%s' is %%r. Expected %r."
                    % (requestname, params, sensorname, status)
                )

        for params in bad:
            self.assert_request_fails(requestname, *params)


class DeviceTestServer(DeviceServer):
    """Test server."""

    def __init__(self, *args, **kwargs):
        super(DeviceTestServer, self).__init__(*args, **kwargs)
        self.__msgs = []
        self.restart_queue = Queue.Queue()
        self.set_restart_queue(self.restart_queue)

    def setup_sensors(self):
        self.restarted = False
        self.add_sensor(DeviceTestSensor(
            Sensor.INTEGER, "an.int", "An Integer.", "count",
            [-5, 5],
            timestamp=12345, status=Sensor.NOMINAL, value=3
        ))

    def request_new_command(self, sock, msg):
        """A new command."""
        return Message.reply(msg.name, "ok", "param1", "param2")

    def request_raise_exception(self, sock, msg):
        """A handler which raises an exception."""
        raise Exception("An exception occurred!")

    def request_raise_fail(self, sock, msg):
        """A handler which raises a FailReply."""
        raise FailReply("There was a problem with your request.")

    def request_slow_command(self, sock, msg):
        """A slow command, sleeps for msg.arguments[0]"""
        time.sleep(float(msg.arguments[0]))
        return Message.reply(msg.name, "ok", msgid=msg.mid)

    def handle_message(self, sock, msg):
        self.__msgs.append(msg)
        super(DeviceTestServer, self).handle_message(sock, msg)

    def messages(self):
        return self.__msgs


class TestUtilMixin(object):
    """Mixin class implementing test helper methods for making
       assertions about lists of KATCP messages.
       """

    def _assert_msgs_length(self, actual_msgs, expected_number):
        """Assert that the number of messages is that expected."""
        num_msgs = len(actual_msgs)
        if num_msgs < expected_number:
            self.assertEqual(num_msgs, expected_number,
                             "Too few messages received.")
        elif num_msgs > expected_number:
            self.assertEqual(num_msgs, expected_number,
                             "Too many messages received.")

    def _assert_msgs_equal(self, actual_msgs, expected_msgs):
        """Assert that the actual and expected messages are equal.

           actual_msgs: list of message objects received
           expected_msgs: expected message strings
           """
        for msg, msg_str in zip(actual_msgs, expected_msgs):
            self.assertEqual(str(msg), msg_str)
        self._assert_msgs_length(actual_msgs, len(expected_msgs))

    def _assert_msgs_match(self, actual_msgs, expected):
        """Assert that the actual messages match the expected regular
           expression patterns.

           actual_msgs: list of message objects received
           expected: expected patterns
           """
        for msg, pattern in zip(actual_msgs, expected):
            self.assertTrue(re.match(pattern, str(msg)), "Message did match pattern %r: %s" % (pattern, msg))
        self._assert_msgs_length(actual_msgs, len(expected))

    def _assert_msgs_like(self, actual_msgs, expected):
        """Assert that the actual messages start and end with
           the expected strings.

           actual_msgs: list of message objects received
           expected_msgs: tuples of (expected_prefix, expected_suffix)
           """
        for msg, (prefix, suffix) in zip(actual_msgs, expected):
            str_msg = str(msg)

            if prefix and not str_msg.startswith(prefix):
                self.assertEqual(str_msg, prefix,
                    msg="Message '%s' does not start with '%s'."
                    % (str_msg, prefix)
                )

            if suffix and not str_msg.endswith(suffix):
                self.assertEqual(str_msg, suffix,
                    msg="Message '%s' does not end with '%s'."
                    % (str_msg, suffix)
                )
        self._assert_msgs_length(actual_msgs, len(expected))


# TODO: this is obsolete; remove it once all the tests that use it have been refactored
def device_wrapper(device):
    outgoing_informs = []

    def reply_inform(sock, msg, orig_msg):
        outgoing_informs.append(msg)

    def inform(sock, msg):
        outgoing_informs.append(msg)

    def mass_inform(msg):
        outgoing_informs.append(msg)

    def informs():
        return outgoing_informs

    def clear_informs():
        del outgoing_informs[:]

    device.inform = inform
    device.reply_inform = reply_inform
    device.mass_inform = mass_inform
    device.informs = informs
    device.clear_informs = clear_informs

    return device
