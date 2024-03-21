import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
# from mcs_plot import get_rate
import os

plt.rcParams["axes.linewidth"] = 1
# matplotlib.rcParams['text.usetex'] = True
# matplotlib.rcParams['text.latex.preamble'] = r"""
#                                          \usepackage{libertine}
#                                          \usepackage[libertine]{newtxmath}
#                                          \usepackage{sfmath}
#                                          \usepackage[T1]{fontenc}
#                                          """
matplotlib.rcParams['hatch.linewidth'] = 2
color = sns.color_palette("Set1")

root_path = 'coding_data'

# coding parameter, mcs: 4
# app_rate: (nin, nout)
# 10: (10, 20)
# 20: (10, 20)
# 30: (15, 10)


def change_width(ax, new_value):
    for patch in ax.patches:
        print(patch.get_x())
        current_width = patch.get_width()
        diff = current_width - new_value
        # we change the bar width
        patch.set_width(new_value)
        # we recenter the bar
        # patch.set_x(patch.get_x() + diff * .5)



if __name__ == '__main__':

    data = pd.DataFrame()
    app_rates = [10, 20, 30]
    methods = ['our', 'ourcode']
    for app_rate in app_rates:
        for method in methods:
            df = pd.read_csv(f'result_coding/{method}_{app_rate}.csv')
            data = pd.concat([data, df], ignore_index=True)
    data = data.astype({'app_rate': 'int32'})

    plt.figure(figsize=(8, 6))
    color[0], color[1] = color[1], color[0]
    ax = sns.barplot(data=data, x='app_rate', y='pdr', hue='method',
                     hue_order=['our', 'ourcode'], palette=color,
                     capsize=.1, errwidth=4, width=0.6, fill=False, linewidth=3)


    for bar in ax.patches[:3]:
        bar.set_hatch('/')
        bar.set_edgecolor(color[0])
    for bar in ax.patches[3:]:
        bar.set_hatch('-')
        bar.set_edgecolor(color[1])

    patches = ax.patches
    lines_per_err = 3
    for i, line in enumerate(ax.get_lines()):
        newcolor = patches[i // lines_per_err].get_edgecolor()
        line.set_color(newcolor)

    h, l = ax.get_legend_handles_labels()
    leg = ax.legend(h, ['w/o ECC', 'w/ ECC'], fontsize=35, handlelength=1, frameon=False,
                    bbox_to_anchor=(-.03, 0, 1, 1.22), loc='upper left', ncols=2)

    # change_width(ax, .3)
    # leg.get_title().set_fontsize('18')
    plt.ylabel('PDR', fontsize=37)
    plt.xlabel('App. Data Rate (Mbps)', fontsize=37)
    # ax[0].yaxis.set_label_coords(-.05, -.5)
    plt.tick_params(axis="both", labelsize=37, width=1, length=5)
    plt.yticks(np.linspace(0, 1, 3))
    plt.grid(axis='y', linewidth=1, alpha=0.5)
    ax.set_axisbelow(True)
    # plt.tight_layout()
    plt.subplots_adjust(top=0.9, left=0.155, bottom=0.19, right=0.99)
    plt.show()
