import sys, argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime as dt

# %matplotlib inline

class constructTable(object):
    """
    Like Cursor but the crosshair snaps to the nearest x, y point.
    For simplicity, this assumes that *x* is sorted.
    """

    def __init__(self, df, columns=None):
        self.df = df
        if columns == None:
            self.columns = columns
        else:
            self.columns = columns
            self.elements = list(df[columns].unique())
            self.dicts = {columns: self.elements,
                             '60% Total': [], 
                             'Product Subtotal': [], 
                             '# of Order': [], 
                             'Quantity': [],
                             'Transaction Fee':[], 
                             'Grand Total':[],
                             'Total Estimated Shipping Fee':[]
                        } 
        
    def drop_duplicate_order_id(self, df):
        return df.drop_duplicates(subset='Order ID', keep='first')
    
    def dataSlicer(self):
        features = ['Order ID', 'Order Status', 'Year','Year_Month', 'Year_Week', 'Year_Month_Day',
                       'Parent SKU Reference No.', 'Product Name', 'Original Price', '60% Price', 
                       'Deal Price', 'Quantity', 'Product Subtotal', 'Seller Rebate',                       
                       'Seller Discount', 'Shopee Rebate', 'No of product in order', 'Seller Voucher',                    
                       'Seller Absorbed Coin Cashback', 'Shopee Voucher', 'Total Amount', 
                       'Buyer Paid Shipping Fee', 'Transaction Fee', 'Grand Total',
                       'Estimated Shipping Fee', 'Username (Buyer)']
        df = self.df.copy()
        df['Order Creation Date'] = pd.to_datetime(df['Order Creation Date'])
        df['60% Price'] = 0.6 * df['Original Price']*df.Quantity
        df['Year'] = df['Order Creation Date'].dt.strftime('%Y')
        df['Year_Month'] = df['Order Creation Date'].dt.strftime('%Y-%m')
        df['Year_Week'] = df['Order Creation Date'].dt.strftime('%Y-%U')
        df['Year_Month_Day'] = df['Order Creation Date'].dt.strftime('%Y-%m-%d')
        df = df[(df['Order Status'] != 'Cancelled') 
                & (df.Year_Month.notna())
                & (df.Year_Month != '2019-08')]
        return df[features].copy()

    def contructDataFrame(self):
        for element in self.elements:
            drop_dupl_df = self.drop_duplicate_order_id(self.df.copy())
            isMonth = self.df[self.columns].str.contains(element)
            dupl_isMonth = drop_dupl_df[self.columns].str.contains(element)

            self.dicts['60% Total'].append(self.df[isMonth]['60% Price'].sum())
            self.dicts['Product Subtotal'].append(self.df[isMonth]['Product Subtotal'].sum())
            self.dicts['# of Order'].append(int(drop_dupl_df[dupl_isMonth].Quantity.count()))
            self.dicts['Quantity'].append(int(self.df[isMonth].Quantity.sum()))
            self.dicts['Transaction Fee'].append(drop_dupl_df[dupl_isMonth]['Transaction Fee'].sum())
            self.dicts['Grand Total'].append(drop_dupl_df[dupl_isMonth]['Grand Total'].sum())
            self.dicts['Total Estimated Shipping Fee'].append(drop_dupl_df[dupl_isMonth]['Estimated Shipping Fee'].sum())

        return pd.DataFrame.from_dict(self.dicts)
    

class TablePlot(object):
    """
    Like Cursor but the crosshair snaps to the nearest x, y point.
    For simplicity, this assumes that *x* is sorted.
    """

    def __init__(self, df, element):
        self.df = df
        self.fig, self.ax = plt.subplots()
        self.x = df[element].values
        self.y1 = df['# of Order'].values
        self.y2 = df.Quantity.values
        self.y3 = df['Grand Total'].values
        self.y_revenue_lim = df['Grand Total'].max() + 20.0
        self.y_lim = df.Quantity.max() + 1.0
        #self.x_cord = np.arange(0, len(self.x)+1)
        #self.lx = self.ax.axhline(color='r', lw=0.1, ls="-")  # the horiz line
        #self.ly = self.ax.axvline(color='r', lw=0.1, ls="-")  # the vert line
        self.element = element
        # text location in axes coords
        #self.txt = self.ax.text(0.7, 0.9, '', transform=self.ax.transAxes)
    '''
    def mouse_move(self, event):
        if not event.inaxes:
            return

        x, y = event.xdata, event.ydata
        indx = min(np.searchsorted(self.x, x), len(self.x_cord) - 1)
        x = self.x[indx]
        y1 = self.y1[indx]
        #y2 = self.y2[indx]
        # update the line positions
        self.lx.set_ydata(y1)
        self.ly.set_xdata(x)

        self.txt.set_text('Revenue = RM{:.2f}'.format(y))
        print('Revenue = RM{:.2f}'.format(y))
        self.ax.figure.canvas.draw()
    '''    
    def order_plot(self):
        self.ax.plot(self.x, self.y1)
        self.ax.plot(self.x, self.y2)
        # show a legend on the plot
        self.ax.legend(["# of Order", "Qty"], loc='best')
        
        #self.fig.canvas.mpl_connect('motion_notify_event', self.mouse_move)
        
        self.fig.set_size_inches(10,5, forward=False)# label the figure
        self.ax.grid(linestyle="--", axis="y")
        
        # to make more honest, start they y axis at 0
        self.ax.set_ylim([0,self.y_lim])

        # Label the axes
        title_frac = self.element.replace("_","-")
        self.ax.set_xlabel('Dates: {}'.format(title_frac))
        self.ax.set_ylabel('Quantity')
             
        if self.element.split("_")[-1] == "Day":
            title_frac = "Dai"
        else:
            title_frac = self.element.split("_")[-1]
        self.ax.set_title('{}ly Product Order'.format(title_frac))

        if title_frac == "Week" or title_frac =="Dai":
            for tick in self.ax.get_xticklabels():
                tick.set_rotation(90)

        # save and display graph
        plt.savefig('{}ly_Order.png'.format(title_frac))
        
        #plt.show()

    def revenue_plot(self):
        self.ax.plot(self.x, self.y3)
        # show a legend on the plot
        self.ax.legend(["Revenue"], loc='best')
        
        #self.fig.canvas.mpl_connect('motion_notify_event', self.mouse_move)
        
        self.fig.set_size_inches(9,5, forward=False)# label the figure
        
        # Label the axes
        title_frac = self.element.replace("_","-")
        self.ax.set_xlabel('Dates: {}'.format(title_frac))
        self.ax.set_ylabel('Revenue (RM)')
                     
        if self.element.split("_")[-1] == "Day":
            title_frac = "Dai"
        else:
            title_frac = self.element.split("_")[-1]
        self.ax.set_title('{}ly Revenue'.format(title_frac))
        
        self.ax.grid(linestyle="--", axis="y")
        
        # to make more honest, start they y axis at 0
        self.ax.set_ylim([0,self.y_revenue_lim])
        if title_frac == "Week" or title_frac =="Dai":
            for tick in self.ax.get_xticklabels():
                tick.set_rotation(90)

        # save and display graph
        plt.savefig('{}ly_Revenue.png'.format(title_frac))

        #plt.show()
        
    def appendTotal(self):
        df = self.df.copy()
        df['NET PROFIT'] = df['Grand Total'] - df['Transaction Fee'] - df['60% Total']

        sum_df = df.sum()
        sum_df[self.element] = 'Overall Total'
        sum_df
        
        df = df.append(sum_df, ignore_index=True)
        
        if self.element == 'Year':
            return df.style.applymap(self.highlight_cols, subset=pd.IndexSlice[['NET PROFIT']])
        else:
            return df.style.apply(self.bold_max)
    
    def bold_max(self, x):
        return ['font-weight: bold' if v == x.iloc[-1] else ''
                    for v in x]

    def highlight_cols(self, x):
        color = 'orange'
        return 'background-color: %s' % color

    def currencyFormat(x):
        return "RM{:.2f}".format(x)





if __name__:
	parser = argparse.ArgumentParser()
	parser.add_argument('-f', "--filename", help='Excel filename in .xls or .xlsx')
	parser.add_argument('-o', "--output", help='Result Excel filename in .xls or .xlsx')
	args = parser.parse_args()
	filename = args.filename
	if args.output == None:
		output = "Report.xlsx"
	else:
		output = args.output 	 	

	df = pd.read_excel(filename)
	df.head()

	ct = constructTable(df, None) 
	filtered_df = ct.dataSlicer()

	year_data = constructTable(filtered_df, 'Year')
	year_table = year_data.contructDataFrame()
	year_table

	month_data = constructTable(filtered_df, 'Year_Month')
	month_table = month_data.contructDataFrame()
	month_table.tail()

	week_data = constructTable(filtered_df, 'Year_Week')
	week_table = week_data.contructDataFrame()
	week_table.tail()

	day_data = constructTable(filtered_df, 'Year_Month_Day')
	day_table = day_data.contructDataFrame()
	day_table.tail()

	annual = TablePlot(year_table, 'Year')
	annual.order_plot()
	annual.revenue_plot()
	year_table = annual.appendTotal()

	monthly = TablePlot(month_table, 'Year_Month')
	monthly.order_plot()
	monthly.revenue_plot()
	month_table = monthly.appendTotal()

	weekly = TablePlot(week_table, 'Year_Week')
	weekly.revenue_plot()
	week_table = weekly.appendTotal()
	weekly.order_plot()

	daily = TablePlot(day_table, 'Year_Month_Day')
	daily.order_plot()
	daily.revenue_plot()
	day_table = daily.appendTotal()

	with pd.ExcelWriter(output, engine='openpyxl') as writer:  
	    filtered_df.to_excel(writer, sheet_name='overall_data')
	    day_table.to_excel(writer, sheet_name='day_report')
	    week_table.to_excel(writer, sheet_name='week_report')
	    month_table.to_excel(writer, sheet_name='month_report')
	    year_table.to_excel(writer, sheet_name='year_report')
