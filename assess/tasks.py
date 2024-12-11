import shutil

from invoke import task

# this should almost definitely dissapear - it should be covered by the build scripts
@task
def copy_styles(c):
    source_path = "./app/static/src/"
    dist_path = "./app/static/dist/"

    shutil.copytree(source_path, dist_path, dirs_exist_ok=True)
    print("Copied styles from " + source_path + " to " + dist_path)
