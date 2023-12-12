# Potsdam Interactive Webapp (PIW) framework library

## Summary

This Python package can be used to host interactive webapps that make research available in an interactive and reusable way.

## How to use this library

This package can be added as a dependency via `poetry`:
```commandline
poetry install git+https://github.com/PhilippVerpoort/piw.git # when using poetry
# OR
pip install git+https://github.com/PhilippVerpoort/piw.git # when using pip
```

You can then create a webapp via:
```python
from piw import Webapp
from dash.dependencies import Input, State

webapp = Webapp(
    piw_id='my_webapp_id',
    load=[my_load_func],
    ctrls=[my_ctrl_func],
    generate_args=[
        Input('my-update-button', 'n_clicks'),
        State('my-parameter-table', 'data'),
    ],
    update=[my_update_func],
    proc=[my_process_func],
    plots=[MyFirstPlot, MySecondPlot],
)
```

The classes `MyFirstPlot` and `MySecondPlot` must be subclasses of `piw.AbstractPlot`. You can then export the figures into files via:
```python
webapp.export()
```
You can also launch the webapp on your local machine via:
```python
webapp.start()
webapp.run()
```
To host this webapp as a service with a WSGI-capable webserver (such as Apache2 with `mod_wsgi`), you need to create a file `wsgi.py` as such:
```python
import sys, os
sys.path.insert(0,os.path.dirname(__file__))

from webapp import webapp

webapp.start()
application = webapp.flask_app
```
More details on hosting Flask apps with WSGI can be found [here](https://flask.palletsprojects.com/en/2.0.x/deploying/mod_wsgi/).

A more extensive tutorial on getting started with `piw` will soon be made available. Meanwhile, the following examples may server as a starting point:
* [green-value-chains](https://github.com/PhilippVerpoort/green-value-chains/)
* [blue-green-H2](https://github.com/PhilippVerpoort/blue-green-H2)
