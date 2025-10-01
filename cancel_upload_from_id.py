import boto3

# Configuration
BUCKET_NAME = 'bucket-name' #Bucket Name
KEY = 'file-name'  # File name of upload
UPLOAD_ID = 'upload-id' #Upload ID

# Initialize the S3 client
s3_client = boto3.client('s3')

def abort_multipart_upload():
    try:
        s3_client.abort_multipart_upload(Bucket=BUCKET_NAME, Key=KEY, UploadId=UPLOAD_ID)
        print(f"Successfully aborted multipart upload for '{KEY}' in bucket '{BUCKET_NAME}'.")
    except Exception as e:
        print(f"Error aborting upload: {e}")

if __name__ == '__main__':
    abort_multipart_upload()
