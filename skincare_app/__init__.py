import pandas as pd
import os
from flask import Flask


# application factory function
def create_app(test_config=None):
    # create and configure the skincare_app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'skincare_app.db'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    with app.app_context():
        # load the product dataset and store it in the app's context
        product_df = pd.read_pickle('skincare_app/static/data/product_data.pkl')
        app.config['PRODUCT_DF'] = product_df

        from .insights import init_dashboard
        init_dashboard(app)

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import routine
    app.register_blueprint(routine.bp)




    return app
