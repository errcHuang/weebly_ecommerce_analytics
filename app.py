import base64
import io
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html

from datetime import datetime as dt
from datetime import timedelta
import dateutil.parser

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px 

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, 
                external_stylesheets=external_stylesheets)

# indicator box  
def indicator(text, value):
    return html.Div(
        [
            
            html.P(
                text,
                className="twelve columns",
                style={'text-align': 'center', 
                       'float': 'left',
                       'font-size': '15px'}
            ),
            html.P(
                value, ##
                style={'text-align':'center',
                       'color': '#2a3f5f',
                       'font-size': '35px'}
            ),
        ],
        className="four columns",
        style={
                'border':'1px solid #C8D4E3',
                'border-radius': '3px',
                'background-color': 'white',
                'height':'100px',
                'vertical-align':'middle',
              }
        
    )


app.layout = html.Div(children=[
   ## hidden div storing dataframes ##
   html.Div(id='dataframe', style={'display':'none'}),
   html.Div(id='filtered-dataframe', style={'display':'none'}),
   #html.Div(id='filtered-dataframe'),

   
   ## Upload ##
   html.Div([
    dcc.Markdown('Upload CSV file of Weebly orders below',
                 style={'textAlign':'center', 'font-size': '20px'}),
    dcc.Markdown("*Don't know where that is? [Download here](https://www.weebly.com/editor/main.php#/store/orders) by clicking \"Export Orders\"*",
                 style={'textAlign':'center', 'font-size': '16px'}),
    
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ', html.A('Select File')
        ]),
        style={
            'width': '100%',
            'height': '50px',
            'lineHeight': '50px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
    ),
    html.P(id='filename',
           style={'textAlign':'center', 'font-style':'italic'}),
    html.Hr()
   ]),
    
   ## Header ##
   html.Div([  
        html.H2("Vocé Tea Analytics" ,
                  style=dict(color='black'))
    ],
    className='row header'
   ),
   
   dcc.Tabs(id='tabs', children=[
           ## Tab 1 (Sales) ##
           dcc.Tab(id='sales-tab', label='Sales', children=[
                html.Br(),
                # Top controls
                html.Div([
                    # time resolution toggle
                    html.Div([
                        dcc.Dropdown(
                            id='sales-time-dropdown',
                            options=[
                                {'label': 'View data by month', 'value':'Monthly'},
                                {'label': 'View data by week', 'value':'Weekly'},
                                {'label': 'View data by day', 'value':'Daily'}
                            ],
                            value='Monthly',
                            searchable=False
                        )
                    ], className='four columns'),
                ], 
                className='row'
                ),
                
                html.Hr(),
                   
                # indicators row
                html.Div(id='sales-indicators',
                className='row'),
                         
                html.Br(),
                    
                # graph toggles
                html.Div([
                    dcc.Checklist(
                        id='sales-checkbox',
                        options=[
                                {'label':'View sales by product','value':'y'}
                        ],
                        value=[],
                        style={'width':'98%', 'display': 'inline-block', 'font-size': '20px'}
                    ),
                ], className='row'),
                
                # graphs
                html.Div([
                    dcc.Graph(id='sales-graph')        
                ], className='row'),
                    
                html.Div([
                    dcc.Checklist(
                        id='orders-checkbox',
                        options=[
                                {'label':'View orders by coupon use','value':'y'},
                        ],
                        value=[],
                        style={'width':'98%', 'display': 'inline-block', 'font-size': '20px'}
                    )
                ], className='row'),
            
                html.Div([
                    dcc.Graph(id='orders-graph')
                ], className='row'),
                
                #table
                html.Div([
                    dcc.Graph(id='revenue-table')
                ], className='row')
            ]),
           
           dcc.Tab(id='customer-tab', label='Customer')
   ], style={'font-size': 'large'}),
                        
   html.Hr(),

   # date selector
   html.Div([
       html.Div([
           dcc.DatePickerRange(
               id='sales-datepickerrange',
               #min_date_allowed = dt.today(),
               #max_date_allowed = dt.today(),
               #start_date = min_date,
               #end_date = max_date,
               start_date_placeholder_text='Orders from',
               end_date_placeholder_text='Orders until',
               day_size=45
               )
           ],
           className='three columns',
           style={'float':'left'}
       ),
      html.Div([
        dcc.Markdown('**Advanced filtering**'),
        dcc.Markdown('Compute above results for orders ONLY between the two dates. (*Selects all dates by default*)')
      ], className='four columns'),
   ], className='row'
   )
   
  ]
)
      
def display_sales(df, scale_str, display_product=False):
    category20 = ["#b4ddd4", "#1c5b5a", "#66fcba", "#b31f59", "#46a26c", "#4443b4", "#dc8bfe", "#9525ba", "#2499d7", "#67486a", "#a8a2f4", "#3f16f9", "#efd453", "#7d4400", "#fec9af", "#af3007", "#fb899b", "#f6932e", "#9d8d88", "#fb57f9"]
    def resample_sales(pivoted_orders, scale, to_process=False):

            pivoted_orders = pivoted_orders.resample(scale, on='Date').sum() ##ding ding ding

            if scale=='M':
                pivoted_orders.index = pivoted_orders.index.strftime('%Y-%m')
            elif scale=='W' or scale=='D':
                pivoted_orders.index = pivoted_orders.index.strftime('%Y-%m-%d')
            pivoted_orders = pivoted_orders.reset_index()
            pivoted_orders = pivoted_orders.rename(columns=dict(index='Date'))
            
            if to_process:
                pivoted_orders = pd.melt(pivoted_orders, id_vars=['Date'], 
                                         value_vars=column_names,
                                         var_name='Product Name',
                                         value_name='Sales ($)')
            return pivoted_orders
        
    if display_product == True:
        product_sales = df.groupby(['Date','Product Name'], as_index=False)['Sales ($)'].sum()
        pivoted_sales = product_sales.pivot(index='Date', columns='Product Name').fillna(value=0)
        pivoted_sales['Date'] = pivoted_sales.index
        pivoted_sales = pivoted_sales.reset_index(drop=True)

        #get unique column names from data
        column_names = list(filter(None,df['Product Name'].unique().astype(str)))
        column_names = sorted([c for c in column_names if c != 'nan' and c != 'None'])
        pivoted_sales.columns = np.append(column_names, 'Date')

        #add shipping price to the category
        shipping_price = df.groupby(['Date'], as_index=False)['Shipping Price'].sum()
        pivoted_sales['Shipping'] = shipping_price['Shipping Price']
        column_names = np.append(column_names,'Shipping')

        fig = px.bar(resample_sales(pivoted_sales, scale_str[0], True), x='Date', y='Sales ($)', 
                     color='Product Name', 
                     title='%s Sales ($) by product distribution' % scale_str,
                     color_discrete_sequence=category20)
    else: #just show aggregate
        daily_sales = df.groupby('Date', as_index=False)['Subtotal','Shipping Price'].sum()
        daily_sales['Sales ($)'] = daily_sales['Subtotal'] + daily_sales['Shipping Price']
        daily_sales = resample_sales(daily_sales, scale_str[0])
        fig = px.bar(daily_sales, x='Date', y='Sales ($)', title='%s Overall Sales' % scale_str)
        fig.update_traces(marker_color='rgb(158,202,225)')

    # add date buttons
    fig.update_layout(
        xaxis=go.layout.XAxis(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1m",
                         step="month",
                         stepmode="backward"),
                    dict(count=3,
                         label="3m",
                         step="month",
                         stepmode="backward"),
                    dict(count=6,
                         label="6m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="YTD",
                         step="year",
                         stepmode="todate"),
                    dict(count=1,
                         label="1y",
                         step="year",
                         stepmode="backward"),
                    dict(step="all")
                ])
            ),
            type="date"
        ),
        plot_bgcolor='rgba(211,211,211,0.35)'
    )
    fig.for_each_trace(
        lambda trace: trace.update(name=trace.name.replace("Product Name=", "")),
    )
    return fig

def display_orders(df, scale_str, display_promo=False):
    
    orders = df.drop_duplicates(subset='Order #').groupby('Date', as_index=False)['Order #', 'Coupon'].count()
    orders = orders.rename(columns={'Order #': 'Total', 'Coupon': 'Promo'}) 
    orders['Regular'] = np.subtract(orders['Total'], orders['Promo'])
    
    def resample_orders(pivoted_orders, scale='D', display_promo=False):

        pivoted_orders = pivoted_orders.resample(scale, on='Date').sum() ##ding ding ding

        if scale=='M':
            pivoted_orders.index = pivoted_orders.index.strftime('%Y-%m')
        elif scale=='W' or scale=='D':
            pivoted_orders.index = pivoted_orders.index.strftime('%Y-%m-%d')
        pivoted_orders = pivoted_orders.reset_index()
        pivoted_orders = pivoted_orders.rename(columns=dict(index='Date'))
        
        if display_promo:
            pivoted_orders = pd.melt(pivoted_orders, id_vars=['Date'], 
                                value_vars=['Regular', 'Promo'],
                                var_name='Order type',
                                value_name='# of orders')
        return pivoted_orders
    
    
    if display_promo == True:
        fig = px.bar(resample_orders(orders, scale_str[0], True), x='Date', y='# of orders', color='Order type')
        fig.update_layout(
            title=go.layout.Title(
                text="# of %s Orders by order type" % scale_str,
                xref="paper",
                x=0
            )
        )

    else: #just show aggregate  
        fig = px.bar(resample_orders(orders,scale=scale_str[0]), x='Date', y='Total')
        fig.update_layout(
            title=go.layout.Title(
                text="Total Number of Daily Orders",
                xref="paper",
                x=0
            )
        )
        fig.update_yaxes(title='# of orders')


    # add date buttons
    fig.update_layout(
        xaxis=go.layout.XAxis(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1m",
                         step="month",
                         stepmode="backward"),
                    dict(count=3,
                         label="3m",
                         step="month",
                         stepmode="backward"),
                    dict(count=6,
                         label="6m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="YTD",
                         step="year",
                         stepmode="todate"),
                    dict(count=1,
                         label="1y",
                         step="year",
                         stepmode="backward"),
                    dict(step="all")
                ])
            ),
            type="date"
        ),
        plot_bgcolor='rgba(211,211,211,0.35)'
    )
    fig.for_each_trace(
        lambda trace: trace.update(name=trace.name.replace("Order type=", "")),
    )
    return fig

## Create/adjust sales figures based on change in input
@app.callback([Output('sales-graph', 'figure'),
               Output('orders-graph', 'figure')],
              [Input('sales-checkbox','value'),
               Input('orders-checkbox', 'value'),
               Input('sales-time-dropdown', 'value'),
               Input('filtered-dataframe', 'children')])
def update_sales_figures(sales_cb, orders_cb, timestep, json_data):
    if json_data is not None:
        df = pd.read_json(json_data)
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Return figures depending on checkbox value
        if sales_cb: #box is checked
            sales_fig = display_sales(df, timestep, display_product=True)
        else:
            sales_fig = display_sales(df, timestep, display_product=False)
        
        if orders_cb:
            orders_fig = display_orders(df, timestep, display_promo=True)
        else:
            orders_fig = display_orders(df, timestep, display_promo=False)
        
        return sales_fig, orders_fig
    else:
        return {},{}


def revenue_table(df):
    today = dt.today().strftime('%Y-%m-%d')
    mnth = (dt.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    mnths3 = (dt.today() - timedelta(weeks=13)).strftime('%Y-%m-%d')
    yr = (dt.today() - timedelta(weeks=52)).strftime('%Y-%m-%d')
    
    
    def generate_prods(data):
        ## From csv, returns dataframe with product name, Qty, Sales, % of Sales
        prods = data.groupby(['Product Name'], as_index=False)['Product Quantity','Sales ($)'].sum()
        ship = pd.DataFrame([['Shipping',data['Shipping Price'].count(),data['Shipping Price'].sum()]], 
                 columns=['Product Name', 'Product Quantity', 'Sales ($)'])
        prods = prods.append(ship, ignore_index=True)
        prods['% of Total Sales'] = np.divide(prods['Sales ($)'], prods['Sales ($)'].sum())*100
        prods = prods.sort_values(by='Sales ($)', ascending=False).append(prods.sum().rename('Total'))
        prods = prods.reset_index(drop=True)
        prods = prods.round(2)
        prods.tail(1).loc[:,'Product Name'] = ['<b>Total</b>']
        return prods
    
    all_prods = generate_prods(df)
    mnth_prods = generate_prods(df.loc[(df['Date'] > mnth) & (df['Date'] <=today)])
    mnths3_prods = generate_prods(df.loc[(df['Date'] > mnths3) & (df['Date'] <=today)])
    yr_prods = generate_prods(df.loc[(df['Date'] > yr) & (df['Date'] <=today)])
    
    fig = go.Figure()
    
    fig.add_trace(
      go.Table(
        header=dict(values=list(all_prods.columns),
                    align='left'),
        cells=dict(
            values=all_prods.values.transpose(),
            align='left'),
      )
    )
    
    fig.add_trace(
      go.Table(
        header=dict(values=list(mnth_prods.columns),
                    align='left'),
        cells=dict(
            values=mnth_prods.values.transpose(),
            align='left'),
        visible=False
      )
    )
    
    fig.add_trace(
      go.Table(
        header=dict(values=list(mnths3_prods.columns),
                    align='left'),
        cells=dict(
            values=mnths3_prods.values.transpose(),
            align='left'),
        visible=False
      )
    )
    
    fig.add_trace(
      go.Table(
        header=dict(values=list(yr_prods.columns),
                    align='left'),
        cells=dict(
            values=yr_prods.values.transpose(),
            align='left'),
        visible=False
      )
    )
    
    fig.update_layout(title="% of Total Revenue by Product - All to date")
    
    fig.update_layout(
        updatemenus=[
            go.layout.Updatemenu(
                active=0,
                buttons=list([
                    dict(label="All",
                         method="update",
                         args=[{"visible": [True, False, False, False]},
                               {"title": "% of Total Revenue by Product - All to date"}]),
                    dict(label="1m",
                         method="update",
                         args=[{"visible": [False, True, False, False]},
                               {"title": "% of Total Revenue by Product - Past 1 month"}]),
                    dict(label="3m",
                         method="update",
                         args=[{"visible": [False, False, True, False]},
                               {"title": "% of Total Revenue by Product - Past 3 months"}]),
                    dict(label="1yr",
                         method="update",
                         args=[{"visible": [False, False, False, True]},
                               {"title": "% of Total Revenue by Product - Past 1 year"}]),
                ]),
            )
        ],
        height = (len(yr_prods.values.transpose()[0]) + 2) * 40 + 0
    )

    return fig

# filters dataframe based on start/end date and outputs new dataframe
@app.callback([Output('sales-indicators','children'),
               Output('filtered-dataframe', 'children'),
               Output('revenue-table', 'figure')],
              [Input('sales-datepickerrange', 'start_date'),
               Input('sales-datepickerrange', 'end_date'),
               Input('dataframe', 'children')]
             )
def update_df_figures(start_date, end_date, json_data):
    if json_data and start_date and end_date is not None:
        # Retrieve dataframe and preprocess
        df = pd.read_json(json_data)
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        df['Date'] = pd.to_datetime(df['Date'])
        
        start_date = dateutil.parser.parse(start_date)
        end_date = dateutil.parser.parse(end_date)

        # Create filtered dataframe betwen datepickerrange dates
        mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
        filtered_df = df.loc[mask]
        # Create sales indicator
#        return html.Div([
#                indicator('Avg daily sales from %s to %s' % (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')), '$%.2f' % filtered_df['Total'].mean()),
#                indicator('Total sales from %s to %s' % (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')), '$%.2f' % filtered_df['Total'].sum()),
#                indicator('# of orders from %s to %s' (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')), '$%d' % filtered_df['Order #'].count())
#        ])
        return [html.Div([
                indicator('Avg daily sales', '$%.2f' % (filtered_df['Subtotal']+filtered_df['Shipping Price']).mean()),
                indicator('Total sales', '$%.2f' % (filtered_df['Subtotal']+filtered_df['Shipping Price']).sum()),
                indicator('# of orders', filtered_df['Order #'].count())
                ]), 
                filtered_df.to_json(date_format='iso'),
                revenue_table(filtered_df)]
        # Output filtered dataframe
    else:
        return [None,None,{}]
    
       

# Updates all date picker range settings based on data frame
@app.callback([Output('sales-datepickerrange', 'min_date_allowed'),
               Output('sales-datepickerrange', 'max_date_allowed'),
               Output('sales-datepickerrange', 'start_date'),
               Output('sales-datepickerrange', 'end_date')],
              [Input('dataframe', 'children')])
def setup_date_range(json_data):
    if json_data is not None:
        df = pd.read_json(json_data)
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        df['Date'] = pd.to_datetime(df['Date'])
        
        ## Adjust min/max ranges on datepickerrange
        
        min_date = min(df['Date'])
        max_date = max(df['Date'])
        
        #add an extra day to max day
        #max_date_str = max_date.split('-')
        #max_date_str[2] = str(int(max_date_str[2])+1)
        #max_date = '-'.join(max_date_str)
        max_date = max_date + timedelta(days=1)
        
        return [min_date, max_date, min_date, max_date]
    
    else:
        return [None,None,None,None]

# Returns dataframe from file
@app.callback([Output('dataframe', 'children'),
               Output('filename', 'children')],
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def parse_file(contents, filename):
    if contents is not None: #nothing uploaded
        # Reading the file
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            if 'csv' in filename:
                # Assume that the user uploaded a CSV file
                df = pd.read_csv(
                    io.StringIO(decoded.decode('utf-8')))
            elif 'xls' in filename:
                # Assume that the user uploaded an excel file
                df = pd.read_excel(io.BytesIO(decoded))
            else: 
                raise Exception('Not a CSV or excel file.')
        except Exception as e:
            print(e)
            return [None, html.Div([
                'There was an error processing this file. Please upload a proper CSV/excel file.'
            ])]
        
        # Processing the file
        df['Date'] = pd.to_datetime(df['Date']) # add datetime formatting
        df['Shipping Email'] = df['Shipping Email'].str.lower() #converting to lower case
        df = df.rename(columns={"Product Total Price": "Sales ($)"}) #rename column 
        
        return df.to_json(date_format='iso'), 'uploaded %s' % filename
    else:
        return [None, '']

if __name__ == '__main__':
    app.run_server(debug=True)