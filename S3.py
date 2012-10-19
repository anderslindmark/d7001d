from boto.s3.connection import Location
from boto.s3.connection import S3Connection
from boto.exception import BotoClientError
from boto.exception import S3ResponseError
from boto.s3.key import Key
from boto.s3.lifecycle import Lifecycle
import aws_common
import sys


# Creates a file in the bucket, returns a url
def uploadFile(filename, content):
	object = Key(bucket)
	object.key = aws_common.S3_RESPONSE_PREFIX + filename
	object.set_contents_from_string(content)

	url = object.generate_url(expires_in=60*30)
	print "url: %s" % url
	return url

# Add a lifecycle-rule for automatic deletion
def setDeletionPolicy(bucket):
	lifecycle = Lifecycle()
	lifecycle.add_rule("Audo-delete objects in %s after 1 day" % aws_common.S3_RESPONSE_PREFIX, aws_common.S3_RESPONSE_PREFIX, "Enabled", 1)
	print "Added deletion policy"
	bucket.configure_lifecycle(lifecycle)

# Creates the bucket
def createBucket(bucketname):
	try:
		bucket = connection.create_bucket(bucketname, location=aws_common.S3_LOCATION)
		print "Bucket created"
		setDeletionPolicy(bucket)
		return bucket
	except S3ResponseError as error:
		# Bucket cant be created
		print error
		return None

# Initialize s3-connection and get bucket
connection= S3Connection(aws_common.AWS_ACCESS_KEY, aws_common.AWS_SECRET_KEY)
try:
	bucket = connection.get_bucket(aws_common.S3_BUCKET_NAME)
except S3ResponseError:
	bucket = createBucket(aws_common.S3_BUCKET_NAME)
	if bucket is None:
		print "Could not create bucket"
		sys.exit()

if __name__ == "__main__":
	print "Helloes"

