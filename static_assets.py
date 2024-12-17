"""Compile static assets."""

import os
from os import path

from flask import Flask
from flask_assets import Bundle, Environment


def init_assets(app=None, auto_build=False, static_folder="static"):
    app = app or Flask(__name__, static_folder=static_folder)
    with app.app_context():
        env = Environment(app)
        env.load_path = [
            path.join(path.dirname(__file__), "assess/static/src"),
            path.join(path.dirname(__file__), "authenticator/frontend/static/src"),
        ]
        # env.set_directory(env_directory)
        # App Engine doesn't support automatic rebuilding.
        env.auto_build = auto_build
        # This file needs to be shipped with your code.
        env.manifest = "file"

        js = Bundle(
            "./assess/js/namespaces.js",
            "./assess/js/helpers.js",
            "./assess/js/all.js",
            "./assess/js/components/*/*.js",
            "./assess/js/init.js",
            filters="jsmin",
            output="assess/js/main.min.js",
        )
        css = Bundle(
            "./assess/css/*.css",
            filters="cssmin",
            output="assess/css/main.min.css",
            extra={"rel": "stylesheet/css"},
        )

        authenticator_js = Bundle(
            "./authenticator/js/namespaces.js",
            "./authenticator/js/helpers.js",
            "./authenticator/js/all.js",
            "./authenticator/js/fsd_cookies.js",
            "./authenticator/js/components/**/*.js",
            filters="jsmin",
            output="authenticator/js/main.min.js",
        )

        env.register("authenticator_main_js", authenticator_js)
        env.register("default_styles", css)
        env.register("main_js", js)

        bundles = [authenticator_js, css, js]

        return bundles


def build_bundles(static_folder="static"):
    os.makedirs(static_folder, exist_ok=True)
    bundles = init_assets(static_folder=static_folder)
    for bundle in bundles:
        bundle.build()


if __name__ == "__main__":
    build_bundles()
