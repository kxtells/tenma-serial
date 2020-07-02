import time

# Import plotting library
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# Import tenma library
from tenma.tenmaDcLib import instantiate_tenma_class_from_device_response, TenmaException

# Retrieve a proper tenma handler for your unit (mainly tries to keep values
# within ranges)
tenma = instantiate_tenma_class_from_device_response('/dev/ttyACM0')

print(tenma.getVersion())

fig, ax = plt.subplots()
ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax.grid(True)

data = []
tstamps = []
while True:
    current = tenma.runningCurrent(1)
    voltage = tenma.runningVoltage(1)
    timestamp = time.time()

    data.append(voltage)
    tstamps.append(timestamp)

    plt.clf()
    plt.plot(tstamps, data)
    plt.pause(0.5)
