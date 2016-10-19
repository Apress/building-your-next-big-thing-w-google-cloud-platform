# Copyright 2015 Google Cloud Platform Book ISBN - 978-1-4842-1005-5
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from oauth2client.client import GoogleCredentials
from apiclient.discovery import build

CLOUD_STORAGE_SCOPE = 'https://www.googleapis.com/auth/devstorage.read_only'


def main():

    # 1. Load credentials from default account
    credentials = GoogleCredentials.get_application_default()

    # Alternatively you can load a custom JSON key
    # credentials = GoogleCredentials.from_stream(<path-to-json-key>)

    if credentials.create_scoped_required():
        credentials = credentials.create_scoped(CLOUD_STORAGE_SCOPE)

    # If you want to generate and show the current access token:
    # from httplib2 import Http
    # credentials._refresh(Http().request)
    # print credentials.access_token

    # 2. Access API using apiclient.discovery
    gcs_service = build('storage', 'v1', credentials=credentials)
    content = gcs_service.objects().list(
        bucket='lunchmates_document_dropbox').execute()

    print json.dumps(content)


if __name__ == '__main__':
    main()
