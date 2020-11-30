import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation, gridspec
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d.art3d import Line3DCollection


def make_anim_simple_osc(
    x,
    y,
    dt=0.001,
    ms_per_frame=10,
    trail_length=500,
    figsize=(8, 8),
    cmap="gist_yarg",
    lw=2,
):
    def make_2d_segments(x_data, y_data):
        # Convert the x, y arrays into line segments
        vertices = np.array([x_data, y_data]).T.reshape(-1, 1, 2)
        segments = np.concatenate([vertices[:-1], vertices[1:]], axis=1)
        return segments

    # Make matplotlib figure
    fig = plt.figure(figsize=figsize)
    ax = plt.subplot(111)
    ax.set_aspect("equal")

    # Set the axis limits
    axis_limits = max(max(np.absolute(x)), max(np.absolute(y))) * 1.2
    ax.set_xlim(-axis_limits, axis_limits)
    ax.set_ylim(-axis_limits, axis_limits)
    ax.set_xlabel("")

    # Make the initial line collection object
    lsegs = LineCollection(make_2d_segments([0], [0]), cmap=cmap, lw=lw)
    lsegs.set_array(np.arange(trail_length))
    ax.add_collection(lsegs)

    # Time label
    time_str = ax.text(-axis_limits / 1.1, -axis_limits / 1.1, "", fontsize=12)

    # Number of data points to skip per frame
    skip = int(ms_per_frame / (1000.0 * dt))

    def anim_init():
        # Animation initialization function
        lsegs.set_segments(None)
        time_str.set_text("")
        return lsegs, time_str

    def animate_frame(i):
        # Animiation function for each frame
        lsegs.set_segments(
            make_2d_segments(
                x[max(i * skip - trail_length, 0) : i * skip + 1],
                y[max(i * skip - trail_length, 0) : i * skip + 1],
            )
        )
        time_str.set_text("Time: %0.2fs" % (i * skip * dt))
        return lsegs, time_str

    num_frames = len(x) // skip
    anim = animation.FuncAnimation(
        fig,
        animate_frame,
        init_func=anim_init,
        frames=num_frames,
        interval=ms_per_frame,
        blit=True,
    )
    plt.close(anim._fig)
    return fig, ax, anim


def make_anim_controlled_osc(
    x,
    y,
    w,
    dt=0.001,
    ms_per_frame=10,
    trail_length=500,
    figsize=(8, 6),
    cmap="gist_yarg",
    lw=2,
    dotsize=20,
):
    def make_2d_segments(x_data, y_data):
        # Convert the x, y arrays into line segments
        vertices = np.array([x_data, y_data]).T.reshape(-1, 1, 2)
        segments = np.concatenate([vertices[:-1], vertices[1:]], axis=1)
        return segments

    # Make matplotlib figure
    fig = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(1, 2, width_ratios=[12, 1])
    gs.update(wspace=0)
    ax = plt.subplot(gs[0], aspect="equal")

    # Set the axis limits
    axis_limits = max(max(np.absolute(x)), max(np.absolute(y))) * 1.2
    ax.set_xlim(-axis_limits, axis_limits)
    ax.set_ylim(-axis_limits, axis_limits)
    ax.set_xticks(
        np.linspace(-np.round(axis_limits, 0), np.round(axis_limits, 0), num=5)
    )
    ax.set_yticks(
        np.linspace(-np.round(axis_limits, 0), np.round(axis_limits, 0), num=5)
    )

    # Make the initial line collection object
    lsegs = LineCollection(make_2d_segments([0], [0]), cmap=cmap, lw=lw)
    lsegs.set_array(np.arange(trail_length))
    ax.add_collection(lsegs)

    # Time label
    time_str = ax.text(-axis_limits / 1.1, -axis_limits / 1.1, "", fontsize=12)

    # Sidebar plot
    ax2 = plt.subplot(gs[1])
    speed_limits = max(np.absolute(w)) * 1.2
    ax2.set_ylim(-speed_limits, speed_limits)
    ax2.set_yticks(np.linspace(-int(speed_limits), int(speed_limits), num=5))
    ax2.set_xticks([])
    ax2.yaxis.set_label_position("right")
    ax2.yaxis.tick_right()
    ax2.spines["left"].set_visible(False)
    ax2.spines["top"].set_visible(False)
    ax2.spines["bottom"].set_visible(False)
    (dot,) = ax2.plot([], [], "r.", markersize=dotsize)

    # Number of data points to skip per frame
    skip = int(ms_per_frame / (1000.0 * dt))

    def anim_init():
        # Animation initialization function
        lsegs.set_segments(None)
        dot.set_data([], [])
        time_str.set_text("")
        return lsegs, dot, time_str

    def animate_frame(i):
        # Animiation function for each frame
        lsegs.set_segments(
            make_2d_segments(
                x[max(i * skip - trail_length, 0) : i * skip + 1],
                y[max(i * skip - trail_length, 0) : i * skip + 1],
            )
        )
        dot.set_data([0.015], [w[i * skip]])
        time_str.set_text("Time: %0.2fs" % (i * skip * dt))
        return lsegs, dot, time_str

    num_frames = len(x) // skip
    anim = animation.FuncAnimation(
        fig,
        animate_frame,
        init_func=anim_init,
        frames=num_frames,
        interval=ms_per_frame,
        blit=True,
    )
    plt.close(anim._fig)
    return fig, ax, ax2, anim


def make_anim_chaotic(
    x,
    y,
    z,
    dt=0.001,
    ms_per_frame=10,
    trail_length=500,
    figsize=(8, 8),
    cmap="gist_yarg",
    lw=2,
):
    def make_3d_segments(x_data, y_data, z_data):
        # Convert the x, y arrays into line segments
        vertices = np.array([x_data, y_data, z_data]).T.reshape(-1, 1, 3)
        segments = np.concatenate([vertices[:-1], vertices[1:]], axis=1)
        return segments

    # Make matplotlib figure
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="3d")

    # Set the axis limits
    axis_limits = (
        max(max(np.absolute(x)), max(np.absolute(y)), max(np.absolute(z))) * 1.2
    )
    ax.set_xlim(-axis_limits, axis_limits)
    ax.set_ylim(-axis_limits, axis_limits)
    ax.set_zlim(-axis_limits, axis_limits)

    # Make the initial line collection object
    lsegs = Line3DCollection(make_3d_segments([0], [0], [0]), cmap=cmap, lw=lw)
    lsegs.set_array(np.arange(trail_length))
    ax.add_collection3d(lsegs)

    # Time label
    time_str = ax.text(
        -axis_limits / 1.05, -axis_limits / 1.05, -axis_limits / 1.05, "", fontsize=12
    )

    # Number of data points to skip per frame
    skip = int(ms_per_frame / (1000.0 * dt))

    def anim_init():
        # Animation initialization function
        lsegs.set_segments(None)
        time_str.set_text("")
        return lsegs, time_str

    def animate_frame(i):
        # Animiation function for each frame
        lsegs.set_segments(
            make_3d_segments(
                x[max(i * skip - trail_length, 0) : i * skip + 1],
                y[max(i * skip - trail_length, 0) : i * skip + 1],
                z[max(i * skip - trail_length, 0) : i * skip + 1],
            )
        )
        time_str.set_text("Time: %0.2fs" % (i * skip * dt))
        return lsegs, time_str

    num_frames = len(x) // skip
    anim = animation.FuncAnimation(
        fig,
        animate_frame,
        init_func=anim_init,
        frames=num_frames,
        interval=ms_per_frame,
        blit=True,
    )
    plt.close(anim._fig)
    return fig, ax, anim
