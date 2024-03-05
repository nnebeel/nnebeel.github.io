import datetime
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

def update_image(frame):
    now = datetime.datetime.now()
    np.random.seed(now.hour * 3600 + now.minute * 60 + now.second)
    image_data = np.random.rand(10, 10)
    im.set_array(image_data)
    ax.set_title(f"Abstract Time Image: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    return im,

# Set up the figure and the initial plot
fig, ax = plt.subplots()
im = ax.imshow(np.random.rand(10, 10), cmap='viridis')

# Create the animation
ani = FuncAnimation(fig, update_image, interval=1000)  # Update every 1000 milliseconds (1 second)

plt.show()
