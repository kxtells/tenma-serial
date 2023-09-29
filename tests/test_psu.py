import glob
import os
import pytest
import sys

import serial

from tenma.tenmaDcLib import instantiate_tenma_class_from_device_response, TenmaException

def forAllChannels(psu, func):
    for channel in range(1, psu.NCHANNELS + 1):
        # Channel 3 on these PSUs is special
        # TODO: add specific tests for these
        if psu.MATCH_STR in ['72-13320', '72-13330'] and channel == 3:
            continue
        func(channel)

@pytest.fixture
def tenma_psu():
    port = os.getenv('TENMA_PORT', None)
    if port:
        psu = instantiate_tenma_class_from_device_response(port, debug=True)
    else:
        if sys.platform.startswith('win'):
            ports = ['COM%s' % i for i in range(1, 256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')
        # find the port where the PSU is connected
        for comport in ports:
            try:
                psu = instantiate_tenma_class_from_device_response(comport, debug=True)
            except (OSError, serial.SerialException):
                pass
    # for safety, turn off the PSU
    psu.OFF()
    yield psu
    psu.close()

def test_psu_init(tenma_psu):
    expectedModel = os.getenv('TENMA_MODEL', '72-2540')
    assert expectedModel in tenma_psu.getVersion()

def test_psu_voltage(tenma_psu):
    def assertVoltage(channel):
        assert tenma_psu.setVoltage(channel, 0) == 0
        assert tenma_psu.setVoltage(channel, tenma_psu.MAX_MV) == float(tenma_psu.MAX_MV)/1000
        # test invalid voltage
        with pytest.raises(TenmaException):
            tenma_psu.setVoltage(channel, tenma_psu.MAX_MV + 5)
        with pytest.raises(TenmaException):
            tenma_psu.setVoltage(channel, -1)
    forAllChannels(tenma_psu, assertVoltage)
    # test invalid channel
    with pytest.raises(TenmaException):
        tenma_psu.setVoltage(-1, tenma_psu.MAX_MV)
    with pytest.raises(TenmaException):
        tenma_psu.setVoltage(tenma_psu.NCHANNELS + 1, tenma_psu.MAX_MV)

def test_psu_current(tenma_psu):
    def assertCurrent(channel):
        assert tenma_psu.setCurrent(channel, 0) == 0
        assert tenma_psu.setCurrent(channel, tenma_psu.MAX_MA) == float(tenma_psu.MAX_MA)/1000
        # test invalid current
        with pytest.raises(TenmaException):
            tenma_psu.setCurrent(channel, tenma_psu.MAX_MA + 5)
        with pytest.raises(TenmaException):
            tenma_psu.setCurrent(channel, -1)
    forAllChannels(tenma_psu, assertCurrent)
    # test invalid channel
    with pytest.raises(TenmaException):
        tenma_psu.setCurrent(-1, tenma_psu.MAX_MA)
    with pytest.raises(TenmaException):
        tenma_psu.setCurrent(tenma_psu.NCHANNELS + 1, tenma_psu.MAX_MA)

def test_psu_memory(tenma_psu):
    for slot in range (1, tenma_psu.NCONFS + 1):
        # set voltage and current
        tenma_psu.setVoltage(1, slot * tenma_psu.MAX_MV / 5)
        tenma_psu.setCurrent(1, slot * tenma_psu.MAX_MA / 5)
        tenma_psu.saveConfFlow(slot, 1)
        # recall memory and assert voltages
        tenma_psu.recallConf(slot)
        assert tenma_psu.readVoltage(1) == slot * tenma_psu.MAX_MV / 5.0 / 1000.0
        assert tenma_psu.readCurrent(1) == slot * tenma_psu.MAX_MA / 5.0 / 1000.0
    # test invalid channels
    with pytest.raises(TenmaException):
        tenma_psu.saveConfFlow(1, -1)
    with pytest.raises(TenmaException):
        tenma_psu.saveConfFlow(1, tenma_psu.NCHANNELS + 1)
    # test invalid slots
    with pytest.raises(TenmaException):
        tenma_psu.saveConfFlow(-1, 1)
    with pytest.raises(TenmaException):
        tenma_psu.recallConf(-1)
    with pytest.raises(TenmaException):
        tenma_psu.saveConfFlow(tenma_psu.NCONFS + 1, 1)
    with pytest.raises(TenmaException):
        tenma_psu.recallConf(tenma_psu.NCONFS + 1)

def test_psu_beep(tenma_psu):
    tenma_psu.setBEEP(True)
    assert tenma_psu.getStatus()['BeepEnabled'] == True
    tenma_psu.setBEEP(False)
    assert tenma_psu.getStatus()['BeepEnabled'] == False

def test_psu_on(tenma_psu):
    # set voltage to 0 to try and be as safe as possible when turning on real PSUs
    def zeroVoltageCurernt(channel):
        assert tenma_psu.setVoltage(channel, 0) == 0
        assert tenma_psu.setCurrent(channel, 0) == 0
    def assertRunningCurrent(channel):
        assert tenma_psu.runningCurrent(channel) == 0
    forAllChannels(tenma_psu, zeroVoltageCurernt)
    tenma_psu.ON()
    assert tenma_psu.getStatus()['outEnabled'] == True
    forAllChannels(tenma_psu, assertRunningCurrent)
    tenma_psu.OFF()
    assert tenma_psu.getStatus()['outEnabled'] == False