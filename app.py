import json

import pandas as pd

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_leaflet.express as dlx
import dash_leaflet as dl
import dash_bootstrap_components as dbc

import plotly.express as px

from dash.dependencies import Input, Output, State
from dash_extensions import Download
from dash_extensions.snippets import send_data_frame
from dash_extensions.javascript import Namespace
from dash_extensions.javascript import assign

import dash_table

import fdb as fdb #conexion firebird

# app initialize
app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)
server = app.server
app.config["suppress_callback_exceptions"] = True
app.config["prevent_initial_callbacks"] = True
# mapbox
mapbox_access_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNrOWJqb2F4djBnMjEzbG50amg0dnJieG4ifQ.Zme1-Uzoi75IaFbieBDl3A"


#------------------------------#Connect Data base-----------------------------------


dsn='170.247.0.41:/usr/bases/CEMBD.FDB' ##si esta desde internet cambie la  ip a 170.247.0.41-172.16.255.4
user="CORALG"
pswr="coralsge#2021"
con=fdb.connect(dsn=dsn, user=user, password=pswr, charset='UTF8')
cursor=con.cursor();

##-------------------------------------# Functions to consult DB---------------------------
def options_CATV(con):
    #CONSULTA PARA OBTENER LOS CODIGOS DE LAS CATVS
    sql="""SELECT DISTINCT
    L.CODIG_SUSCR
    FROM LUMINARIA L 
    INNER JOIN CARACTESTICA_LUMINARIA TL
        ON L.CODIG_TECNO=TL.CODIG_CARAC
    WHERE CODIG_SUSCR IS NOT NULL
    AND TL.DESCRIPCION='CATV'"""
    df=pd.read_sql_query(sql,con)
    return df

def options_tecnologia(con):
    #CONSULTA PARA OBTENER LOS TIPOS DE TECNOLOGIA SUBIDOS EN LA TABLA PRINCIPAL
    sql="""SELECT DISTINCT
    TL.DESCRIPCION as TECNOLOGIA
    FROM LUMINARIA L 
    INNER JOIN CARACTESTICA_LUMINARIA TL
        ON L.CODIG_TECNO=TL.CODIG_CARAC
    """
    df= pd.read_sql_query(sql,con)
    return df

def options_municipios(con,tecno):
    ##Consulta de municipios segun tipo de tecnologia

    sql=f"""SELECT DISTINCT
    L.DIVIS_POLIT, M.DESCRIPCION AS MUNICIPIO
    FROM LUMINARIA L 
    INNER JOIN CARACTESTICA_LUMINARIA TL
        ON L.CODIG_TECNO=TL.CODIG_CARAC
    INNER JOIN DIVISION_POLITICA M
        ON L.DIVIS_POLIT=M.CODIG_DIVIS    
    WHERE TL.DESCRIPCION in {tecno}
    """ 
    sql=sql.replace("[","(").replace("]",")")

    return pd.read_sql_query(sql,con).values.tolist() ## En la ultima fila se modifica los tipos de tecnologia

def consulta_catv(con,cods):
    sql=f"""SELECT
    L.*,TL.DESCRIPCION AS TECNOLOGIA, M.DESCRIPCION AS MUNICIPIO
    FROM LUMINARIA L 
    INNER JOIN CARACTESTICA_LUMINARIA TL
        ON L.CODIG_TECNO=TL.CODIG_CARAC
    INNER JOIN DIVISION_POLITICA M
        ON L.DIVIS_POLIT=M.CODIG_DIVIS    
    WHERE L.CODIG_SUSCR IN {cods}
    AND TL.DESCRIPCION='CATV'"""
    sql=sql.replace("[","(").replace("]",")")
    df=pd.read_sql_query(sql,con)
    df.CODIG_SUSCR=df.CODIG_SUSCR.apply(lambda x: str(x))
    df.rename(columns={"LATITUD_DEC":"lat","LONGITU_DEC":"lon","POTENCIA_WT":"W"},inplace=True)
    df.fillna(0,inplace=True)
    return df

def consulta_tecno_munci(con,tecno,mun):
    sql=f"""SELECT
    L.*,TL.DESCRIPCION AS TECNOLOGIA, M.DESCRIPCION AS MUNICIPIO
    FROM LUMINARIA L 
    INNER JOIN CARACTESTICA_LUMINARIA TL
        ON L.CODIG_TECNO=TL.CODIG_CARAC
    INNER JOIN DIVISION_POLITICA M
        ON L.DIVIS_POLIT=M.CODIG_DIVIS    
    WHERE TL.DESCRIPCION IN {tecno}
    AND L.DIVIS_POLIT='{mun}' """
    sql=sql.replace("[","(").replace("]",")")
    df=pd.read_sql_query(sql,con)
    df.CODIG_SUSCR=df.CODIG_SUSCR.apply(lambda x: str(x))
    df.rename(columns={"LATITUD_DEC":"lat","LONGITU_DEC":"lon","POTENCIA_WT":"W"},inplace=True)
    df.fillna(0,inplace=True)
    return df

def opciones_all_municipios(con):
    sql="""select * 
    from DIVISION_POLITICA
    WHERE PADRE_DIVIS='52';"""
    return pd.read_sql_query(sql,con)[['CODIG_DIVIS','DESCRIPCION']].values.tolist()

#-------------------------OTHER FUNCTIONS-----------------------------------
def build_banner():
    return html.Div(
        id="banner",
        className="banner",
        children=[
            html.Img(src=app.get_asset_url("logocorregido.png")),
            html.H6("Mapas interactivos cargas especiales"),
        ],
    )


def build_graph_title(title):
    return html.P(className="graph-title", children=title)


#adapting data to geojson format
def get_data(con,cods=None,tecno=None,mun=None):
    
    #df_cod = df[df["CODIG_SUSCR"].isin(cod)]  # pick one cod
    if cods is not None:
        df_cod = consulta_catv(con,cods)
    elif tecno is not None and mun is not None:
        df_cod = consulta_tecno_munci(con,tecno,mun)
    df_cod = df_cod[['lat', 'lon', 'ID_LUMINARIA', 'W', 'MUNICIPIO','CODIG_SUSCR','DIVIS_POLIT','TRANSFORMAD']]  # drop irrelevant columns
    dicts = df_cod.to_dict('rows')
    for item in dicts:
        item["popup"] = """<b>Informacions CATV</b>
                             <br>Codigo usuario: {}
                             <br>ID equipo: {}
                             <br>Transformador: {}
                             <br>Potencia: {} w
                             <br>Municipio: {}""".format(item["CODIG_SUSCR"],item["ID_LUMINARIA"],item["TRANSFORMAD"],item["W"],item["MUNICIPIO"])  # bind tooltip
        item["tooltip"] = "ID "+str(item["ID_LUMINARIA"])  # bind popup
    geojson = dlx.dicts_to_geojson(dicts)  # convert to geojson
    
    geobuf = dlx.geojson_to_geobuf(geojson)  # convert to geobuf
    return geojson

# # Load data
# ##Prepare the data
# df=pd.read_excel("geo_info.xlsx")
# df.CODIG_SUSCR=df.CODIG_SUSCR.apply(lambda x: str(x))
# df.rename(columns={"LATITUD_DEC":"lat","LONGITU_DEC":"lon"},inplace=True)
# df.fillna(0,inplace=True)
# color_prop = 'CODIG_SUSCR'
# df_plotly=df.copy()



#----------------------------------#DROP DOWNS--------------------------
# Setup  options to to choose what to show in the map.

df_cods=options_CATV(con)
cods=df_cods.values.tolist() #Iterable for list
cod_options=[dict(label=str(x),value=json.dumps(x)) for x in cods]
cod_options+=[dict(label="Todos",value=json.dumps(df_cods.CODIG_SUSCR.unique().tolist()))]

#Setup option for Municipios
municipios_all=opciones_all_municipios(con)
mun_all_options=[dict(label=x[1],value=x[0]) for x in municipios_all]

#Setup option for tecnologia

df_tec=options_tecnologia(con)
arra=df_tec.TECNOLOGIA.unique()
tec=df_tec.values.tolist() #Iterable for list
tec_options=[dict(label=str(x),value=json.dumps(x)) for x in tec]
tec_options+=[dict(label="Todos excepto CATV",value=json.dumps([x for x in arra if x!="CATV"]))]

#Setup option for the table
table_options=[dict(label='Toda la informacion',value='All')]
table_options+=[dict(label='Resumen de informacion',value='Summary')]

table_agg_options=['IDENTIFICACION','MUNICIPIO','TRANSFORMADOR']
table_agg_options=[dict(label=x,value=x) for x in table_agg_options]

#Drop downs to choose code
dd_tec = dcc.Dropdown(options=tec_options, id="dd_tec", clearable=False, value=json.dumps(["CATV"]))
dd_tec_plotly = dcc.Dropdown(options=tec_options, id="dd_tec_plotly", clearable=False, value=json.dumps(["CATV"]))

##Drop downs to choose tecnology
dd_cod = dcc.Dropdown(options=cod_options, id="dd_cod", clearable=False, value=json.dumps(cods[0]))
dd_cod_plotly = dcc.Dropdown(options=cod_options, id="dd_cod_plotly", clearable=False, value=json.dumps(cods[0]))

##Drop down to choose municipio
dd_mun_all = dcc.Dropdown(options=mun_all_options, id="dd_mun_all", clearable=False)


##Drop down for the table
dd_table_agg=dcc.Dropdown(options=table_agg_options, id="dd_table_agg", clearable=False, value='IDENTIFICACION',multi=True)
dd_table_info=dcc.Dropdown(options=table_options, id="dd_table_info", clearable=False, value='All')
##

#----------------------------#Inputs to edit data-------------------------
edit_layout = html.Div([

            html.Div(id="titulo-edit" ),

            html.Table([                
                html.Tr(["Potencia (w): ",
                  dcc.Input(id='potencia-input', type='number')]),
                html.Tr(["Latitud: ",
                  dcc.Input(id='latitud-input', type='number')]),
                html.Tr(["Longitud: ",
                  dcc.Input(id='longitud-input', type='number')]),
                html.Tr(["Transformador: ",
                  dcc.Input(id='transformador-input', type='text')]),
                html.Tr(["Municipio: ",
                  dd_mun_all]),
                html.Tr(["Codigo Interno: ",
                  dcc.Input(id='codigoin-input', type='number')]),
            ]),
])

#--------------------------------##TABLE-------------------------------
TABLE=dash_table.DataTable(
    id='table',
    columns=[],
    data=[],
    page_size=6,
    filter_action='native',
    style_cell={
        'minWidth': 95, 'maxWidth': 250, 'width': 95, 'textAlign': 'left',
        'border': '1px solid black' 
    },
    style_data_conditional=[
        {
            'if': {'row_index': 'odd'},
            'backgroundColor': 'rgb(248, 248, 248)'
        }
    ],
    style_header={
        'backgroundColor': 'rgb(230, 230, 230)',
        'fontWeight': 'bold',
        'border': '1px solid black' 
    }
    )

##table layout
Table_layout = html.Div([
            build_graph_title("Informacion de los puntos seleccionados"),
            html.Div(id="Tabla-titulo" ),

            html.Table([                
                html.Tr(["Seleccione Tipo de tabla: ",
                         dd_table_info]),
                html.Tr(["Agrupacion(Tabla resumida): ",
                         dd_table_agg], id="html-tabla-resumida",style={"display":"none"}),
                html.Tr([]),
                html.Tr([TABLE]),
                html.Tr([html.Button(id='Download_Table', n_clicks=0, children='Download_Table',
                                     style={"display":"none"}),
                      Download(id="download")]),
            ]),
])



#----------------------------------------#ALERT----------------------------------------------

Alert=dbc.Alert(children="no_return",
                id="alert-fade",
                is_open=True,
                color="white",
                duration=2000,)


                #----------------------### MAPS and LAYOUTS ###-------------------------
## Create geojson.

draw_flag = assign("""function(feature, latlng){var flag = L.icon({iconUrl: '/assets/pin.png', iconSize: [48, 48]});return L.marker(latlng, {icon: flag});}""")
geojson = dl.GeoJSON(data=get_data(con, cods[0]), id="geojson",options=dict(pointToLayer=draw_flag), #format="geobuf",
                     zoomToBounds=True,  # when true, zooms to bounds when data changes
                     zoomToBoundsOnClick=True,  # when true, zooms to bounds of feature (e.g. cluster) on click
                     )


# Map Layers for geojson
# Cool, dark tiles by Stadia Maps.
url = 'https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png'
attribution = '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> '
black=dl.BaseLayer(dl.TileLayer(url=url, maxZoom=20, attribution=attribution),name="Oscuro")
default=dl.BaseLayer(dl.TileLayer(),name="Predeterminado",checked=True)

##Layouts page content
geo_layout = html.Div([
            html.H1(className="graph-title", children="Mapa Interactivo"),
            dl.Map([dl.LayersControl([default,black]), geojson, 
                    dl.LocateControl(options={'locateOptions': {'enableHighAccuracy': True}}),
                    dl.LayerGroup(id="layer")],
                   id="map",),

            html.Div([dd_tec,dd_cod],style={"position": "relative", "bottom": "80px", "left": "10px", "z-index": "1000", "width": "200px"}),
        ], style={'width': '80%', 'height': '80vh', 'margin': "auto", "display": "block", "position": "relative",'padding-bottom': '50px'})

info_geo_layout=html.Div([
                    
                    build_graph_title("Opciones: "),
                    html.Br(),
                    html.Button(id='edit-button', n_clicks=0, children='Editar_punto',),
                    html.Br(),
                    html.Div(id='edit-content'),
                    html.Div(id='features',children=edit_layout,style={'display':'none'},),
                    html.Div(id="botones-editar",children=[
                        html.Button(id='aceptar-edit-button', n_clicks=0, children='Aceptar'),
                        html.Button(id='cancel-edit-button', n_clicks=0, children='Cancelar')
                              ],style={'display':'none','padding-right': '20px','padding-left': '20px'}
                             ,)
            ])


##Create the plotly fig
fig = px.scatter_mapbox(consulta_catv(con,cods[0]), lat="lat", lon="lon", hover_name="CODIG_SUSCR", hover_data=["MUNICIPIO","ID_LUMINARIA","W","TRANSFORMAD"],
                        color="CODIG_SUSCR", zoom=10, height=600)

fig.update_layout(mapbox_style="dark", mapbox_accesstoken="pk.eyJ1IjoiZ2Fib2NjOTUiLCJhIjoiY2tsd3BybmN3MDFtcDJ2azJoNzdzZWcwbiJ9.OEu_jCUAe3_UhAe17RXPcA")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.update_layout(clickmode='event+select')

##Layouts page content
plotly_layout=html.Div([
            html.H1(className="graph-title", children="Mapa para Analisis"),
            dcc.Graph(id="plotly_fig",figure=fig,className='card'),
            html.Div([dd_tec_plotly,dd_cod_plotly],style={"position": "relative", "bottom": "80px", "left": "10px", "z-index": "1000", "width": "200px"}),
            ],className='wrapper')



#---------------------------#HTLM STRUCTURE#-----------------------------------------


app.layout = html.Div(
    children=[
        html.Div(
            id="top-row",
            children=[
                html.Div(
                    className="row",
                    id="top-row-header",
                    children=[
                        html.Div(
                            id="header-container",
                            children=[
                                build_banner(),
                                build_graph_title("Seleccione tipo de mapa"),
                                html.Div([
                                    html.Button(id='plotly-button', n_clicks=0, children='MAPA_ANALISIS',className='button',style={'color': 'black'}),
                                    html.Button(id='Geojson-button', n_clicks=0, children='MAPA_INTERACTIVO',className='button',style={'color': 'black'}),
                                    ]
                                    
                                ),
                                html.P(
                                    id="instructions",
                                    children=[
                                    html.Div("Bienvenido al aplicativo desarrollado para la visualizacion de "
                                    "la informacion que se encuentra subida al aplicativo SINAP. "
                                    "A continuacion seleccione uno de los dos mapas:  "),
                                    html.Div("1- Mapa interactivo: Permite ver en tiempo real los equipos elementos "
                                    "subidos en la base de datos ademas de la posicion actual del usuario, separandolos por tipo de tecnologia, codigo usuario "
                                    "y municipio. Ademas permite editar la informacion de manera individual  "
                                    ),
                                    html.Div("2- Mapa de analisis: Permite visualizar de manera rapida y clara "
                                    "los elementos subidos en SINAP, ademas entrega una tabla segun la informacion "
                                    "que se seleccione del mapa. Para seleccionar informacion del mapa, utilice la herramienta "
                                    "Box-select o Lasso-select ubicadas en la parte superior derecha del mapa, "
                                    "o inlcuso con SHIFT sostenido se puede hacer click sobre los elementos deseados.")]
                                    ,style={'text-align': 'justify'}
                                ),
                                
                            ],
                        )
                    ],
                ),
                html.Div(
                    className="row",
                    id="top-row-graphs",
                    children=[
                        # Well map
                        html.Div(
                            id="well-map-container",
                            children=[
                                 build_graph_title("Mapa"),
                                 Alert,
                                 html.Div(id='page-content',
                                          children=[geo_layout]
                                 )
                            ],
                        ),
                        html.Div(
                            id="info-container",
                            children=[
                                 
                                 html.Div(id='page-content-info'
                                          ,children=[info_geo_layout]
                                 )
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            className="row",
            id="table-contenido",
            children=[
                # Formation bar plots
                html.Div(
                    id="form-bar-container",
                    className="six columns",
                    children=[
                        
                        Table_layout,
                    ],
                ),
                html.Div(
                    # Selected well productions
                    id="well-production-container",
                    className="six columns",
                    children=[
                        build_graph_title("Grafica"),
                        html.Div(children=[dcc.Graph(id="grafica-potencia")])
                    ],
                ),
            ]
        , style={"display":"none"}),
        html.Div(
            
            id="bottom-row-2",
            children=[
                html.Div("Aplicativo desarrollado por el ingeniero Gabriel Coral para el uso exclusivo de personal de "
                "CEDENAR S.A E.S.P y Asociados"),
                html.Div("Todos los derechos de autor reservados"),
                html.Div("2021")
                ]
            ,style={'text-align': 'center',
                    'font-size': '10px',
                    'opacity': '0.60'}),
    ]
)

##----------------------------------#CallBacks#-------------------------------##
@app.callback(Output("dd_cod", "options"),
              [Input("dd_tec", "value")])
def update_ddcod(tecno):
    if json.loads(tecno)==["CATV"]:
        df_cods=options_CATV(con)
        cods=df_cods.values.tolist() #Iterable for list
        cod_options=[dict(label=str(x),value=json.dumps(x)) for x in cods]
        cod_options+=[dict(label="Todos",value=json.dumps(df_cods.CODIG_SUSCR.unique().tolist()))]
        return cod_options
    else:
        municipios=options_municipios(con,json.loads(tecno))
        mun_options=[dict(label=x[1],value=x[0]) for x in municipios]
        return mun_options

###CallBacks###
@app.callback(Output("geojson", "data"),
              [Input("dd_cod", "value")],
              [State("dd_tec", "value")])
def update(code,tecno):
    if json.loads(tecno)==["CATV"]:
        data= get_data(con,cods=json.loads(code))
        return data
    else:
        data= get_data(con,mun=code,tecno=json.loads(tecno))
        return data

@app.callback(Output("dd_cod_plotly", "options"),
              [Input("dd_tec_plotly", "value")])
def update_ddcod_plotly(tecno):
    if json.loads(tecno)==["CATV"]:
        df_cods=options_CATV(con)
        cods=df_cods.values.tolist() #Iterable for list
        cod_options=[dict(label=str(x),value=json.dumps(x)) for x in cods]
        cod_options+=[dict(label="Todos",value=json.dumps(df_cods.CODIG_SUSCR.unique().tolist()))]
        return cod_options
    else:
        municipios=options_municipios(con,json.loads(tecno))
        mun_options=[dict(label=x[1],value=x[0]) for x in municipios]
        return mun_options

@app.callback(Output("plotly_fig", "figure"),
              [Input("dd_cod_plotly", "value")],
              [State("dd_tec_plotly", "value")])
def update_plotly(code,tecno):
    ##Creating plotly figure
    if json.loads(tecno)==["CATV"]:
        df_plotly = consulta_catv(con,code)
        fig = px.scatter_mapbox(df_plotly, lat="lat", lon="lon", hover_name="CODIG_SUSCR", hover_data=["MUNICIPIO", "ID_LUMINARIA","W","TRANSFORMAD"],
                            color="CODIG_SUSCR", zoom=10, height=600)
    else:
        df_plotly = consulta_tecno_munci(con,json.loads(tecno),code)
        fig = px.scatter_mapbox(df_plotly, lat="lat", lon="lon", hover_name="TECNOLOGIA", hover_data=["MUNICIPIO", "ID_LUMINARIA","W","TRANSFORMAD"],
                    color="TECNOLOGIA", zoom=10, height=600)

    fig.update_layout(mapbox_style="dark", mapbox_accesstoken="pk.eyJ1IjoiZ2Fib2NjOTUiLCJhIjoiY2tsd3BybmN3MDFtcDJ2azJoNzdzZWcwbiJ9.OEu_jCUAe3_UhAe17RXPcA")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(clickmode='event+select')
    return fig

@app.callback([Output('edit-content', 'children'), Output('botones-editar','style'), Output('features','style'),
               Output("alert-fade", "is_open"),Output("alert-fade", "children"),Output("alert-fade", "color"),],
              [Input('edit-button', 'n_clicks'),Input('cancel-edit-button', 'n_clicks'),Input('aceptar-edit-button', 'n_clicks')],
              [State('potencia-input', 'value'),State('latitud-input', 'value'),
              State('longitud-input', 'value'),State('dd_mun_all', 'value'),
              State('codigoin-input', 'value'),State('transformador-input', 'value'),State("alert-fade", "is_open")])
def update_edit_info(n_c1,n_c2,n_c3,potencia,latitud,longitud,municipio,codigoin,transformador,is_open):
    global id_equipo
    ctx = dash.callback_context

    if not ctx.triggered:
        button_id = ''
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id== "edit-button":
        edit_layout=build_graph_title("Modo de edicion")
        return edit_layout,{'display':'flex'},{'display':'flex'},is_open,"no_return",""
    
    elif button_id=="cancel-edit-button":
        return html.Div(),{'display':'none'},{'display':'none'},is_open,"no_return",""
    
    elif button_id=="aceptar-edit-button":
        if (potencia is not None) & (municipio is not None) & (latitud is not None) & (longitud is not None) & (codigoin is not None):
            query=f"""UPDATE LUMINARIA
                    SET TRANSFORMAD='{transformador}' ,POTENCIA_WT={potencia}, DIVIS_POLIT={municipio}, LATITUD_DEC={latitud},
                    LONGITU_DEC={longitud}, CODIG_SUSCR={codigoin}
                    WHERE ID_LUMINARIA={id_equipo};"""
            try:
                cursor.execute(query);
                con.commit()
                return html.Div(),{'display':'none'},{'display':'none'},(not is_open),"Informacion actualizada","success"
            except:
                return html.Div(),{'display':'none'},{'display':'none'},(not is_open),"No se pudo actualizar la informacion","danger"
        else:
            return html.Div("Falta informacion por diligenciar, favor verificar"),{'display':'inine'},{'display':'inine'},is_open,"no_return",""
    else:
        return html.Div(),{'display':'none'},{'display':'none'},is_open,"no_return",""

@app.callback([Output('titulo-edit', 'children'), Output('transformador-input', 'value'),
              Output('potencia-input', 'value'),Output('latitud-input', 'value'),
              Output('longitud-input', 'value'),Output('dd_mun_all', 'value'),
              Output('codigoin-input', 'value')],[Input("geojson", "click_feature")])
def update_features(features):
    global id_equipo
    try:
        id_equipo=features['properties']['ID_LUMINARIA']
        msj="Informacion ID Luminaria " + str(id_equipo)
        return msj, features['properties']['TRANSFORMAD'],features['properties']['W'], features['geometry']['coordinates'][1], features['geometry']['coordinates'][0], features['properties']['DIVIS_POLIT'],features['properties']['CODIG_SUSCR']
    except:
        return "Informacion ID Luminaria ","","","","","",""
    
    
@app.callback([Output('page-content', 'children'),Output('page-content-info', 'children'),
               Output("table-contenido",'style')],
              [Input('plotly-button', 'n_clicks'),Input('Geojson-button', 'n_clicks')])
def display_page(nc1,nc2):
    ctx = dash.callback_context

    if not ctx.triggered:
        button_id = ''
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id=='plotly-button':
        return plotly_layout, "", {"display":"inline"}
    elif button_id=='Geojson-button':
        return geo_layout, info_geo_layout, {"display":"none"}

@app.callback(
    [Output('table', 'data'),Output('table', 'columns'),Output('html-tabla-resumida', 'style'),Output('Download_Table', 'style'),Output('grafica-potencia','figure')],
    [Input('plotly_fig', 'selectedData'),Input('dd_table_info', 'value'),Input('dd_table_agg', 'value')])
def display_selected_data(selectedData, estado_info, agg_values):
    global table_df
#    try:
    data_list=[]
    if selectedData is not None:
        for data in selectedData['points']:
            prov_list=[data['hovertext']]
            prov_list=prov_list+data['customdata']
            data_list.append(prov_list)
        df_selectedata=pd.DataFrame(data_list,columns=['IDENTIFICACION','MUNICIPIO','ID_LUMINARIA','POTENCIA','TRANSFORMADOR'])
        fig = px.histogram(df_selectedata, x="POTENCIA", title='Distribucion de la potencia [Watts]')
        if estado_info=="Summary":
            table_df = pd.pivot_table(df_selectedata, values=['POTENCIA', 'ID_LUMINARIA'], index=agg_values,
                    aggfunc={'POTENCIA': sum,
                             'ID_LUMINARIA': len})
    
            table_df=table_df.reset_index().rename(columns={'POTENCIA':"Suma_Total_"+'POTENCIA','ID_LUMINARIA':"Cuenta_Total_Dispositivos"})
            columns=[{"name": i, "id": i} for i in table_df.columns]
            data=table_df.to_dict('records')
            return data, columns , {"display":"inline"},{"display":"inline"},fig
        else:
            table_df=df_selectedata.copy()
            columns=[{"name": i, "id": i} for i in table_df.columns]
            data=table_df.to_dict('records')
            return data, columns , {"display":"none"}, {"display":"inline"},fig
    else:
        return [],[{"name":"","id":""}], {"display":"inline"}, {"display":"none"},px.histogram(height=450)
    
@app.callback(Output("download", "data"), [Input("Download_Table", "n_clicks")])
def generate_csv(n_nlicks):
    global table_df
    return send_data_frame(table_df.to_csv, filename="Informacion_tabla.csv")

@app.callback(Output("layer", "children"), [Input("map", "click_lat_lng")])
def map_click(click_lat_lng):
    return [dl.Marker(position=click_lat_lng, children=dl.Tooltip("({:.5f}, {:.5f})".format(*click_lat_lng)))]


# -------------------------Running the server------------------------------
if __name__ == "__main__":
    app.run_server(debug=True)
