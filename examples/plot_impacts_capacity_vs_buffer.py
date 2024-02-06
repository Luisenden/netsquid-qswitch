import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_pickle('diff_in_buffer_impact.pkl')
df['nnodes'] = 20-df.isna().sum(axis=1)
df = df.fillna(0)

df['diff_buffer'] = df['buffer_size'].apply(lambda x: x[0]-x[1])

cols = [name for name in df.columns if 'leaf_node' in name]
df = (df[cols].T/df[cols].sum(axis=1)).T.join(df[['diff_buffer', 'nnodes']])
print(df)

sns.lineplot(data=df, x='diff_buffer', y='leaf_node_0', hue='nnodes')
plt.legend(loc='center left', bbox_to_anchor=(1, 0.5)).set_title('# Nodes')
plt.xscale('symlog')
plt.ylabel('Capacity per Node (Hz)')
plt.grid()

plt.tight_layout()
plt.show()
