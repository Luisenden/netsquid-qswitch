import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_pickle('diff_in_buffer_impact.pkl')
df['nnodes'] = 20-df.isna().sum(axis=1)
df = df.fillna(0)

df['diff_buffer'] = df['buffer_size'].apply(lambda x: x[0]-x[1])

cols = [name for name in df.columns if 'leaf_node' in name]
df = (df[cols].T/df[cols].sum(axis=1)).T.join(df[['diff_buffer','nnodes']])
print(df)

sns.lineplot(data=df, x='diff_buffer', y=f'leaf_node_0', hue='nnodes')
plt.legend(loc='center left', bbox_to_anchor=(1, 0.5)).set_title('# Nodes')
plt.xscale('symlog')
plt.ylabel('Capacity per Node (Hz)')
plt.grid()

plt.tight_layout()
plt.show()

# df['rates'] = df['rates'].apply(lambda x: np.array(x)/1e6)
# df['overall capacity'] = df['mean_capacity']
# df['fideliy'] = df['mean_fidelity']
# df['nnodes'] = df['rates'].apply(len)

# cnodes = df.columns[df.columns.str.contains('leaf_node')]
# df['nodes contribution'] = df[cnodes].mean(axis=1)  # how much contribution per node on average
# df['control'] = df[cnodes].sum(axis=1) / (3 * df['overall capacity'])  # leaf node shares have to sum to 1

# # plot overall capacity and nodes contribution (+ control = 1)
# df_plot = df.melt('nnodes', value_vars=['overall capacity', 'nodes contribution', 'control'],
#                   var_name='Legend', value_name='val')
# sns.lineplot(data=df_plot, x='nnodes', y='val', hue='Legend', style='Legend')
# plt.ylabel(r'Capacity [Hz]')
# plt.legend().set_title('')
# plt.xlabel('# nodes')
# plt.yscale('log')
# plt.grid()
# plt.show()

# # plot the difference between minimum and maximum collected capacity
# df_diff = df.groupby(['nnodes'])[['mean_capacity'] + cnodes.to_list()].apply(lambda x:  np.max(x) - np.min(x))
# df_diff['leaf diff mean'] = df_diff[cnodes].mean(axis=1)
# df_diff = df_diff.join(df.groupby(['nnodes'])[['nodes contribution']].apply(np.mean), on='nnodes')
# df_diff = df_diff.join(df.groupby(['nnodes'])[['overall capacity']].apply(np.mean), on='nnodes')

# df_diff['overall diff'] = df_diff['mean_capacity']
# df_diff['leaf contribution'] = df_diff['nodes contribution']


# df_diff['overall impact'] = df_diff['mean_capacity']/df_diff['overall capacity']
# df_diff['leaf impact'] = df_diff['leaf diff mean']/df_diff['nodes contribution']

# df_diff = df_diff.reset_index()
# df_plot = df_diff[['nnodes', 'overall diff', 'leaf diff mean']]
# df_plot = df_plot.melt('nnodes', var_name='Legend', value_name='val')
# sns.lineplot(data=df_plot, x='nnodes', y='val', hue='Legend', style='Legend')
# plt.ylabel(r'Difference in Capacity [Hz]')
# plt.legend().set_title('')
# plt.xlabel('# nodes')
# plt.grid()
# plt.show()

# # plot the normalized difference in capacity and leaf node contribution; reflecting the impact of varied buffer sizes
# df_plot = df_diff[['nnodes', 'overall impact', 'leaf impact']]
# df_plot = df_plot.melt('nnodes', var_name='Legend', value_name='val')
# sns.lineplot(data=df_plot, x='nnodes', y='val', hue='Legend', style='Legend')
# plt.ylabel(r'Impact [1]')
# plt.xlabel('# nodes')
# plt.legend().set_title('')
# plt.grid()
# plt.show()
