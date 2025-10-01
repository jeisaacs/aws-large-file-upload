import boto3
import os
from boto3.s3.transfer import TransferConfig
from math import ceil

# Initialize S3 client
s3_client = boto3.client('s3')

def upload_with_progress(file_path, bucket_name, storage_class):
    try:
        file_size = os.path.getsize(file_path)
        chunk_size = 1024 * 1024 * 50  # 50 MB Chunk Size
        total_chunks = ceil(file_size / chunk_size)

        # Extract the filename from the path to use as the S3 key (upload to root)
        s3_key = os.path.basename(file_path)

        # Create multipart upload and get the UploadId
        response = s3_client.create_multipart_upload(Bucket=bucket_name, Key=s3_key, StorageClass=storage_class)
        upload_id = response['UploadId']
        print(f"UploadId: {upload_id}")

        # Upload parts
        parts = []
        with open(file_path, 'rb') as file:
            for part_number in range(1, total_chunks + 1):
                print(f"Uploading chunk {part_number}/{total_chunks}...")
                chunk = file.read(chunk_size)
                response = s3_client.upload_part(
                    Bucket=bucket_name,
                    Key=s3_key,
                    PartNumber=part_number,
                    UploadId=upload_id,
                    Body=chunk
                )
                parts.append({'ETag': response['ETag'], 'PartNumber': part_number})
                uploaded_mb = part_number * chunk_size / (1024 * 1024)
                remaining_mb = max(0, (file_size - part_number * chunk_size) / (1024 * 1024))
                print(f"Progress: Uploaded {uploaded_mb:.2f} MB, Remaining {remaining_mb:.2f} MB")

        # Complete multipart upload
        s3_client.complete_multipart_upload(
            Bucket=bucket_name,
            Key=s3_key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
        print(f"Upload completed successfully for {file_path} to s3://{bucket_name}/{s3_key}.")

    except Exception as e:
        print(f"An error occurred: {e}")
        # Abort the upload if any error occurs
        if 'upload_id' in locals():
            s3_client.abort_multipart_upload(Bucket=bucket_name, Key=s3_key, UploadId=upload_id)
            print(f"Multipart upload aborted for UploadId: {upload_id}")

if __name__ == '__main__':
    # Define the variables
    FILE_PATH = "path/to/your/file.ext"  # Replace with your actual file path
    BUCKET_NAME = "bigchange-onedrive-backup"  # Replace with your actual S3 bucket name
    STORAGE_CLASS = "DEEP_ARCHIVE"  # Example: "STANDARD", "GLACIER", "REDUCED_REDUNDANCY"

    # Check if the file exists before uploading
    if not os.path.exists(FILE_PATH):
        print(f"File {FILE_PATH} does not exist. Please check the file path.")
    else:
        upload_with_progress(FILE_PATH, BUCKET_NAME, STORAGE_CLASS)
