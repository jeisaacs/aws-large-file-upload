import boto3

# Configuration
BUCKET_NAME = 'synology01-backup-video'  # Bucket Name
PREFIX = ''  # Prefix or part of the key name

# Initialize the S3 client
s3_client = boto3.client('s3')

def list_multipart_uploads():
	try:
		response = s3_client.list_multipart_uploads(Bucket=BUCKET_NAME)
		
		uploads = response.get('Uploads', [])
		if not uploads:
			print("No multipart uploads found for the specified prefix.")
			return
		
		print("Active Multipart Uploads:")
		for upload in uploads:
			print(f"Key: {upload['Key']}, Upload ID: {upload['UploadId']}")
			
	except Exception as e:
		print(f"An error occurred: {e}")
		
if __name__ == '__main__':
	list_multipart_uploads()
	