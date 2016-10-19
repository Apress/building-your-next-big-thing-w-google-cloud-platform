# Code Snippets in "Building your Next Big Thing with Google Cloud Platform"
This repository supports the content explained in the different chapters of the book [Building your Next Big Thing with Google Cloud Platform] (http://www.amazon.com/Building-Thing-Google-Cloud-Platform/dp/1484210050).
It contains snippets of code that illustrate how to operate some services in [Google Cloud Platform](https://cloud.google.com/). Use these routines to learn about the services in Google Cloud Platform and how to operate them in your client, web application or continuous integration tools.

Note that the content of this repository will change as services in Google Cloud Platform are developed and improved. Your contributions are more than welcome, even necessary. Also, feel free to add completely new test cases or services.

This is the current list of snippets that you can find in this repository:

Service                                                | Folder         | Sample Command
------------------------------------------------------ | -------------- | -----
Cloud Storage                                          | cloud-storage  | `python signed-urls.py`
Any service using OAuth 2.0 Application Authentication | oauth2         | `python api_access_application_authentication.py`
Cloud Dataflow                                         | cloud-dataflow | `./gradlew run -Pargs="--project=<project-id> --runner=BlockingDataflowPipelineRunner --stagingLocation=<location-staging-files>"`
Cloud Pub/Sub                                          | cloud-pub-sub  | `python publish-message.py`
