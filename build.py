import os
import shutil
import urllib.request
import zipfile


def build_assets():
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


if __name__ == "__main__":
    build_assets()
