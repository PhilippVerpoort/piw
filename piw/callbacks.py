from copy import deepcopy
from pathlib import Path
from typing import Callable

from dash import Dash
from dash import callback_context as ctx
from dash.dependencies import Input, Output, State
from flask import send_file

from piw.abstract_plot import AbstractPlot


ASSETS = Path(__file__).parent / 'assets'

def setCallbacks(dash_app: Dash, plots: list[AbstractPlot], subfigPlotsInit: dict, generateArgs: list,
                 def_inputs: dict, update: list[Callable], display: Callable):
    # create lists containing all figNames and subfigNames
    figNames = [figName for plot in plots for figName in plot.figs]
    subfigNames = [subfigName for plot in plots for subfigName in plot.subfigs]

    # serving asset files
    @dash_app.server.route('/assets/<path>')
    def serveAssets(path: str):
        return send_file(ASSETS / path, as_attachment=True)

    # show/hide figure cards
    @dash_app.callback(
        [*(Output(f"card-{figName}", 'style') for figName in figNames)],
        [Input('url', 'pathname')]
    )
    def showFigCards(route):
        show = {}
        hide = {'display': 'none'}

        return [
            show if route.lstrip('/') in figSpecs['display'] else hide
            for plot in plots
            for figName, figSpecs in plot.figs.items()
        ]

    # general callback for (re-)generating plots
    @dash_app.callback(
        [*(Output(subfigName, 'figure') for subfigName in subfigNames), ],
        [*generateArgs,
         State('url', 'pathname'), ])
    def callbackUpdate(*args):
        route = args[-1]

        if not ctx.triggered:
            # load default figures for initial display
            subfigsGenerated = subfigPlotsInit
        else:
            # get name of button pressed
            try:
                btnPressed = ctx.triggered[0]['prop_id'].split('.')[0]
            except Exception:
                btnPressed = None

            # get new input and output data
            inputsUpdated = deepcopy(def_inputs)
            for u in update:
                u(inputsUpdated, btnPressed, args)

            # get list of figs required
            figNamesReq = [
                figName
                for plot in plots
                for figName, figSpecs in plot.figs.items()
                if route.lstrip('/') in figSpecs['display']
            ]

            # get figures
            subfigsGenerated = display(inputsUpdated, figNamesReq)

        # sort generated subfigs and return
        subfigsReturn = dict(sorted(subfigsGenerated.items(), key=lambda t: subfigNames.index(t[0])))
        return *subfigsReturn.values(),
