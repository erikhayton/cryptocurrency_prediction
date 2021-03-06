"""Plot portfolio

Plot diffrent portfolio informations

Run:
    python plot_portfolio.py --help
"""

import configs.get_datasets
import pandas as pd
import numpy as np
from configs.vars import coins, days, todays_day, todays_month, currency
from configs.functions import print_dollar
import plotly.graph_objs as go
import plotly.offline as offline
import fbprophet
#---------------------------------------------------------------------------------->
def _build_layout(title, y_axis_title=None, y_axis_type=None):
    """[summary]
    
    Arguments:
        title {[type]} -- [description]
        y_axis_title {[type]} -- [description]
    
    Keyword Arguments:
        y_axis_type {[type]} -- [description] (default: {None})
    
    Returns:
        [type] -- [description]
    """

    layout = go.Layout(plot_bgcolor='#2d2929',
                       paper_bgcolor='#2d2929',
                       title=title,
                       font=dict(color='rgb(255, 255, 255)'),
                       legend=dict(orientation="h"),
                       yaxis=dict(title=y_axis_title, type=y_axis_type))
    return layout
#---------------------------------------------------------------------------------->
def _build_data(pct_change=False):
    """[summary]
    
    Keyword Arguments:
        pct_change {bool} -- [description] (default: {False})
    
    Returns:
        [type] -- [description]
    """

    data = []
    for coin in coins:
        df = pd.read_csv('datasets/{}-{}_{}_d{}_{}.csv'.format(todays_day,
                                                                todays_month,
                                                                coin,
                                                                days,
                                                                currency))
        trace = go.Scatter(x=df.date,
                           y=df['prices'].pct_change()*100 if pct_change else df['prices'],
                           name = str(coin).upper())
        data.append(trace)
    return data
#---------------------------------------------------------------------------------->
def plot(data, layout, file_name):
    """Plot the data according to data and layout functions.
    
    Arguments:
        title {str} -- Graph title
        y_axis_title {str} -- Y axis title
    
    Keyword Arguments:
        pct_change {bool} -- Price is shown in percent of change (default: {False})
        y_axis_type {str} -- Scale is linear or log (default: {None})
    
    """
    offline.plot({'data': data,
                 'layout': layout},
                 filename='{}-{}_{}-{}.html'.format(file_name,
                                                    todays_day,
                                                    todays_month,
                                                    currency))
#---------------------------------------------------------------------------------->
def main():
    """[summary]
    """

    if FLAGS.change:
        plot(data=_build_data(pct_change=True),
             layout=_build_layout(title='Portfolio Change in {} Days'.format(days),
                                  y_axis_title='Change (%)'),
             file_name='pct_change')
#---------------------------------------------------------------------------------->
    if FLAGS.linear or FLAGS.log:
        plot(data=_build_data(),
             layout=_build_layout(title='Portfolio {} in {} Days'.format('Linear' if FLAGS.linear 
                                                                         else 'Log Scale', days),
                                  y_axis_title='Price ({})'.format(currency.upper()),
                                  y_axis_type='linear' if FLAGS.linear else 'log'),
             file_name='linear' if FLAGS.linear else 'log')
#---------------------------------------------------------------------------------->
    if FLAGS.forecast_coin and FLAGS.forecast_days and FLAGS.forecast_scale:
        df = pd.read_csv('datasets/{}-{}_{}_d{}_{}.csv'.format(todays_day,
                                                               todays_month,
                                                               FLAGS.forecast_coin,
                                                               days,
                                                               currency))
        df['ds'] = df['date']
        df['y'] = df['prices']
        df = df[['ds', 'y']]
        df_prophet = fbprophet.Prophet(changepoint_prior_scale=FLAGS.forecast_scale)
        df_prophet.fit(df)
        df_forecast = df_prophet.make_future_dataframe(periods=int(FLAGS.forecast_days))
        df_forecast = df_prophet.predict(df_forecast)
        data = [
            go.Scatter(x=df['ds'], y=df['y'], name='Price', line=dict(color='#94B7F5')),
            go.Scatter(x=df_forecast['ds'], y=df_forecast['yhat'], name='yhat'),
            go.Scatter(x=df_forecast['ds'], y=df_forecast['yhat_upper'], fill='tonexty',
                       mode='none', name='yhat_upper', fillcolor='rgba(0,201,253,.21)'),
            go.Scatter(x=df_forecast['ds'], y=df_forecast['yhat_lower'], fill='tonexty',
                       mode='none', name='yhat_lower', fillcolor='rgba(252,201,5,.05)'),
        ]
        plot(data=data,
             layout=_build_layout(title='{} Days of {} Forecast'.format(FLAGS.forecast_days,
                                                                        currency.upper()),
                                  y_axis_title='Price ({})'.format(currency.upper())),
             file_name='forecast')
#---------------------------------------------------------------------------------->
    if FLAGS.correlation:
        base_df = pd.read_csv('datasets/{}-{}_{}_d{}_{}.csv'.format(todays_day,
                                                                todays_month,
                                                                coins[0],
                                                                days,
                                                                currency))
        for coin in coins:
            coin_price = pd.read_csv('datasets/{}-{}_{}_d{}_{}.csv'.format(todays_day,
                                                            todays_month,
                                                            coin,
                                                            days,
                                                            currency))
            base_df[coin] = coin_price['prices']
        base_df.set_index('date', inplace=True)
        base_df.drop(['market_caps','prices','total_volumes'], 1, inplace=True)
        base_df.to_csv('datasets/teste_correlation.csv')
        heatmap = go.Heatmap(
            z=base_df.pct_change().corr(method=FLAGS.correlation).values,
            x=base_df.pct_change().columns,
            y=base_df.pct_change().columns,
            colorbar=dict(title='Pearson Coefficient'),
            colorscale=[[0, 'rgb(255,0,0)'], [1, 'rgb(0,255,0)']],
            zmin=-1.0,
            zmax=1.0
        )
        plot(data=[heatmap],
             layout=_build_layout(title='{} Correlation Heatmap - {} days'.format(FLAGS.correlation, days).title()),
             file_name='correlation')
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Deep analysis of cryptocurrencies')
    parser.add_argument('--correlation', type=str, default=None, help='Plot correlation heatmap. Choose the method {pearson, kendall, spearman} ')
    parser.add_argument('--change', action='store_true', help='Plot portfolio percent change')
    parser.add_argument('--linear', action='store_true', help='plot portfolio linear prices')
    parser.add_argument('--log', action='store_true', help='Plot portfolio log prices')
    parser.add_argument('--forecast_coin', '-fc', type=str, help='Coin name')
    parser.add_argument('--forecast_days', '-fd', type=int, default=5, help='How many days to forecast')
    parser.add_argument('--forecast_scale', '-fs', type=float, default=0.1, help='Changepoint priot scale [0.1 ~ 0.9]')
    FLAGS = parser.parse_args()
    main()
    print_dollar()