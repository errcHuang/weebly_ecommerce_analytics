import base64
import io
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html

from datetime import datetime as dt
from datetime import timedelta
from uszipcode import SearchEngine


import dateutil.parser
import gender_guesser.detector as gender

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px 

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, 
                external_stylesheets=external_stylesheets)
server = app.server

### LAYOUT OF APP ##

app.layout = html.Div(children=[
   ## hidden div storing dataframes ##
   html.Div(id='dataframe', style={'display':'none'}),
   html.Div(id='filtered-dataframe', style={'display':'none'}),
   #html.Div(id='filtered-dataframe'),

   #UPLOAD COMPONENT
   html.Div(id='upload-div', children=[
    dcc.Markdown('Upload CSV file of Weebly orders below',
                 style={'textAlign':'center', 'font-size': '20px'}),
    dcc.Markdown("*Don't know where that is? Go to [this page](https://www.weebly.com/editor/main.php#/store/orders) and click \"Export Orders\"*",
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
            'margin': '10px',
            'background-color': 'white'
        },
    ),
    html.P(id='filename',
           style={'textAlign':'center', 'font-style':'italic'}),
    html.Hr()
   ], 
   style={'background-color':'rgba(220,220,220,0.3)',
          'display':'block',
          'margin-bottom': '0px'}),

   ## Header ##
   html.Div([  
        html.H1("Weebly eCommerce Analytics" ,
                  style=dict(color='black'))
    ],
    className='row header'
   ),
    
   # advanced filtering
   html.Div([
       html.Div([
               dcc.Markdown('''
                      **Sales** provides insights into your sales from a 
                      product and geographical level. 
                      
                      **Customer** displays metrics about customer demographics 
                      and spending behavior.
                      ''')
        
       ], className='six columns'),
       html.Div([
           dcc.DatePickerRange(
               id='sales-datepickerrange',
               #min_date_allowed = dt.today(),
               #max_date_allowed = dt.today(),
               #start_date = min_date,
               #end_date = max_date,
               start_date_placeholder_text='Orders from',
               end_date_placeholder_text='Orders until',
               day_size=45,
               #with_portal=True
               )
           ],
           className='three columns',
           style={'float':'left',
                  'display':'inline-block'}
       ),
      html.Div([
        dcc.Markdown('**Advanced filtering**: \n'
                     'Compute below results for orders ONLY between the two dates. (*Selects all dates by default*)'),
        #dcc.Markdown('Compute below results for orders ONLY between the two dates. (*Selects all dates by default*)')
      ], className='three columns'),
    
    
   ], className='row'
   ),
               
   html.Br(),
   
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
                                {'label': 'By month', 'value':'Monthly'},
                                {'label': 'By week', 'value':'Weekly'},
                                {'label': 'By day', 'value':'Daily'}
                            ],
                            value='Monthly',
                            searchable=False,
                            style={'font-size':'20px'}
                        )
                    ], className='four columns'),
                ], 
                className='row'
                ),
                
                html.Br(),
                   
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
                        style={'display': 'inline-block',
                               'font-size': '20px',
                               'margin-left': '2.5%'}
                    ),
                    
                    dcc.Checklist(
                        id='orders-checkbox',
                        options=[
                                {'label':'View orders by coupon use','value':'y'},
                        ],
                        value=[],
                        style={'display': 'inline-block', 
                               'font-size': '20px',
                               'float': 'right',
                               'margin-right': '2.5%'}
                    )
                ], 
                className='row'),
                
                # Sales/Orders Bar Charts
                html.Div([
                    dcc.Graph(id='sales-graph',
                              style={'display':'inline-block'}),
                    dcc.Graph(id='orders-graph',
                              style={'display':'inline-block'})
                ], className='row'),
                    
                # US Sales Map
                html.Div([
                    dcc.Graph(id='sales-map',
                              style={'display':'inline-block'}),
                    dcc.Graph(id='product-sales-map',
                              style={'display':'inline-block'})
                ], className='row'),
                    
                #html.Hr(),

                #table
                html.Div([
                    dcc.Graph(id='revenue-table')
                ], className='row')
            ]),
           
           ## TAB 2 ##
           dcc.Tab(id='customer-tab', label='Customer', children=[
                html.Br(),
                # indicators row
                html.Div(id='customer-indicators',
                className='row'),
                html.Br(),
                
                # histograms
                html.Div([
                    dcc.Graph(id='dollars-histogram',
                              style={'display':'inline-block'}),
                    dcc.Graph(id='orders-histogram',
                              style={'display':'inline-block'})
                ], className='row'),
                    
                html.Br(),
                    
                # lifetime spend hist
                html.Div([
                    dcc.Graph(id='lifetime-histogram')
                ], 
                className='row',
                style={'margin':'auto',
                       'float':'center'}),
                    
                html.Br(),
                
                html.Div([
                    dcc.Graph(id='spenders-table'),
                ],
                className='row',
                style={'float':'center',
                       'margin':'auto'})
                   
           ])
   ], style={'font-size': '24px'}),
                        
   html.Hr(),
   html.Div([
       html.P(['Documentation/source ',
               html.A('here.', href='https://github.com/errcHuang/weebly_ecommerce_analytics/blob/master/README.md')],
               #' Contact ', html.A('me.', href='mailto:eric.huanghg@gmail.com')],
              style={'color':'#A9A9A9',
                     'font-size': '16px'})
   ], 
   style={
          'text-align':'center'}),
   html.Br(),
   
  ]
)

### CONTENT CREATION FUNCTIONS ##

# Output: HTML element that displays a box
#         with some KPI and an annotation above it
# Input:  text: a string
#         value: either a string or number
def indicator(text, value):
    return html.Div(
        [
            
            html.P(
                text,
                className="twelve columns",
                style={'text-align': 'center', 
                       'float': 'left',
                       'font-size': '20px'}
            ),
            html.P(
                value, ##
                style={'text-align':'center',
                       'color': '#2a3f5f',
                       'font-size': '30px'}
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

## SALES TAB CONTENT

# Output: fig: Plotly figure that shows bar chart of sales over time
# Input:  df: pandas dataframe (ideally from filtered-dataframe div element)
#         scale_str: string, either "Monthly" / "Daily" / "Weekly" for time scale
#         display_product: boolean of whether to subdivide chart by product
def display_sales(df, scale_str, display_product=False):
    #colors
    category20 = ["#b4ddd4", "#1c5b5a", "#66fcba", "#b31f59", "#46a26c", "#4443b4", 
                  "#dc8bfe", "#9525ba", "#2499d7", "#67486a", "#a8a2f4", "#3f16f9", 
                  "#efd453", "#7d4400", "#fec9af", "#af3007", "#fb899b", "#f6932e", 
                  "#9d8d88", "#fb57f9"]
                  
    # Change dataframe to daily, weekly, monthly
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
        
    # Subdivide data by product
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
        pivoted_sales.loc[:,'Shipping'] = shipping_price['Shipping Price']
        column_names = np.append(column_names,'Shipping')

        fig = px.bar(resample_sales(pivoted_sales, scale_str[0], True), x='Date', y='Sales ($)', 
                     color='Product Name', 
                     title='%s Sales ($) by product distribution' % scale_str,
                     color_discrete_sequence=category20)
    else: #just show aggregate
        daily_sales = df.groupby('Date', as_index=False)['Subtotal','Shipping Price'].sum()
        daily_sales.loc[:,'Sales ($)'] = daily_sales.loc[:,'Subtotal'] + daily_sales.loc[:,'Shipping Price']
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
        plot_bgcolor='rgba(211,211,211,0.35)',
        legend=go.layout.Legend(
            font=dict(
                size=13,
            )
        ),
        titlefont=dict(size=20),
    )
    fig.update_xaxes(tickfont=dict(size=15.5))
    fig.update_yaxes(tickfont=dict(size=15.5), title_font=dict(size=20))
                    
    fig.for_each_trace(
        lambda trace: trace.update(name=trace.name.replace("Product Name=", "")),
    )
    return fig

# Output: fig: Plotly figure that shows bar chart of # of orders over time
# Input:  df: pandas dataframe (ideally from filtered-dataframe div element)
#         scale_str: string, either "Monthly" / "Daily" / "Weekly" for time scale
#         display_promo: boolean of whether to subdivide chart by coupon use
def display_orders(df, scale_str, display_promo=False):
    # Preprocessing
    orders = df.drop_duplicates(subset='Order #').groupby('Date', as_index=False)['Order #', 'Coupon'].count()
    orders = orders.rename(columns={'Order #': 'Total', 'Coupon': 'Promo'}) 
    orders['Regular'] = np.subtract(orders['Total'], orders['Promo'])
    
    # Resample to make daily, weekly, or monthly data
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
    
    # Show division of orders by promo use
    if display_promo == True:
        fig = px.bar(resample_orders(orders, scale_str[0], True), 
                     x='Date', y='# of orders', color='Order type',
                     title="# of %s Orders by order type" % scale_str)

    else: #just show aggregate  
        fig = px.bar(resample_orders(orders,scale=scale_str[0]), x='Date', y='Total',
                     title="Total Number of %s Orders" % scale_str)
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
        plot_bgcolor='rgba(211,211,211,0.35)',
        legend=go.layout.Legend(
            font=dict(
                size=15,
            )
        ),
        titlefont=dict(size=20)
    )
                    
    fig.update_xaxes(tickfont=dict(size=15.5))
    fig.update_yaxes(tickfont=dict(size=15.5), title_font=dict(size=20))
    
    fig.for_each_trace(
        lambda trace: trace.update(name=trace.name.replace("Order type=", "")),
    )
    return fig

# Output: fig1: Plotly figure that shows dots of sales mapped to US zipcodes
#         fig2: Same as fig1 except subdivided by product
# Input:  df: pandas dataframe (ideally from filtered-dataframe div element)
def generate_sales_maps(df):
    # Preprocessing for figure 1
    single_orders = df.drop_duplicates('Order #').reset_index(drop=True)
    single_orders = single_orders.groupby(['Shipping Postal Code', 'Shipping City'], 
                                          as_index=False).sum()
    
    zips = single_orders['Shipping Postal Code'].astype(int).astype(str)
    
    # Converting zip code to latitude and longitude
    search = SearchEngine()
    lat = []
    long = []
    for z in zips:
        info = search.by_zipcode(z)
        lat.append(info.lat)
        long.append(info.lng)      
    single_orders['lat'] = pd.Series(lat)
    single_orders['long'] = pd.Series(long)
    
    #remove outlier
    #single_orders = single_orders.loc[single_orders.loc[:,'Subtotal']<250,:] #minus the $250 outlier order
    
    fig1 = px.scatter_geo(single_orders, lat='lat', lon='long', 
                         locationmode='USA-states',
                         size='Subtotal',
                         color='Subtotal',
                         color_continuous_scale='OrRd',
                         title='Sales excluding shipping ($) by zipcode',
                         hover_data=['Shipping Postal Code'],
                         hover_name='Shipping City',
                         scope='usa')
    
    fig1.update_traces(
        textfont=dict(size=20),
        marker=dict(
            colorbar=dict(
                tickfont=dict(size=12),
                titlefont=dict(size=30)
            ),
            line=dict(width=0.5,color='DarkSlateGrey'),
        ),
    )
            
    fig1.update_layout(
        titlefont=dict(size=20),
        margin=go.layout.Margin(
            l=0,
            r=0,
            b=0,
            t=50,
            pad=4
        ),
    )
    
    # Preprocessing for figure 2
    filled_df = df.fillna(method='ffill')
    zipcodes = filled_df['Shipping Postal Code'].astype(int).astype(str)
    order2zip = dict(zip( filled_df['Order #'], zipcodes)) #could potentially use this for re-adding dates back to orders hm
    product_orders = filled_df.groupby(['Order #','Product Name', 'Shipping City'], as_index=False).sum()
    product_orders["Shipping Postal Code"] = product_orders["Order #"].map(order2zip)
    
    
    # Converting zip code to latitude and longitude
    search = SearchEngine()
    lat = []
    long = []
    for z in product_orders['Shipping Postal Code']:
        info = search.by_zipcode(z)
        lat.append(info.lat)
        long.append(info.lng)      
    product_orders['lat'] = pd.Series(lat)
    product_orders['long'] = pd.Series(long)
    product_orders
    
    #figure
    fig2 = px.scatter_geo(product_orders, lat='lat', lon='long', 
                         locationmode='USA-states',
                         size='Sales ($)',
                         color='Product Name',
                         color_discrete_sequence=px.colors.qualitative.Set3,
                         title='Product Sales ($) by zipcode',
                         hover_data=['Shipping Postal Code'],
                         hover_name='Shipping City',
                         scope='usa',
                         opacity=0.8)
    
    # add border around scatter dots
    fig2.update_traces(marker=dict(line=dict(width=0.5,
                                            color='DarkSlateGrey')))
    # Remove =
    fig2.for_each_trace(
            lambda trace: trace.update(name=trace.name.replace("Product Name=", "")),
    )
    
    fig2.update_layout(
        legend=go.layout.Legend(
                font=dict(
                    size=14,
                ),
                traceorder="normal",
                itemsizing='constant'
        ),
        legend_orientation="h",
        titlefont=dict(size=20),
        margin=go.layout.Margin(
            l=0,
            r=0,
            b=0,
            t=50,
            pad=4
        ),
    )
    
    return fig1,fig2

# Output: fig: Plotly figure that shows table of each product and its sales
# Input:  df: pandas dataframe (ideally from filtered-dataframe div element)
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
    mnth_prods = generate_prods(df.loc[(df['Date'] >= mnth) & (df['Date'] <=today)])
    mnths3_prods = generate_prods(df.loc[(df['Date'] >= mnths3) & (df['Date'] <=today)])
    yr_prods = generate_prods(df.loc[(df['Date'] >= yr) & (df['Date'] <=today)])
    
    fig = go.Figure()
    
    fig.add_trace(
      go.Table(
        header=dict(values=list(all_prods.columns),
                    align='left',
                    font=dict(size=16)),
        cells=dict(
            values=all_prods.values.transpose(),
            align='left',
            font=dict(size=14)),
      )
    )
    
    fig.add_trace(
      go.Table(
        header=dict(values=list(mnth_prods.columns),
                    align='left',
                    font=dict(size=16)),
        cells=dict(
            values=mnth_prods.values.transpose(),
            align='left',
            font=dict(size=14)),
        visible=False
      )
    )
    
    fig.add_trace(
      go.Table(
        header=dict(values=list(mnths3_prods.columns),
                    align='left',
                    font=dict(size=16)),
        cells=dict(
            values=mnths3_prods.values.transpose(),
            align='left',
            font=dict(size=14)),
        visible=False
      )
    )
    
    fig.add_trace(
      go.Table(
        header=dict(values=list(yr_prods.columns),
                    align='left',
                    font=dict(size=16)),
        cells=dict(
            values=yr_prods.values.transpose(),
            align='left',
            font=dict(size=14)),
        visible=False
      )
    )
    
    fig.update_layout(title="% of Total Revenue by Product - All to date",
                      titlefont=dict(size=20))
    
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
                x=-0.0075,
                font=dict(size=14)
            )
        ],
        margin=go.layout.Margin(
            l=0,
            r=10,
            b=0,
            t=50,
            pad=4
        ),
    )

    return fig

## CUSTOMER TAB CONTENT

# Output: fig: Plotly figure that shows histogram of dollars spent per order
#         avg: Float which is the average purchase ($) per order
# Input:  df: pandas dataframe (ideally from filtered-dataframe div element)
def dollars_histogram(df):
    # Get dates
    today = dt.today().strftime('%Y-%m-%d')
    mnth = (dt.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    mnths3 = (dt.today() - timedelta(weeks=13)).strftime('%Y-%m-%d')
    yr = (dt.today() - timedelta(weeks=52)).strftime('%Y-%m-%d')
    
    # Groupby spending
    def generate_spend(data):
        ## From csv, returns dataframe with product name, Qty, Sales, % of Sales
        prods = data.groupby(['Order #'], as_index=False).sum()
        return prods
    
    # Filter data
    all_prods = generate_spend(df)
    mnth_prods = generate_spend(df.loc[(df['Date'] >= mnth) & (df['Date'] <=today)])
    mnths3_prods = generate_spend(df.loc[(df['Date'] >= mnths3) & (df['Date'] <=today)])
    yr_prods = generate_spend(df.loc[(df['Date'] >= yr) & (df['Date'] <=today)])
    
    # Generate figure
    fig = go.Figure()
    
    fig.add_trace(
      go.Histogram(x=all_prods['Subtotal']+all_prods['Shipping Price'])
    )
    
    fig.add_trace(
      go.Histogram(x=mnth_prods['Subtotal']+mnth_prods['Shipping Price'],
      visible=False)
    )
    
    
    fig.add_trace(
      go.Histogram(x=mnths3_prods['Subtotal']+mnths3_prods['Shipping Price'],
      visible=False)
    )
    
    
    fig.add_trace(
      go.Histogram(x=yr_prods['Subtotal']+yr_prods['Shipping Price'],
      visible=False)
    )
    
    fig.update_layout(title="Dollars ($) spent per order - All orders to date",
                      xaxis=dict(title='Dollars ($) spent per order'),
                      yaxis=dict(title='# of customers'))
    
    fig.update_layout(
        updatemenus=[
            go.layout.Updatemenu(
                active=0,
                buttons=list([
                    dict(label="All",
                         method="update",
                         args=[{"visible": [True, False, False, False]},
                               {"title": "Dollars ($) spent per order - All orders to date"}]),
                    dict(label="1m",
                         method="update",
                         args=[{"visible": [False, True, False, False]},
                               {"title": "Dollars ($) spent per order - Orders from past month"}]),
                    dict(label="3m",
                         method="update",
                         args=[{"visible": [False, False, True, False]},
                               {"title": "Dollars ($) spent per order - Orders from past 3 months"}]),
                    dict(label="1yr",
                         method="update",
                         args=[{"visible": [False, False, False, True]},
                               {"title": "Dollars ($) spent per order - Orders from past year"}]),
                ]),
                font=dict(size=14),
                x=-0.055
            )
        ],
        titlefont=dict(size=20)
    )
    fig.update_traces(marker_color='rgb(158,202,225)')
    
    fig.update_xaxes(tick0=0, tickfont=dict(size=15.5), title_font=dict(size=20))
    fig.update_yaxes(tickfont=dict(size=15.5), title_font=dict(size=20))
    
    #avg spend/order KPI
    avg = (all_prods.loc[:,'Subtotal'] + all_prods.loc[:,'Shipping Price']).mean() 
    
    return fig,avg

# Output: fig: Plotly figure that shows histogram of # of orders made per cust
#         avg: Float which is the average # of orders per customer
# Input:  df: pandas dataframe (ideally from filtered-dataframe div element)
def orders_histogram(df):
    # Get dates
    today = dt.today().strftime('%Y-%m-%d')
    mnth = (dt.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    mnths3 = (dt.today() - timedelta(weeks=13)).strftime('%Y-%m-%d')
    yr = (dt.today() - timedelta(weeks=52)).strftime('%Y-%m-%d')
    
    #Groupby orders
    def generate_orders(data):
        ## From csv, returns dataframe with product name, Qty, Sales, % of Sales
        prods = data.groupby(['Shipping Email', 'Shipping Postal Code','Shipping Region'], as_index=False)['Order #'].count().sort_values(by='Order #', ascending=False)
        return prods
    
    # Filtered data frames
    all_prods = generate_orders(df)
    mnth_prods = generate_orders(df.loc[(df['Date'] >= mnth) & (df['Date'] <=today)])
    mnths3_prods = generate_orders(df.loc[(df['Date'] >= mnths3) & (df['Date'] <=today)])
    yr_prods = generate_orders(df.loc[(df['Date'] >= yr) & (df['Date'] <=today)])
    
    # Generate figures
    fig = go.Figure()
    
    fig.add_trace(
      go.Histogram(x=all_prods['Order #'])
    )
    
    fig.add_trace(
      go.Histogram(x=mnth_prods['Order #'],
      visible=False)
    )
    
    
    fig.add_trace(
      go.Histogram(x=mnths3_prods['Order #'],
      visible=False)
    )
    
    
    fig.add_trace(
      go.Histogram(x=yr_prods['Order #'],
      visible=False)
    )
    
    fig.update_layout(title="# of orders per customer - All orders to date",
                      xaxis=dict(title='# of orders'),
                      yaxis=dict(title='# of customers'))
    
    fig.update_layout(
        updatemenus=[
            go.layout.Updatemenu(
                active=0,
                buttons=list([
                    dict(label="All",
                         method="update",
                         args=[{"visible": [True, False, False, False]},
                               {"title": "# of orders per customer - All orders to date"}]),
                    dict(label="1m",
                         method="update",
                         args=[{"visible": [False, True, False, False]},
                               {"title": "# of orders per customer - Orders from past month"}]),
                    dict(label="3m",
                         method="update",
                         args=[{"visible": [False, False, True, False]},
                               {"title": "# of orders per customer - Orders from past 3 months"}]),
                    dict(label="1yr",
                         method="update",
                         args=[{"visible": [False, False, False, True]},
                               {"title": "# of orders per customer - Orders from past year"}]),
                ]),
                font=dict(size=14),
                x=-0.055
            )
        ],
        titlefont=dict(size=20)
    )
    
    fig.update_xaxes(tick0=0, dtick=1, tickfont=dict(size=15.5), title_font=dict(size=20))
    fig.update_yaxes(tickfont=dict(size=15.5), title_font=dict(size=20))
    
    avg = all_prods['Order #'].mean() #avg orders per cust
    
    return fig, avg

# Output: fig: Plotly figure that shows table of top spending customers + info
# Input:  df: pandas dataframe (ideally from filtered-dataframe div element)
def spenders_table(df):
    ## TOP SPENDERS
    top_spenders = df.groupby(['Shipping First Name', 'Shipping Last Name','Shipping Email','Shipping City','Shipping Region'], as_index=False).sum().sort_values(by='Subtotal', ascending=False)
    top_spenders['Total Sales ($)'] = top_spenders.loc[:,'Subtotal']+top_spenders.loc[:,'Shipping Price']
    top_spenders = top_spenders.round(2)
    top_spenders = top_spenders.rename(columns={'Shipping Region':'State',
                                 'Shipping Email':'Email', 
                                 'Shipping City':'City',
                                 'Shipping First Name':'First Name',
                                 'Shipping Last Name':'Last Name'})
    top_spenders = top_spenders[['First Name', 'Last Name', 'Email', 'City','State','Total Sales ($)']]
    fig = go.Figure()
    
    fig.add_trace(
      go.Table(
        columnwidth=[60,60,120,60,40,60, 40],
        header=dict(values=list(top_spenders.columns),
                    align='left',
                    font=dict(size=16)
                   ),
        cells=dict(
            values=top_spenders.values.transpose(),
            align='left',
            fill=dict(color=['rgba(220,220,220,0.3)','rgba(220,220,220,0.3)','rgba(220,220,220,0.3)','rgba(220,220,220,0.3)','rgba(220,220,220,0.3)',
                             'lightyellow']),
            font=dict(size=15)
        ),
      )
    )
    
    fig.update_layout(title="Top Customers by Sales ($)",
                      titlefont=dict(size=20),
                      margin=go.layout.Margin(
                        l=40,
                        r=20,
                        b=0,
                        t=50,
                        pad=4
                      )
    )
                      
    return fig

# Output: fig: Plotly figure that shows histogram of lifetime spending / cust
#         avg: Float which is the average lifetime spending ($) of a customer
# Input:  df: pandas dataframe (ideally from filtered-dataframe div element)
def lifetime_histogram(df):
    cust_df = df.groupby(['Shipping Email'], as_index=False).sum()
    cust_df['Total Spending ($)'] = cust_df.loc[:,'Subtotal'] + cust_df.loc[:,'Shipping Price']
    
    fig = px.histogram(cust_df, x='Total Spending ($)')
    
    
    fig.update_layout(title="Lifetime Customer Sales ($)",
                      yaxis=dict(title='# of customers'),
                      titlefont=dict(size=20)
                     )
    
    fig.update_traces(marker_color='rgb(242,207,156)')
    
    fig.update_xaxes(tick0=0, tickfont=dict(size=15.5), title_font=dict(size=20))
    fig.update_yaxes(tickfont=dict(size=15.5), title_font=dict(size=20))
    
    avg = cust_df['Total Spending ($)'].mean()
    
    return fig, avg
            
### CALLBACK FUNCTIONS

# After data has been uploaded, update figures with no user input (Both tabs)                     
@app.callback([Output('customer-indicators', 'children'),
               Output('dollars-histogram', 'figure'),
               Output('orders-histogram', 'figure'),
               Output('spenders-table', 'figure'),
               Output('lifetime-histogram', 'figure')],
              [Input('filtered-dataframe', 'children')])
def render_customer_tab(json_data):
    if json_data is not None:
        df = pd.read_json(json_data)
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        df['Date'] = pd.to_datetime(df['Date'])
        

        d_hist, avg_spend_order = dollars_histogram(df)
        o_hist, avg_orders_cust = orders_histogram(df)
        s_table = spenders_table(df)
        l_hist, avg_cust_spend = lifetime_histogram(df)
        
        d = gender.Detector()
        unique_emails = df.drop_duplicates(subset='Shipping Email')
        first_names = unique_emails['Shipping First Name'].str.lower().dropna()
        genders = [d.get_gender(str(i).capitalize()) for i in first_names]
        gender_dict = dict(zip(*np.unique(genders,return_counts=True)))
        
        female_pct = (gender_dict['female']+gender_dict['mostly_female'])/(gender_dict['female']+gender_dict['mostly_female']+gender_dict['male']+gender_dict['mostly_male'])
        female_pct = female_pct*100
        
        indicators = html.Div([
            indicator('Avg lifetime spend / customer', '$%.2f' % avg_cust_spend),
            indicator('Avg purchase / order', '$%.2f' % avg_spend_order),
            indicator('% Female Customers', '%.1f%%' % female_pct)
        ])
        return indicators,d_hist,o_hist,s_table,l_hist
    else:
        return None,{},{},{},{}

# Create/adjust sales/orders figures based on change in checkbox (Sales Tab)
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

# Filters dataframe based on date range and outputs new dataframe and figures
@app.callback([Output('sales-indicators','children'),
               Output('filtered-dataframe', 'children'),
               Output('revenue-table', 'figure'),
               Output('sales-map', 'figure'),
               Output('product-sales-map','figure')],
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
                indicator('# of orders', len(filtered_df['Order #'].unique()))
                ]), 
                filtered_df.to_json(date_format='iso'),
                revenue_table(filtered_df),
                *generate_sales_maps(pd.read_json(json_data))]
        # Output filtered dataframe
    else:
        return [None,None,{},{},{}]
    
       

# Updates all date picker range settings based on uploaded file
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

# Parses dataframe from file and displays upload status
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
        df['Shipping City'] = df['Shipping City'].str.title()
        df = df.rename(columns={"Product Total Price": "Sales ($)"}) #rename column 
        
        return df.to_json(date_format='iso'), 'uploaded %s' % filename
    else:
        return [None, '']

if __name__ == '__main__':
    app.run_server(debug=True)