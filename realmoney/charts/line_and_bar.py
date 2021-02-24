import datetime as dt
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def line_and_bar_plot(title: str, df: pd.DataFrame, bar_column: str, line_column: str = None, date_column: str = 'Date', 
                    x_ticks: int = 5, from_: dt.date = None, to_: dt.date = None, fig_size=[12, 8], bar_palette_fn=None):
    """
    Bar Plot plus optional line plot for a dataframe representing a time series
    """

    sns.set(style="darkgrid")

    df = df.copy()
    df = df.sort_values(by=date_column)
    
    from_=from_ or df[date_column].min()
    to_=to_ or df[date_column].max()
    
    df = df[df['Date'] >= from_]
    df = df[df['Date'] <= to_]

    x_range = range(len(df))
    df['__INT_INDEX__'] = x_range
    
    if bar_palette_fn is None: # red-green palette for default
        bar_pallete_fn = lambda r: 'r' if r[bar_column] < 0 else 'g'

    bar_palette = {r['__INT_INDEX__']: bar_palette_fn(r) for r in df.to_dict(orient='records')}


    fig, ax1 = plt.subplots(figsize=fig_size)
    
    x_data = zip(x_range, df[date_column])
    x_ticks = [xd[1].strftime('%b-%d') if xd[0] % x_ticks == 0 else '' for xd in x_data]

    plot = sns.barplot(data=df, y=bar_column, x='__INT_INDEX__', alpha=1, palette=bar_palette, ax=ax1)

    ax2 = ax1.twinx()
    ax2.grid(False)
    
    plot = sns.lineplot(data=df, y=line_column, x='__INT_INDEX__', marker='o')
    plot.set_xticks(x_range) # <--- set the ticks first
    plot.set_xticklabels(x_ticks);
    
    
    x_range=range(len(df))
    x_data = zip(x_range, df['Date'])
    x_ticks = [xd[1].strftime('%b-%d') if xd[0] % 3 == 0 else '' for xd in x_data]
    #ax.set_xticks(df['X']) # <--- set the ticks first
    ax1.set_xticklabels(x_ticks)
    ax1.set(xlabel="Date")
    ax1.set_title(title)
