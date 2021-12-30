import Fractal as f
from chaostech.Rule import *
import components
import transform_components as trc
import chaostech.MathTech as mtec

import dash
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
import dash_loading_spinners as dls
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import datashader as ds
import matplotlib.pyplot as plt
import plotly.express as px 
import plotly.graph_objects as go
import colorcet as cc
import pandas as pd
import numpy as np
from numba import njit

#HELPERS
def raw_figure(preset=None, poly=3, jump=0.5, N=10000, heap = None):
	if preset : pts = preset(N)
	else :
		T = np.array([jump, 0])
		vs = f.get_polygon(poly, 1, True)
		if not heap: heap = heap = f.no_rule()
		T = f.to_array(T, vs.shape[0])
		pts = f.getPointsV(vs, 0, 0, N, None, T, heap)

	poly = f.get_polygon(poly,1,True)
	pts = pd.DataFrame(pts[:,:2], columns = ['x','y'])
	pts["type"] = "iter"
	pts["size"] = ITER_PT_SIZE
	poly = pd.DataFrame(poly, columns = ['x','y'])
	poly["type"] = "poly"
	poly["size"] = POLY_PT_SIZE
	pts = pts.append(poly)
	fig = px.scatter(pts,'x','y',color="type",size = "size", template = 'plotly_dark',color_discrete_sequence=px.colors.qualitative.Set3)
	fig.update_traces(marker=dict(opacity = 1, line=dict(width=1, color='DarkSlateGray')))
	fig.update_xaxes(showgrid=False,zeroline=False,visible=False)
	fig.update_yaxes(showgrid=False,zeroline=False,visible=False)
	fig.update_layout(showlegend = False)
	return fig

def update_fig(p):
	if not p["fig_json"]: return raw_figure(f.sierpc)

	oldfig = go.Figure(p["fig_json"])
	T = np.array([p["jump"], 0])
	vs = f.get_polygon(p["poly"], 1, True)
	if p["midpoints"] : vs = f.stack_midpoints(vs)
	if p["center"] : vs = f.stack_center(vs)
	T = f.to_array(T, vs.shape[0])
	heap = Rule(p["ln"],p["offset"],p["sym"])

	pts = f.getPointsV(vs, 0, 0, p["N"], None, T, heap)
	pts = pd.DataFrame(pts[:,:2],columns = ['x','y'])
	pts["type"] = "iter"
	pts["size"] = ITER_PT_SIZE
	vs = pd.DataFrame(vs, columns = ['x','y'])
	vs["type"] = "poly"
	vs["size"] = POLY_PT_SIZE
	oldfig['data'][0]['marker']["size"]=pts["size"]
	oldfig['data'][0]['x']=pts['x']
	oldfig['data'][0]['y']=pts['y']
	oldfig['data'][1]['marker']["size"]=vs["size"]
	oldfig['data'][1]['x']=vs['x']
	oldfig['data'][1]['y']=vs['y']

	return oldfig

def iterations_callback(p):
	N = p["N"]
	T = np.array([p["jump"], 0])
	vs = f.get_polygon(p["poly"], 1, True)
	if p["midpoints"] : vs = f.stack_midpoints(vs)
	if p["center"] : vs = f.stack_center(vs)
	heap = Rule(p["ln"],p["offset"],p["sym"])
	T = f.to_array(T, vs.shape[0])
	oldfig = go.Figure(p["fig_json"])
	sizeT = oldfig['data'][0]['marker']['size']
	xT = oldfig['data'][0]['x']
	yT = oldfig['data'][0]['y']
	oldN = len(sizeT)
	if oldN < N : # when iterations are higher than last value 
		x0 = oldfig['data'][0]['x'][oldN-1]
		y0 = oldfig['data'][0]['y'][oldN-1]
		N = N-oldN
		pts = f.getPointsV(vs, x0, y0, N+1, None, T, heap)
		pts = pd.DataFrame(pts[:,:2],columns = ['x','y'])
		pts["type"] = "iter"
		pts["size"] = ITER_PT_SIZE
		#append new iterations to old ones
		sizeT = list(sizeT) + list(pts['size'][1:])
		xT = list(xT) + list(pts['x'][1:])
		yT = list(yT) + list(pts['y'][1:])
		oldfig['data'][0]['marker']['size'] = tuple(sizeT)
		oldfig['data'][0]['x'] = tuple(xT)
		oldfig['data'][0]['y'] = tuple(yT)
	elif 0<=oldN-N<5: # when iterations are equal or a bunch (5) less than last value
		newsize = list(sizeT)[:N]
		newx = list(xT)[:N]
		newy = list(yT)[:N]
		oldfig['data'][0]['marker']["size"] = tuple(newsize)
		oldfig['data'][0]['x'] = tuple(newx)
		oldfig['data'][0]['y'] = tuple(newy)
	else: # when iterations are less 
		oldfig = raw_figure(poly=p["poly"],jump=p["jump"],N=N,heap=heap)
	return oldfig

#VARIABLES
default_params = {"poly": 3, "N": 10000, "ln": 0, "sym": False, "offset": 0, "jump": "1/2", "midpoints": False, "center": False, "fig_json":None }

sierpt = default_params.copy()
sierpc = default_params.copy()
sierpc["midpoints"] = True
sierpc["jump"] = "2/3"
sierpc["poly"] = 4
vicsek = sierpc.copy()
vicsek["midpoints"] = False
vicsek["center"] = True
tsquare = default_params.copy()
tsquare["offset"]=2
tsquare["ln"]=1
tsquare["poly"]=4
techs = default_params.copy()
techs["poly"]=4
techs["ln"]=1
webs = default_params.copy() # THIS DOESN'T WORK YET MISSING ROTATION
webs["poly"]=4
webs["offset"] = -1
webs["ln"]=2
webs["symmetry"]=True
XTREME = default_params.copy()
XTREME["N"] = 200000
XTREME["poly"] = 200
XTREME["jump"] = "7/8"
XTREME["center"] = True
presets = {"sierpt": sierpt, "sierpc":sierpc, "vicsek":vicsek,"tsquare": tsquare, "techs": techs, "webs": webs, "XTREME": XTREME}

theme_color = '#232325'
text_color = '#ffdf80'
ITER_PT_SIZE = 0.1
POLY_PT_SIZE = 2.5

#MAIN COMPONENTS
tabs = dbc.Tabs(className = "tabs", children=[dbc.Tab(components.tab1, className = "tab", label="Chaos Game"),
												dbc.Tab(trc.tab2, className="tab", label="Transformations")])
header = html.Div(
	className = 'elements',
	children = [html.H1("FRACTAL GENERATOR", className = "title"),tabs]
		)

#APP INIT
app = dash.Dash(__name__,external_stylesheets=[dbc.themes.SUPERHERO])
app.layout = dbc.Spinner(children = [html.Div(children = [header])], delay_show = 1000, size='md',fullscreen=False)

server = app.server

#CALLBACKS
@app.callback(Output('GRAPH','figure'),
	Input('polygon_input', 'value'),
	Input('jump_input','invalid'),
	Input('iterations_input','value'),
	Input('length_input','value'),
	Input('offset_input', 'invalid'),
	Input('symmetry_input', 'value'),
	Input('midpoints_input', 'value'),
	Input('center_input','value'),
	State('offset_input','value'),
	State('jump_input','value'),
	State('GRAPH','figure'))
def update_graph(poly, inval_jump, N, ln, inval_offset, sym, midpoints, center,offset, jump,  fig_json):
	if fig_json == None : return raw_figure(f.sierpt)
	if inval_offset or inval_jump or jump == None or poly == None or N == None or ln == None: return fig_json
	jump = eval(jump)
	params = {"poly": poly, "N": N, "ln": ln, "sym": sym, "offset": offset, "jump": jump, "midpoints": midpoints, "center": center, "fig_json":fig_json }
	ctx = dash.callback_context
	trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
	if trigger_id == "iterations_input": return iterations_callback(params)
	else : return update_fig(params) 

#CHECK VALIDITY OF JUMP INPUT
@app.callback(Output('jump_input','invalid'),
	Input('jump_input','value'))
def jump_validate(jump):
	if jump == None: return True
	try : jump = eval(jump)
	except SyntaxError : return True #IF IT DOESN'T EVALUATE -> INVALID
	if 0 > jump: return True #IF NEGATIVE -> INVALID
	return False

#CHECK VALIDITY OF OFFSET
@app.callback(Output('offset_input','invalid'),
	Input('offset_input', 'value'),
	Input('symmetry_input', 'value'),
	Input('polygon_input','value'))
def length_validate(offset, sym, poly):
	if offset == None: return True
	if sym : return abs(offset) > poly/2 
	else : return abs(offset) > poly

@app.callback(	
	Output('polygon_input', 'value'),
	Output('jump_input','value'),
	Output('iterations_input','value'),
	Output('length_input','value'),
	Output('offset_input', 'value'),
	Output('symmetry_input', 'value'),
	Output('midpoints_input', 'value'),
	Output('center_input','value'),
	Input('presets_dropdown','value'),
	State('polygon_input', 'value'),
	State('jump_input','value'),
	State('iterations_input','value'),
	State('length_input','value'),
	State('offset_input', 'value'),
	State('symmetry_input', 'value'),
	State('midpoints_input', 'value'),
	State('center_input','value'))
def update_presets(value, poly, jump, N, ln, offset, sym, midpoints, center):
	if value == None: return poly, jump, N, ln, offset, sym, midpoints, center
	preset = presets[value]
	return preset["poly"],preset["jump"],preset["N"],preset["ln"],preset["offset"],preset["sym"],preset["midpoints"],preset["center"]




#TRANSFORM CALLBACKS:

@app.callback(
	Output('args-txt', 'value'),
	Output('probs-txt', 'value'),
	Output('parse-type', 'value'),
	Input('presets-dropdown', 'value')
	)
def load_preset(value):
	if value == 'MB_LIKE':
		return trc.MB_LIKE, trc.MB_LIKE_PROBS, 'regular'
	elif value == 'SPIRAL':
		return trc.SPIRAL, trc.SPIRAL_PROBS, 'borke'
	elif value == 'DRAGON':
		return trc.DRAGON, trc.DRAGON_PROBS, 'borke'
	elif value == 'XMAS':
		return trc.XMAS, trc.XMAS_PROBS, 'borke'
	elif value == 'FERN':
		return trc.FERN, trc.FERN_PROBS, 'borke'
	elif value == 'LEAF':
		return trc.LEAF, trc.LEAF_PROBS, 'borke'
	elif value == 'SIERPT':
		return trc.SIERPT, trc.SIERPT_PROBS, 'regular'
	else:
		raise PreventUpdate


@app.callback(Output('GRAPH2', 'figure'),
	Input('plot-button', 'n_clicks'),
	State('args-txt', 'value'),
	State('probs-txt', 'value'),
	State('parse-type', 'value'),
	State('iters', 'value'),
	State('color-dropdown', 'value'))
def draw_ifs(_, args, probs, parse, N, color):
	if args == None or probs == None:
		raise PreventUpdate

	params = np.array(trc.read_args_from_string(args))
	probs = trc.read_probs_from_string(probs)

	chooser = njit(lambda _: mtec.random_choice_fix(len(params), probs))
	selector = njit(lambda a,i: a[i])
	iterator = njit(lambda x: x)

	if parse == 'regular':
		@njit
		def jump(args, x, y, z):
			a,b,c,d,e,f = args
			x_ = a*x + b*y + c
			y_ = d*x + e*y + f
			return np.array([x_,y_,z])
	elif parse == 'borke':
		@njit
		def jump(args, x, y, z):
			a,b,c,d,e,f = args
			x_ = a*x + b*y + e
			y_ = c*x + d*y + f
			return np.array([x_,y_,z])
	else:
		raise PreventUpdate

	if color != None:
		cmap = eval(color)
	else:
		cmap = cc.fire

	p0 = np.array([0.,0.,0.])
	N = N * 1000

	pts = f.getPointsAdv(N, p0, jump, params, chooser, 
		selector, iterator, probs)

	df = pd.DataFrame(data=pts[:,:2], columns=["x", "y"])
	xbounds = (pts[:, 0].min()-0.2, pts[:, 0].max()+0.2)
	ybounds = (pts[:, 1].min()-0.2, pts[:, 1].max()+0.2)
	cvs = ds.Canvas(plot_width=1500, plot_height=1500, 
			x_range=xbounds, y_range=ybounds)
	agg = cvs.points(df, 'x', 'y')
	img = ds.tf.set_background(ds.tf.shade(agg, how="log", cmap=cmap), 
			"black").to_pil()
	fig = px.imshow(img)
	fig.update_layout(paper_bgcolor='rgb(0,0,0)',plot_bgcolor='rgb(0,0,0)')
	fig.update_xaxes(showticklabels=False)
	fig.update_yaxes(showticklabels=False)
	return fig




if __name__ == '__main__':
    app.run_server(debug=True)




