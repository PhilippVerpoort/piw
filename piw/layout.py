from datetime import datetime
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
                  figs_displayed: dict[str, dict], sort_figs: Optional[list], metadata: dict, def_inputs: dict):
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

    # define metadata card
    authors_list = [
        html.Span(
            [f"{author['first']} {author['last']}"] +
            ([] if 'orcid' not in author else
            [' ', html.A(
                html.Img(
                    src='https://info.orcid.org/wp-content/uploads/2020/12/orcid_16x16.gif',
                    width='16',
                    height='16',
                ),
                href=f"https://orcid.org/{author['orcid']}"
            )])
        )
        for author in metadata['authors']
    ]
    authors = html.Span(children=[
        e for i in zip(
            [a for a in authors_list[:-1]],
            (len(authors_list) - 1) * [', ']
        ) for e in i
    ] + [
        authors_list[-1]
    ]) if authors_list else 'No authors provided'

    meta_card = html.Div(
        id='meta-card',
        children=[
            html.H5(
                id='meta-heading',
                children='PIK Interactive Webapp',
            ),
            html.H3(
                id='meta-title',
                children=metadata['title'],
            ),
            html.Div(
                id='meta-authors',
                children=authors,
            ),
            html.Div(
                id='meta-date',
                children=f"Published: {datetime.strptime(metadata['date'], '%Y-%m-%d').strftime('%d %b %Y')}",
            ),
            html.Div(
                id='meta-doi',
                children=[
                    html.Span('DOI: '),
                    html.A(
                        metadata['doi'],
                        href=f"https://doi.org/{metadata['doi']}",
                        target='_blank',
                    ),
                ],
            ) if 'doi' in metadata else None,
            html.Div(
                id='meta-licence',
                children=[
                    html.Span('Licence: '),
                    html.A(
                        metadata['licence']['name'],
                        href=metadata['licence']['link'],
                        target='_blank',
                    ),
                ],
            ) if 'doi' in metadata else None,
            html.Div(
                id='meta-reference',
                children=['Accompanying: ', metadata['reference_citeas']] +
                ([
                    ' DOI: ',
                    html.A(
                        metadata['reference_doi'],
                        href=f"https://doi.org/{metadata['reference_doi']}",
                        target='_blank',
                    ),
                ] if 'reference_doi' in metadata else []),
            ) if 'reference_citeas' in metadata else None,
            html.Div(
                id='meta-abstract',
                children=metadata['abstract'],
            ),
            html.Button(id='btn-about', n_clicks=0, children='ABOUT', className='btn btn-primary'),
            html.A(
                html.Button(id='btn-paper', n_clicks=0, children='Paper', className='btn btn-outline-secondary'),
                href=f"https://doi.org/{metadata['reference_doi']}", target='_blank',
            ) if 'reference_doi' in metadata else None,
        ],
        className='side-card elements-card',
    )

    # define modal window for about details
    about_modal = dbc.Modal(
        [
            dbc.ModalHeader(html.B('About this webapp')),
            dbc.ModalBody(
                [
                    html.Div(
                        children=metadata['about'],
                    ),
                    html.Div(
                        children=[
                            html.B('Cite as:'),
                            ' ' + metadata['citeas'],
                        ],
                    ),
                    html.Div(
                        children=[
                            html.B('Published:'),
                            ' ' + datetime.strptime(metadata['date'], '%Y-%m-%d').strftime('%d %b %Y'),
                        ],
                    ),
                    html.Div(
                        children=[
                            html.B('Version:'),
                            ' ' + metadata['version'],
                        ],
                    ) if 'version' in metadata else None,
                    html.Div(
                        children=[
                            html.B('DOI:'),
                            ' ',
                            html.A(metadata['doi'], href=f"https://doi.org/{metadata['doi']}"),
                        ],
                    ) if 'doi' in metadata else None,
                    html.Div(
                        children=[
                            html.B('Licence:'),
                            ' ',
                            html.A(metadata['licence']['name'], href=metadata['licence']['link']),
                        ],
                    ) if 'licence' in metadata else None,
                    html.Div(
                        children=[html.B('Accompanying:'), ' ', metadata['reference_citeas']] +
                        ([
                            ', DOI: ',
                            html.A(metadata['reference_doi'], href=f"https://doi.org/{metadata['reference_doi']}"),
                        ] if 'reference_doi' in metadata else []),
                    ) if 'reference_citeas' in metadata else None,
                ]
            ),
        ],
        id='about-modal',
    )

    # define control cards
    ctrl_divs = []
    for c in ctrls:
        ctrl_divs.extend(c(def_inputs))

    # define modal window for editing control tables
    ctrl_tables_modal = dbc.Modal(
        [
            dbc.ModalHeader('Update value'),
            dbc.ModalBody(
                [
                    dbc.Label('Value:'),
                    dcc.Textarea(id='ctrl-tables-modal-textfield', style={'width': '100%', 'height': 500}),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button('OK', color='primary', id='ctrl-tables-modal-ok'),
                    dbc.Button('Cancel', id='ctrl-tables-modal-cancel'),
                ]
            ),
        ],
        id='ctrl-tables-modal',
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
                                html.B(metadata['title']),
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
                children=[meta_card] + ctrl_divs
            ),

            # right column
            html.Div(
                id='right-column',
                className='eight columns',
                children=figure_cards(figs_displayed, sort_figs),
            ),

            # modals
            ctrl_tables_modal,
            about_modal,

            # dcc locations and stores
            dcc.Location(id='url', refresh=False),
            dcc.Store(id='ctrl-tables-modal-open', storage_type='session', data=''),
            dcc.Store(id='about-modal-open', storage_type='session', data=''),
        ],
    )


# create all figure cards
def figure_cards(figs_displayed: dict[str, dict], sort_figs: Optional[list]):
    cards = {}

    for fig_name, fig_specs in figs_displayed.items():
        if 'subfigs' in fig_specs:
            subfigs = [
                (subfigName, subfigSpecs['size']['webapp']['width'], subfigSpecs['size']['webapp']['height'])
                for subfigName, subfigSpecs in fig_specs['subfigs'].items()
            ]
        else:
            subfigs = [(fig_name, fig_specs['size']['webapp']['width'], fig_specs['size']['webapp']['height'])]

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
                                    'width': f"{sub_fig_width}%",
                                    'height': sub_fig_height,
                                    'float': 'left',
                                },
                            ),
                        ],
                        type='circle',
                        style={
                            'width': f"{sub_fig_width}%",
                            'height': sub_fig_height,
                            'float': 'left',
                        },
                    )
                    for sub_fig_name, sub_fig_width, sub_fig_height in subfigs
                ),
                html.Hr(),
                html.B(f"{fig_specs['name']} | {fig_specs['title']}"),
                html.P(fig_specs['desc']),
            ],
            style={} if display_default else {'display': 'none'},
        )

    if sort_figs is None:
        return list(cards.values())
    else:
        return list(dict(sorted(cards.items(), key=lambda t: sort_figs.index(t[0]))).values())
