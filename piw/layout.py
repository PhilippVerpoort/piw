from typing import Optional, Final

from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

from piw.abstract_plot import AbstractPlot


# default app links in upper right corner
DEFLINKS: Final[dict[str, str]] = {
    'Imprint': 'https://interactive.pik-potsdam.de/imprint',
    'Accessibility': 'https://interactive.pik-potsdam.de/accessibility',
    'Privacy policy': 'https://interactive.pik-potsdam.de/privacy-policy',
}


# create app layout
def create_layout(dash_app: Dash, pages: dict, links: Optional[dict[str, str]], ctrls: list,
                  plots: list[AbstractPlot], sort_figs: Optional[list], title: str, desc: Optional[str],
                  authors: Optional[list[str]], date: Optional[str], def_inputs: dict):
    # define page tabs
    page_divs = [
        html.Div(
            dcc.Link(
                page_name,
                href=dash_app.get_relative_path(f"/{page_path}"),
                className='nav-link',
            ),
            className='app-modes',
        )
        for page_path, page_name in pages.items()
    ] if len(pages) > 1 else []

    # define links in upper right corner
    links = links if links is not None else DEFLINKS
    link_divs = [
        html.Div(
            dcc.Link(
                link_name,
                href=link_href,
                className='nav-link',
            ),
        )
        for link_name, link_href in links.items()
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
    ctrl_divs = []
    for c in ctrls:
        ctrl_divs.extend(c(def_inputs))

    # define modal window for updating plot configs
    plot_config_modal = dbc.Modal(
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
                            *page_divs,
                        ],
                        className='header-left-side',
                    ),
                    html.Div(
                        children=link_divs,
                        className='header-right-side',
                    ),
                ],
            ),

            # left column
            html.Div(
                id='left-column',
                className='four columns',
                children=[summary] + ctrl_divs
            ),

            # right column
            html.Div(
                id='right-column',
                className='eight columns',
                children=figure_cards(plots, sort_figs),
            ),

            # modals
            plot_config_modal,

            # dcc locations, stores, and downloads
            dcc.Location(id='url', refresh=False),
            # dcc.Store(id='plot-cfgs', storage_type='memory', data=plot_cfgs),
        ],
    )


# create all figure cards
def figure_cards(plots: list[AbstractPlot], sort_figs: Optional[list]):
    cards = {}

    for Plot in plots:
        for fig_name, fig_specs in Plot.figs.items():
            if 'subfigs' in fig_specs:
                subfigs = [
                    (subfigName, subfigSpecs['size']['webapp']['height'], subfigSpecs['size']['webapp']['width'])
                    for subfigName, subfigSpecs in fig_specs['subfigs'].items()
                ]
            else:
                subfigs = [(fig_name, fig_specs['size']['webapp']['height'], fig_specs['size']['webapp']['width'])]

            display_default = '' in fig_specs['display']

            cards[fig_name] = html.Div(
                id=f"card-{fig_name}",
                className='fig-card',
                children=[
                    *(
                        dcc.Loading(
                            children=[
                                dcc.Graph(
                                    id=sub_fig_name,
                                    style={
                                        'height': sub_fig_height,
                                        'width': f"{sub_fig_width}%",
                                        'float': 'left',
                                    },
                                ),
                            ],
                            type='circle',
                            style={
                                'height': sub_fig_height,
                                'width': f"{sub_fig_width}%",
                                'float': 'left',
                            },
                        )
                        for sub_fig_name, sub_fig_height, sub_fig_width in subfigs
                    ),
                    html.Hr(),
                    html.B(f"{fig_specs['name']} | {fig_specs['title']}"),
                    html.P(fig_specs['desc']),
                    html.Div([
                            html.Hr(),
                            html.Button(id=f"{fig_name}-settings", children='Config', n_clicks=0, ),
                        ],
                        id=f"{fig_name}-settings-div",
                        style={'display': 'none'},
                    ),
                ],
                style={} if display_default else {'display': 'none'},
            )

    if sort_figs is None:
        return list(cards.values())
    else:
        return list(dict(sorted(cards.items(), key=lambda t: sort_figs.index(t[0]))).values())
