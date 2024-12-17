import os
import shutil
import urllib.request
import zipfile

import static_assets


def build_apply_assets():
    if os.path.exists("static"):
        shutil.rmtree("static")

    # Download zips using "url"
    print("Downloading static file zip.")

    url = "https://github.com/alphagov/govuk-frontend/releases/download/v4.0.0/release-v4.0.0.zip"

    # There is a known problem on Mac where one must manually
    # run the script "Install Certificates.command" found
    # in the python application folder for this to work.
    urllib.request.urlretrieve(url, "./govuk_frontend.zip")  # nosec

    print("Deleting old static/apply")

    # Attempts to delete the old files, states if
    # one doesnt exist.
    try:
        shutil.rmtree("static/apply")
    except FileNotFoundError:
        print("No old static/apply to remove.")

    print("Unzipping file to static/apply...")

    # Extracts the previously downloaded zip to /static/apply
    with zipfile.ZipFile("./govuk_frontend.zip", "r") as zip_ref:
        zip_ref.extractall("./static/apply")

    print("Moving files from static/apply/assets to static/apply")

    for file_to_move in os.listdir("./static/apply/assets"):
        shutil.move("./static/apply/assets/" + file_to_move, "static/apply")

    # FIXME: Sorry - we plan to remove this hack when we have pulled in the assessment frontend and got both
    #        things using the same version of GOV.UK Frontend. For now, because we use pre-compiled CSS from GOV.UK
    #        Frontend, it expects assets to be served from a specific URL path (/assets) - so we need to reproduce
    #        that structure here.
    print("Copying images and fonts to /static for hard-coded CSS in GOV.UK Frontend")
    shutil.copytree("static/apply/images", "static/images")
    shutil.copytree("static/apply/fonts", "static/fonts")

    print("Copying css and js from static/src")

    # Copy css
    os.makedirs("./static/apply/styles")
    shutil.copyfile("apply/static/src/styles/tasklist.css", "./static/apply/styles/tasklist.css")

    # Copy over JS source
    os.makedirs("./static/apply/js")
    shutil.copyfile("apply/static/src/js/fsd_cookies.js", "./static/apply/js/fsd_cookies.js")

    print("Deleting temp files")
    # Deletes temp. files.
    shutil.rmtree("./static/apply/assets")
    os.remove("./govuk_frontend.zip")


def build_some_assess_assets(static_dist_root="static/assess"):
    DIST_ROOT = "./" + static_dist_root
    GOVUK_DIR = "/govuk-frontend"
    GOVUK_URL = "https://github.com/alphagov/govuk-frontend/releases/download/v4.7.0/release-v4.7.0.zip"
    ZIP_FILE = "./govuk_frontend.zip"
    DIST_PATH = DIST_ROOT + GOVUK_DIR
    ASSETS_DIR = "/assets"
    ASSETS_PATH = DIST_PATH + ASSETS_DIR

    # Checks if GovUK Frontend Assets already built
    if os.path.exists(DIST_PATH):
        print(
            "GovUK Frontend assets already built. If you require a rebuild manually run build.build_some_assess_assets"
        )
        return True

    # Download zips from GOVUK_URL
    # There is a known problem on Mac where one must manually
    # run the script "Install Certificates.command" found
    # in the python application folder for this to work.

    print("Downloading static file zip.")
    urllib.request.urlretrieve(GOVUK_URL, ZIP_FILE)  # nosec

    # Attempts to delete the old files, states if
    # one doesn't exist.

    print("Deleting old " + DIST_PATH)
    try:
        shutil.rmtree(DIST_PATH)
    except FileNotFoundError:
        print("No old " + DIST_PATH + " to remove.")

    # Extract the previously downloaded zip to DIST_PATH

    print("Unzipping file to " + DIST_PATH + "...")
    with zipfile.ZipFile(ZIP_FILE, "r") as zip_ref:
        zip_ref.extractall(DIST_PATH)

    # Move files from ASSETS_PATH to DIST_PATH

    print("Moving files from " + ASSETS_PATH + " to " + DIST_PATH)
    for file_to_move in os.listdir(ASSETS_PATH):
        shutil.move("/".join([ASSETS_PATH, file_to_move]), DIST_PATH)

    # Copy css
    os.makedirs("./static/assess/styles")
    shutil.copyfile(
        "assess/static/src/styles/landing.css",
        "./static/assess/styles/landing.css",
    )
    shutil.copyfile(
        "assess/static/src/styles/govuk-overrides.css",
        "./static/assess/styles/govuk-overrides.css",
    )
    shutil.copyfile(
        "assess/static/src/styles/comments.css",
        "./static/assess/styles/comments.css",
    )

    # Copy over JS source
    os.makedirs("./static/assess/js")
    shutil.copyfile("assess/static/src/assess/js/fsd_cookies.js", "./static/assess/js/fsd_cookies.js")

    # Delete temp files
    print("Deleting " + ASSETS_PATH)
    shutil.rmtree(ASSETS_PATH)
    os.remove(ZIP_FILE)


def build_some_authenticator_assets(static_dist_root="static/authenticator", remove_existing=False) -> None:
    DIST_ROOT = "./" + static_dist_root
    GOVUK_URL = "https://github.com/alphagov/govuk-frontend/releases/download/v4.8.0/release-v4.8.0.zip"
    ZIP_FILE = "./govuk_frontend.zip"
    DIST_PATH = DIST_ROOT
    ASSETS_DIR = "/assets"
    ASSETS_PATH = DIST_PATH + ASSETS_DIR

    # Checks if GovUK Frontend Assets already built
    if os.path.exists(DIST_PATH):
        print("GovUK Frontend assets already built. If you require a rebuild manually run build.build_govuk_assets")
        return True

    # Download zips from GOVUK_URL
    # There is a known problem on Mac where one must manually
    # run the script "Install Certificates.command" found
    # in the python application folder for this to work.

    print("Downloading static file zip.")
    urllib.request.urlretrieve(GOVUK_URL, ZIP_FILE)  # nosec

    # Attempts to delete the old files, states if
    # one doesn't exist.

    print("Deleting old " + DIST_PATH)
    try:
        shutil.rmtree(DIST_PATH)
    except FileNotFoundError:
        print("No old " + DIST_PATH + " to remove.")

    # Extract the previously downloaded zip to DIST_PATH

    print("Unzipping file to " + DIST_PATH + "...")
    with zipfile.ZipFile(ZIP_FILE, "r") as zip_ref:
        zip_ref.extractall(DIST_PATH)

    # Move files from ASSETS_PATH to DIST_PATH

    print("Moving files from " + ASSETS_PATH + " to " + DIST_PATH)
    for file_to_move in os.listdir(ASSETS_PATH):
        shutil.move("/".join([ASSETS_PATH, file_to_move]), DIST_PATH)

    # Delete temp files
    print("Deleting " + ASSETS_PATH)
    shutil.rmtree(ASSETS_PATH)
    os.remove(ZIP_FILE)


def build_assess_authenticator_assets(remove_existing=False):
    if remove_existing:
        for static_dist_root in ["static/authenticator", "static/assess"]:
            relative_dist_root = "./" + static_dist_root
            if os.path.exists(relative_dist_root):
                shutil.rmtree(relative_dist_root)
    build_some_authenticator_assets(static_dist_root="static/authenticator")
    build_some_assess_assets(static_dist_root="static/assess")
    static_assets.build_bundles(static_folder="static")


if __name__ == "__main__":
    build_apply_assets()
    build_assess_authenticator_assets()
