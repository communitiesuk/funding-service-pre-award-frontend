from collections import namedtuple
from os import getenv
from urllib.parse import quote

from boto3 import client
from botocore.exceptions import ClientError
from flask import current_app, url_for

from config import Config

_S3_CLIENT = client(
    "s3",
    region_name=Config.AWS_REGION,
    endpoint_url=getenv("AWS_ENDPOINT_OVERRIDE", None),
)


def get_file_for_download_from_aws(file_name: str, application_id: str):
    """_summary_: Function is set up to retrieve
    files from aws bucket.
    Args:
        filename: Takes an filename
        application_id: Takes an application_id # noqa
    Returns:
        Returns a tuple of (file_content, mime_type)
    """

    if file_name is None:
        return None

    prefixed_file_name = application_id + "/" + file_name

    try:
        current_app.logger.info(
            "Retrieving file {prefixed_file_name} from AWS", extra=dict(prefixed_file_name=prefixed_file_name)
        )
        obj = _S3_CLIENT.get_object(Bucket=Config.AWS_BUCKET_NAME, Key=prefixed_file_name)

        mimetype = obj["ResponseMetadata"]["HTTPHeaders"]["content-type"]
        data = obj["Body"].read()

        return data, mimetype
    except ClientError as e:
        current_app.logger.error(e)
        raise Exception(e) from e


def list_files_in_folder(prefix):
    response = _S3_CLIENT.list_objects_v2(Bucket=Config.AWS_BUCKET_NAME, Prefix=prefix)
    keys = []
    for obj in response.get("Contents") or []:
        # we cut off the application id.
        _, key = obj["Key"].split("/", 1)
        keys.append(key)
    return keys


_KEY_PARTS = ("application_id", "form", "path", "component_id", "filename")
FileData = namedtuple("FileData", _KEY_PARTS)


def generate_url(file_data: FileData, short_id: str = "") -> str:
    generated_url = url_for(
        "assessment_bp.get_file",
        application_id=file_data.application_id,
        file_name=quote("/".join(file_data[1:]), safe=""),
        short_id=short_id or None,
        quoted=True,
    )
    return generated_url


def list_files_by_prefix(prefix: str) -> list[FileData]:
    objects_response = _S3_CLIENT.list_objects_v2(
        Bucket=Config.AWS_BUCKET_NAME,
        Prefix=prefix,
    )

    contents = objects_response.get("Contents") or []
    return [
        FileData(*key_parts)
        for key in [file["Key"] for file in contents]
        if len(key_parts := key.split("/")) == len(_KEY_PARTS)
    ]
