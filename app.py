import dash
from dash import Dash, dash_table, html, dcc
from dash.dependencies import Input,Output
import pandas as pd
import os
from random import randint
import flask
import spacy
from spacy.displacy.render import DEFAULT_LABEL_COLORS

from brain import get_article, get_replies

def entname(name):
	return html.Span(name, style={
		"font-size": "0.4em",
		"font-weight": "bold",
		"line-height": "1",
		"border-radius": "0.35em",
		"text-transform": "uppercase",
		"vertical-align": "middle",
		"margin-left": "0.25rem"
	})


def entbox(children, color):
	return html.Mark(children, style={
		"background": color,
		"padding": "0.225em 0.3em",
		"margin": "0 0.125em",
		"border-radius": "0.35em",
	})


def entity(children, name):
	if type(children) is str:
		children = [children]

	children.append(entname(name))
	color = DEFAULT_LABEL_COLORS[name]
	return entbox(children, color)

def render(doc):
	children = []
	last_idx = 0
	for ent in doc.ents:
		children.append(doc.text[last_idx:ent.start_char])
		children.append(
			entity(doc.text[ent.start_char:ent.end_char], ent.label_))
		last_idx = ent.end_char
	children.append(doc.text[last_idx:])
	return children

latest_tweets = pd.read_csv('latest_tweets.csv')
twitter_profiles = pd.read_csv('twitter_profiles.csv')

server = flask.Flask(__name__)
server.secret_key = os.environ.get('secret_key', str(randint(0, 1000000)))
app = dash.Dash(__name__, server=server,
	suppress_callback_exceptions=True)

app.title = "SaltWire Social Monitor"

tbl = html.Div([
	dash_table.DataTable(
		id="datatable-interactivity",
		data=latest_tweets.to_dict('records'), 
		columns=[{"name": i, "id": i} for i in latest_tweets.columns],
		page_action="native",
		page_size=10,
		page_current=0,
		row_selectable="single",
		selected_rows=[0],
		hidden_columns=['username', 'retweet_count', 'reply_count', 'like_count', 'quote_count',
		'url', 'created_at', 'id', 'conversation_id'],
		style_header={
			# 'backgroundColor': 'rgb(30, 30, 30)',
			# 'color': 'white',
			# 'textAlign':'center',
			# 'fontSize': '1em',
			'display':'none'
		},
		style_data={
			'backgroundColor': 'rgb(50, 50, 50)',
			'color': 'white',
			'whiteSpace': 'normal',
			'height': 'auto',
		},
		style_table={
			'overflowX':'auto',
			'width':'100%',
		},
		style_cell={
			'fontSize': '1em',
			'textAlign':'left',
			'overflow':'hidden',
			'textOverflow': 'ellipsis',
			'padding':'8px'
		},
	),
])

app.layout = html.Div(
	children=[
		dcc.Store(id='selected'),
		dcc.Location(id='url',refresh=True),
		html.Div(
			className="row",
			children=[
				# Column for user controls
				html.Div(
					className="four columns div-user-controls",
					children=[
						html.A(
							html.Img(
								className="logo",
								src=app.get_asset_url("logo.svg"),
							),
							href="https://saltwire.com",
						),
						html.Div([
							html.H3("Social Media Monitoring",style={'margin':0}),
							html.H5("Select a Twitter handle to filter tweets by publication."),
							html.Br(),
						]),
						html.Div(
							className="row",
							children=[
								html.Div(
									className="div-for-dropdown",
									children=[
										dcc.Dropdown(
											id="handle-dropdown",
											options=[
												{'label': '@chronicleherald', 'value': 'chronicleherald'},
												{'label': '@capebretonpost', 'value': 'capebretonpost'},
												{'label': '@StJohnsTelegram', 'value': 'StJohnsTelegram'},
												{'label': '@PEIGuardian', 'value': 'PEIGuardian'},
												{'label': '@KingsNSnews', 'value': 'KingsNSnews'},
												{'label': '@Casket_News', 'value': 'Casket_News'},
												{'label': '@SSBreaker', 'value': 'SSBreaker'},
												{'label': '@trurodaily', 'value': 'trurodaily'},
												{'label': '@TC_Vanguard', 'value': 'TC_Vanguard'},
												{'label': '@JournalPEI', 'value': 'JournalPEI'},
												{'label': '@SaltWireNetwork', 'value': 'SaltWireNetwork'},
												{'label': '@SaltWireToday', 'value': 'SaltWireToday'}
											],
											placeholder="All",
										)
									],style={'padding':'0px 20px 20px'}
								),
							],
						),
						html.Div(id="handle",children=[]),
						tbl,
					],
				),
				# Column for app graphs and plots
				html.Div(
					id='fig',
					className="eight columns div-for-charts bg-grey",
					style={'padding':'20px'},
				),
			],
		)
	]
)

@app.callback(
	Output("datatable-interactivity", "data"),
	[Input("handle-dropdown", "value")],
)
def update_recent_tweets(handle_dropdown):
	if handle_dropdown:
		df = latest_tweets[latest_tweets['username']==handle_dropdown]
	else:
		df = latest_tweets
	return df.to_dict('records')

@app.callback(
	Output('fig', "children"),
	Input('datatable-interactivity',"data"),
	Input('datatable-interactivity', "derived_virtual_data"),
	Input('datatable-interactivity', "derived_virtual_selected_rows"),
)
def update_fig(data, rows, derived_virtual_selected_rows):
	"""
	latest_tweets keys = ['username', 'retweet_count', 
	'reply_count', 'like_count', 'quote_count',
	'url', 'text', 'created_at', 'id', 'conversation_id']
	"""
	#twitter
	derived_virtual_selected_rows if len(derived_virtual_selected_rows) != 0 else [0]
	dff = pd.DataFrame(data)
	row = dff.iloc[derived_virtual_selected_rows[0]]
	twitter_stats = row.to_dict()
	print(twitter_stats)
	metrics_keys = ['retweet_count','reply_count','like_count','quote_count']
	twitter_metrics = " | ".join([f"{i}: {twitter_stats[i]}" for i in metrics_keys])
	url = row['url'].split("/?")[0]
	replies = pd.DataFrame(get_replies(twitter_stats['conversation_id']))
	print("REPLIES",twitter_stats['conversation_id'],replies)
	metrics = html.Div(id='metrics',children=[
		html.Div(id='twitter',className="six columns", children=[
			html.H2("Twitter"),
			html.P(twitter_metrics),
			html.A(f"@{twitter_stats['username']}: {row['text']}",href=row['url']),
			html.Br(),
			dash_table.DataTable(
				data=replies.to_dict('records'),
				hidden_columns=[i for i in replies.columns if i != 'text'],
				style_header={
					'backgroundColor': 'rgb(30, 30, 30)',
					'color': 'white',
					'textAlign':'center',
					'fontSize': '1em',
				},
				style_data={
					'backgroundColor': 'rgb(50, 50, 50)',
					'color': 'white',
					'whiteSpace': 'normal',
					'height': 'auto',
				},
				style_table={
					'overflowX':'auto',
					'width':'100%',
				},
				style_cell={
					'fontSize': '1em',
					'textAlign':'left',
					'overflow':'hidden',
					'textOverflow': 'ellipsis',
					'padding':'8px'
				},
			)
		]),
		html.Div(id='google',className="six columns", children=[
			html.H2("Google"),
		])
	])
	
	#article
	article_object = get_article(url)
	nlp = spacy.load("en_core_web_sm")
	doc = nlp(article_object['body'])
	article = html.Div(id='article',children=[
		html.H1(article_object['title']),
		html.P(f"Author: {article_object['byline']} | Date posted: {article_object['posted']}"),
		html.Br(),
		html.P(render(doc)),
	])
	return html.Div([article,metrics],style={"height":"100vh"})

if __name__ == '__main__':
	app.server.run(debug=True, threaded=True)