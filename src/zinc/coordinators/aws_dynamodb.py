# # get a reference to the DynamoDB resource
# dynamodb_resource = boto3.resource('dynamodb')
#
# # create the lock-client
# lock_client = DynamoDBLockClient(dynamodb_resource)
#
# ...
#
# # close the lock_client
# lock_client.close()


from urllib.parse import urlparse
import boto3
from python_dynamodb_lock.python_dynamodb_lock import DynamoDBLockClient
from typing import Optional
import logging
from . import CatalogCoordinator, LockException

log = logging.getLogger(__name__)


class Lock(object):
    def __init__(self, lock_client: DynamoDBLockClient, key: str, **kwargs):
        self._lock_client = lock_client
        self._key = key
        self._lock = None

    def acquire(self):
        if self.is_locked():
            return

        self._lock = self._lock_client.acquire_lock(self._key)

    def is_locked(self):
        return self._lock is not None

    def release(self):
        if self._lock is not None:
            self._lock.release()
            self._lock = None


class DynamoDBCatalogCoordinator(CatalogCoordinator):

    def __init__(self, url: Optional[str] = None,
                 aws_key: Optional[str] = None,
                 aws_secret: Optional[str] = None,
                 lock_client: Optional[DynamoDBLockClient] = None,
                 **kwargs):
        super(DynamoDBCatalogCoordinator, self).__init__(**kwargs)

        assert lock_client or (aws_key and aws_secret)

        if lock_client:
            self._lock_client = lock_client
        else:
            urlcomps = urlparse(url)
            region = urlcomps.netloc
            # domain = urlcomps.path[1:]  # strip leading /
            # if domain == '':
            #     domain = 'zinc'

            try:
                client = boto3.client('dynamodb',
                                      region_name=region,
                                      aws_access_key_id=aws_key,
                                      aws_secret_access_key=aws_secret)
                DynamoDBLockClient.create_dynamodb_table(client)
            except client.exceptions.ResourceInUseException:
                log.debug('Unable to create table, assuming it already exists')

            dynamodb_resource = boto3.resource('dynamodb',
                                               region_name=region,
                                               aws_access_key_id=aws_key,
                                               aws_secret_access_key=aws_secret)
            self._lock_client = DynamoDBLockClient(dynamodb_resource)

    #def __del__(self):
    #    if self._lock_client is not None:
    #        self._lock_client.close()

    def get_index_lock(self, domain: Optional[str] = None,
                       timeout: Optional[int] = None, **kwargs) -> Lock:
        assert domain
        return Lock(lock_client=self._lock_client, key=domain)

    @classmethod
    def valid_url(cls, url: str) -> bool:
        urlcomps = urlparse(url)
        return urlcomps.scheme == 'dynamodb'  # and urlcomps.netloc in [r.name for r in boto.sdb.regions()]
