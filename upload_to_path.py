import boto3
import os
from math import ceil

# Initialize S3 client
s3_client = boto3.client('s3')

# Set your S3 bucket and folder
BUCKET_NAME = "synology01-backup-video"
S3_ROOT_FOLDER = "tv"  # Base folder in S3

# Set local folder path (update this to your actual desktop folder)
LOCAL_FOLDER_PATH = os.path.expanduser("~/Desktop/Curb Your Enthusiasm")  # Update this!

# Glacier Deep Archive Storage Class
STORAGE_CLASS = "DEEP_ARCHIVE"

def folder_exists_in_s3(bucket_name, s3_key):
    """Checks if a folder already exists in S3."""
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=s3_key, MaxKeys=1)
    return 'Contents' in response  # Returns True if the folder exists, False otherwise

def upload_with_progress(file_path, s3_key, bucket_name):
    """Uploads a file to S3 with multipart upload, supporting Glacier Deep Archive."""
    try:
        file_size = os.path.getsize(file_path)
        chunk_size = 1024 * 1024 * 50  # 50 MB Chunk Size
        total_chunks = ceil(file_size / chunk_size)

        # Check if the file already exists in S3
        existing_files = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=s3_key)
        if 'Contents' in existing_files:
            print(f"⚠ File already exists in S3: {s3_key}. Skipping upload.")
            return

        # Create multipart upload with Glacier Deep Archive storage
        response = s3_client.create_multipart_upload(Bucket=bucket_name, Key=s3_key, StorageClass=STORAGE_CLASS)
        upload_id = response['UploadId']
        print(f"Uploading: {file_path} → {bucket_name}/{s3_key} (UploadId: {upload_id})")

        # Upload file in parts
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

        # Complete multipart upload
        s3_client.complete_multipart_upload(
            Bucket=bucket_name,
            Key=s3_key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
        print(f"✅ Upload completed: {file_path} → {bucket_name}/{s3_key}")

    except Exception as e:
        print(f"❌ Error: {e}")
        if 'upload_id' in locals():
            s3_client.abort_multipart_upload(Bucket=bucket_name, Key=s3_key, UploadId=upload_id)
            print(f"⚠ Multipart upload aborted: {upload_id}")

def upload_folder(local_folder, bucket_name, s3_folder):
    """Recursively uploads all files from a local folder to S3 in alphanumeric order, maintaining the full folder structure."""
    
    root_folder_name = os.path.basename(local_folder)  # Extract the root folder name
    s3_root_path = f"{s3_folder}/{root_folder_name}"  # Include the root folder in S3

    # Ensure root folder exists in S3
    if not folder_exists_in_s3(bucket_name, s3_root_path):
        print(f"📁 Creating folder in S3: {s3_root_path}/")

    for root, dirs, files in os.walk(local_folder):
        # Sort folders and files in alphanumeric order
        dirs.sort()
        files.sort()

        for file in files:
            local_file_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_file_path, os.path.dirname(local_folder))  # Fix folder structure
            s3_key = f"{s3_folder}/{relative_path}".replace("\\", "/")  # Convert to S3 format

            upload_with_progress(local_file_path, s3_key, bucket_name)

if __name__ == '__main__':
    if not os.path.exists(LOCAL_FOLDER_PATH):
        print(f"❌ Folder {LOCAL_FOLDER_PATH} does not exist. Please check the path.")
    else:
        print(f"🚀 Uploading folder: {LOCAL_FOLDER_PATH} → s3://{BUCKET_NAME}/{S3_ROOT_FOLDER}")
        upload_folder(LOCAL_FOLDER_PATH, BUCKET_NAME, S3_ROOT_FOLDER)
