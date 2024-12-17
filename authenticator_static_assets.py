"""Compile static assets."""

import os
from os import path

from flask import Flask
from flask_assets import Bundle, Environment


def init_assets(app=None, auto_build=False, static_folder="static"):
    app = app or Flask(__name__, static_folder=static_folder)
    with app.app_context():
        env = Environment(app)
        env.load_path = [path.join(path.dirname(__file__), "authenticator/frontend/static/src")]
        # env.set_directory(env_directory)
        # App Engine doesn't support automatic rebuilding.
        env.auto_build = auto_build
        # This file needs to be shipped with your code.
        env.manifest = "file"

        js = Bundle(
            "./js/namespaces.js",
            "./js/helpers.js",
            "./js/all.js",
            "./js/fsd_cookies.js",
            "./js/components/**/*.js",
            filters="jsmin",
            output="authenticator/js/main.min.js",
        )

        env.register("authenticator_main_js", js)

        bundles = [js]
        return bundles


def build_bundles(static_folder="static"):
    os.makedirs(static_folder, exist_ok=True)
    bundles = init_assets(static_folder=static_folder)
    for bundle in bundles:
        bundle.build()


if __name__ == "__main__":
    build_bundles()
