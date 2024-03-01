import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import seaborn as sns
import matplotlib

plt.rcParams["axes.linewidth"] = 1
matplotlib.rcParams['text.usetex'] = True
matplotlib.rcParams['text.latex.preamble'] = r"""
                                         \usepackage{libertine}
                                         \usepackage[libertine]{newtxmath}
                                         \usepackage{sfmath}
                                         \usepackage[T1]{fontenc}
                                         """
matplotlib.rcParams['hatch.linewidth'] = 2
color = sns.color_palette("Set1")

root_path = 'multiple_vehicle'
time_step = 0.1



def get_rate(file_path, nodeId):
    df = pd.read_csv(file_path, index_col=False)
    if nodeId > 0:
        df = df[df['nodeId'] == nodeId]
    rate = []
    ts = []
    last_ts = 0
    start_ts = 0
    buf_size = 1362
    is_first = True
    recv_pkt = 0
    for _, row in df.iterrows():
        if is_first:
            is_first = False
            start_ts = row['timestamp']
        cur_ts = row['timestamp'] - start_ts

        while cur_ts > last_ts + time_step:
            rate.append(recv_pkt * buf_size * 8 / time_step / 1e6)
            ts.append(last_ts+start_ts)
            last_ts += time_step
            recv_pkt = 0
        recv_pkt += 1
    ret = pd.DataFrame({'ts': ts, 'rate': rate})
    return ret

def calculate():
    result = pd.DataFrame(columns=['rate', 'ts', 'num', 'method'])
    for num in range(1, 7):
        print('num:', num)
        for pi_id in range(1, num + 1):
            test_id = f"pi-{pi_id}/uc_{num}"
            df = get_rate(os.path.join(root_path, test_id, 'result.csv'), -1)
            df['num'] = num
            df['method'] = 'baseline_uc'
            result = pd.concat([result, df], ignore_index=True)

    for pi_id in range(1, 7):
        print('pi_id:', pi_id)
        test_id = f"pi-{pi_id}/bc"
        df = get_rate(os.path.join(root_path, test_id, 'result.csv'), -1)
        start_ts = df['ts'].iloc[0]
        df['method'] = 'baseline_bc'
        for num in range(1, 8 - pi_id):
            df.loc[(df['ts'] > start_ts + 10 * (num-1)) & (df['ts'] <= start_ts + 10 * num), 'num'] = num
        result = pd.concat([result, df], ignore_index=True)

    for pi_id in range(1, 7):
        print('pi_id:', pi_id)
        test_id = f"pi-{pi_id}/our"
        df = get_rate(os.path.join(root_path, test_id, 'result.csv'), -1)
        start_ts = df['ts'].iloc[0]
        df['method'] = 'our'
        for num in range(1, 8 - pi_id):
            df.loc[(df['ts'] > start_ts + 10 * (num-1)) & (df['ts'] <= start_ts + 10 * num), 'num'] = num
        result = pd.concat([result, df], ignore_index=True)
    result = result[result['num'].notnull()]
    result = result.astype({'num': 'int32'})
    result.to_csv('multicar_result.csv')


if __name__ == "__main__":
    # calculate()
    color[0], color[2] = color[2], color[0]
    df = pd.read_csv('multicar_result.csv')
    plt.figure(figsize=(8, 4))
    ax = sns.barplot(data=df, x='num', y='rate', hue='method', palette=color,
                     hue_order=['baseline_bc', 'baseline_uc', 'our'],
                     capsize=.1, errwidth=4, fill=False, linewidth=3)

    for bar in ax.patches[6:12]:
        bar.set_hatch('/')
        bar.set_edgecolor(color[1])
    for bar in ax.patches[:6]:
        bar.set_hatch('\\')
        bar.set_edgecolor(color[0])
    for bar in ax.patches[12:]:
        bar.set_hatch('-')
        bar.set_edgecolor(color[2])

    patches = ax.patches
    lines_per_err = 3
    for i, line in enumerate(ax.get_lines()):
        newcolor = patches[i // lines_per_err].get_edgecolor()
        line.set_color(newcolor)

    h, l = ax.get_legend_handles_labels()
    leg = ax.legend(h, ['802.11ac broadcast', '802.11ac unicast', '\it{Soar}'], fontsize=25,
                    borderaxespad=0.1, handlelength=1, ncols=1,
                    bbox_to_anchor=(0, 0, 1, 1), loc='upper right')
    # leg.get_title().set_fontsize('25')
    plt.ylabel('Throughput (Mbps)', fontsize=29)
    plt.xlabel('Number of Vehicles', fontsize=29)
    ax.yaxis.set_label_coords(-.105, 0.45)
    plt.tick_params(axis="both", labelsize=28, width=1, length=5)
    plt.tick_params(axis='x', length=0)
    ax.set_ylim(0, 114)
    ax.set_yticks([0, 25, 50, 75, 100])
    plt.grid(axis='y', linewidth=1, alpha=0.5)
    ax.set_axisbelow(True)
    # plt.tight_layout()
    plt.subplots_adjust(left=0.14, bottom=0.19, top=0.99, right=0.99)
    # plt.savefig('figure/fig_multicar_v3.pdf', dpi=600)
    plt.show()
