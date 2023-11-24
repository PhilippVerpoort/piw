from typing import Optional, Type

from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

from piw.abstract_plot import AbstractPlot


# default app links in upper right corner
DEFLINKS = {
    'Impressum': 'https://interactive.pik-potsdam.de/impressum',
    'Accessibility': 'https://interactive.pik-potsdam.de/accessibility',
    'Privacy policy': 'https://interactive.pik-potsdam.de/privacy-policy',
}

# create app layout
def createLayout(dash_app: Dash, pages: dict, links: Optional[dict[str, str]], ctrls: list, plots: list[Type[AbstractPlot]], sort_figs: Optional[list],
                 title: str, desc: Optional[str], authors: Optional[list[str]], date: Optional[str], def_inputs: dict):
    # define page tabs
    pageDivs = [
        html.Div(
            dcc.Link(
                pageName,
                href=dash_app.get_relative_path(f"/{pagePath}"),
                className='mainlink',
            ),
            className='app-modes',
        )
        for pagePath, pageName in pages.items()
    ] if len(pages) > 1 else []

    # define links in upper right corner
    links = links if links is not None else DEFLINKS
    linkDivs = [
        html.Div(
            dcc.Link(
                linkName,
                href=linkHref,
                className='mainlink',
            ),
        )
        for linkName, linkHref in links.items()
    ]

    # define summary card
    summary = html.Div(
        id='summary-card',
        children=[
            html.H5('PIK Interactive Webapp'),
            html.H3(title),
            html.Div(
                id='desc',
                children=desc,
            ) if desc is not None else None,
            html.Div(
                id='auth',
                children=', '.join(authors),
            ) if authors is not None else None,
            html.Div(
                id='date',
                children=f"Published on {date}",
            ) if date is not None else None,
        ],
        className='side-card elements-card',
    )

    # define control cards
    ctrlDivs = []
    for c in ctrls:
        ctrlDivs.extend(c(def_inputs))

    # define modal window for updating plot configs
    plotConfigModal = dbc.Modal(
        [
            dbc.ModalHeader('Update plot config'),
            dbc.ModalBody(
                [
                    dbc.Label('Config:'),
                    dcc.Textarea(id='plot-config-modal-textfield', style={'width': '100%', 'height': 500}),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button('OK', color='primary', id='plot-config-modal-ok'),
                    dbc.Button('Cancel', id='plot-config-modal-cancel'),
                ]
            ),
        ],
        id='plot-config-modal',
    )

    # define full layout
    dash_app.layout = html.Div(
        id='app-container',

        # banner
        children=[
            html.Div(
                id='banner',
                className='banner',
                children=[
                    html.Div(
                        children=[
                            html.A(
                                html.Img(src=dash_app.get_asset_url("logo.png")),
                                href='https://www.pik-potsdam.de/',
                            ),
                            html.Div(
                                html.B(title),
                                className='app-title',
                            ),
                            *pageDivs,
                        ],
                        className='header-left-side',
                    ),
                    html.Div(
                        children=linkDivs,
                        className='header-right-side',
                    ),
                ],
            ),

            # left column
            html.Div(
                id='left-column',
                className='four columns',
                children=[summary] + ctrlDivs
            ),

            # right column
            html.Div(
                id='right-column',
                className='eight columns',
                children=figureCards(plots, sort_figs),
            ),

            # modals
            plotConfigModal,

            # dcc locations, stores, and downloads
            dcc.Location(id='url', refresh=False),
            # dcc.Store(id='plot-cfgs', storage_type='memory', data=plot_cfgs),
        ],
    )

# create all figure cards
def figureCards(plots: list[Type[AbstractPlot]], sort_figs: Optional[list]):
    cards = {}

    for Plot in plots:
        for figName, figSpecs in Plot.figs.items():
            if 'subfigs' in figSpecs:
                subfigs = [
                    (subfigName, subfigSpecs['size']['webapp']['height'], subfigSpecs['size']['webapp']['width'])
                    for subfigName, subfigSpecs in figSpecs['subfigs'].items()
                ]
            else:
                subfigs = [(figName, figSpecs['size']['webapp']['height'], figSpecs['size']['webapp']['width'])]

            displayDefault = '' in figSpecs['display']

            cards[figName] = html.Div(
                id=f"card-{figName}",
                className='fig-card',
                children=[
                    *(
                        dcc.Loading(
                            children=[
                                dcc.Graph(
                                    id=subFigName,
                                    style={
                                        'height': subFigHeight,
                                        'width': f"{subFigWidth}%",
                                        'float': 'left',
                                    },
                                ),
                            ],
                            type='circle',
                            style={
                                'height': subFigHeight,
                                'width': f"{subFigWidth}%",
                                'float': 'left',
                            },
                        )
                        for subFigName, subFigHeight, subFigWidth in subfigs
                    ),
                    html.Hr(),
                    html.B(f"{figSpecs['name']} | {figSpecs['title']}"),
                    html.P(figSpecs['desc']),
                    html.Div([
                            html.Hr(),
                            html.Button(id=f"{figName}-settings", children='Config', n_clicks=0, ),
                        ],
                        id=f"{figName}-settings-div",
                        style={'display': 'none'},
                    ),
                ],
                style={} if displayDefault else {'display': 'none'},
            )

    if sort_figs is None:
        return list(cards.values())
    else:
        return list(dict(sorted(cards.items(), key=lambda t: sort_figs.index(t[0]))).values())
