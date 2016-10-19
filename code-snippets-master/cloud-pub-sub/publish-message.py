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

import base64

from oauth2client.client import GoogleCredentials
from apiclient import discovery

PUBSUB_API_SCOPE = 'https://www.googleapis.com/auth/pubsub'

PROJECT_NAME = 'earth-is-a-strange-place'
TOPIC_NAME = 'habitable-planets'
SUBSCRIPTION_NAME = 'new-habitable-planets-notifier'


"""This sample code composes a signer object used to construct signed URLs
according to the specified params. In this the following test case,
a new object is created and uploaded to Datastore to be further read,
both through signed urls. Thus, note that no authorization mechanisms are
needed once the signed url is generated."""


def list_resource(request, resource_name, page_token=None):

    # List resources for project and page token. Retry once in case of failure
    response = request.list(project='projects/%s' % PROJECT_NAME,
                            pageToken=page_token).execute(num_retries=1)

    for resource in response[resource_name]:
        print resource

    # If the response has more results, execute next batch
    new_page_token = response.get('nextPageToken')
    if new_page_token:
        list_resource(request, resource_name, new_page_token)


def setupSystem(client):

    print '\n### Setup'

    # 1. Create new topic
    topic_uri = 'projects/%s/topics/%s' % (PROJECT_NAME, TOPIC_NAME)
    topic_response = client.projects().topics().create(
        name=topic_uri, body={}).execute()

    print 'Created topic - %s' % topic_response.get('name')

    # 2. Add a pull subscription to the topic
    subscription_uri = 'projects/%s/subscriptions/%s' % (
        PROJECT_NAME, SUBSCRIPTION_NAME)

    body = {'topic': topic_uri, 'ackDeadlineSeconds': 30}
    subscription_response = client.projects().subscriptions().create(
        name=subscription_uri, body=body).execute()

    print 'Created subscription - %s' % subscription_response.get('name')


def publishMessages(client):

    print '\n### Publish messages'

    message_data = base64.b64encode(
        'Kepler: Add another potentially habitable planet to my list!')

    # Create a POST body for the request Pub/Sub request
    body = {
        'messages': [{
            'data': message_data,
            'attributes':
            {
                'timestamp': '1749099512',
                'candidate_name': 'KOI-3284.01',
                'right_ascension': '18h 46m 35s',
                'declination': '+41deg 57m 3.93s',
                'telescope': 'Kepler'
            }
        }, {
            'data': message_data,
            'attributes':
            {
                'timestamp': '1749096501',
                'candidate_name': 'KOI-4742.01',
                'right_ascension': '19h 01m 27.98s',
                'declination': '+39deg 16m 48.30s',
                'telescope': 'Kepler'
            }
        }]
    }
    topic_uri = 'projects/%s/topics/%s' % (PROJECT_NAME, TOPIC_NAME)
    publish_response = client.projects().topics().publish(
        topic=topic_uri, body=body).execute()

    print 'Published 2 new planets with ids - %s' % publish_response.get(
        'messageIds')


def consumeMessages(client):

    print '\n### Consume messages'

    max_n_messages = 10
    subscription_uri = 'projects/%s/subscriptions/%s' % (
        PROJECT_NAME, SUBSCRIPTION_NAME)

    body = {
        # If returnImmediately is set to False, the request waits until
        # enough messages are added to the queue up to the maximum specified
        # or the request times out. Otherwise it returns immediately.
        'returnImmediately': True,
        'maxMessages': max_n_messages,
    }

    messages_response = client.projects().subscriptions().pull(
        subscription=subscription_uri, body=body).execute()

    received_messages = messages_response.get('receivedMessages')
    if received_messages is not None:
        ack_ids = []

        for message in received_messages:
            pubsub_message = message.get('message')

            if pubsub_message:

                data = base64.b64decode(str(pubsub_message.get('data')))
                attributes = pubsub_message.get('attributes')
                if attributes is not None:

                    print 'Processing habitable planet candidate: %s'
                    + attributes['candidate_name']

                    # Tasks to do:
                    #
                    # 1. Check if a planet with the same discovery timestamp
                    # and celestial coordinates (right_ascension | declination)
                    #  has been already stored and return if that is the case.
                    #
                    # 2. Store new planet candidate in your database
                    #
                    # 3. Notify the interested parties by email

                    # Append the acknowledgement id to the batch ack id list
                    ack_ids.append(message.get('ackId'))

        # Send acknowledgement for the messages processed succesfully
        ack_body = {'ackIds': ack_ids}
        client.projects().subscriptions().acknowledge(
            subscription=subscription_uri, body=ack_body).execute()


def cleanUp(client):

    print '\n### Clean up'

    # 1. Delete subscription
    subscription_uri = 'projects/%s/subscriptions/%s' % (
        PROJECT_NAME, SUBSCRIPTION_NAME)

    client.projects().subscriptions().delete(
        subscription=subscription_uri).execute()

    print 'Deleted subscription - %s' % subscription_uri

    # 2. Delete topic
    topic_uri = 'projects/%s/topics/%s' % (PROJECT_NAME, TOPIC_NAME)
    client.projects().topics().delete(topic=topic_uri).execute()
    print 'Deleted topic - %s\n' % topic_uri


def main():

    credentials = GoogleCredentials.get_application_default()

    # Alternatively you can load a custom JSON key
    # credentials = GoogleCredentials.from_stream(<path-to-json-key>)

    if credentials.create_scoped_required():
        credentials = credentials.create_scoped(PUBSUB_API_SCOPE)

    pubsub_client = discovery.build('pubsub', 'v1beta2',
                                    credentials=credentials)

    # 1. The system administrator sets up the system, creating a topic
    # and a subscription to track planets
    setupSystem(pubsub_client)

    # 2. The telescope publishes messages for planets found in the last 12 h
    publishMessages(pubsub_client)

    # 3. Your application processes the messages and acknowledges them
    consumeMessages(pubsub_client)

    # 4. The project is cleaned up
    cleanUp(pubsub_client)

if __name__ == '__main__':
    main()
