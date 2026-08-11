import boto3

from app.core.config import settings


s3_client = boto3.client(
    "s3",
    region_name=settings.AWS_DEFAULT_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)


def s3_upload(
    contents: bytes,
    key: str,
    content_type: str
):

    s3_client.put_object(
        Bucket=settings.AWS_BUCKET,
        Key=key,
        Body=contents,
        ContentType=content_type
    )


def get_s3_hash(
    key: str
) -> str | None:

    try:

        head = s3_client.head_object(
            Bucket=settings.AWS_BUCKET,
            Key=key
        )

        return head["ETag"].strip('"')

    except Exception:
        return None


def generate_presigned_url(
    key: str
) -> str:

    return s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_BUCKET,
            "Key": key
        },
        ExpiresIn=3600
    )