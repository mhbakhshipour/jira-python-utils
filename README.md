# Jira Python Utils

## Installation
Just copy and paste in your projects as a helper!

## Usage
Here's a simple example of how to use the Jira class to create a ticket in JIRA in django views:
`
from rest_framework import viewsets
from core.local_settings import env

class MHBPViewSet(viewsets.ModelViewSet):
    ...
    def perform_create(self, serializer):
        super().perform_create(serializer)
        if env != "development":
            data = {"id": obj.id, "product_id": obj.product.product_id, "name": obj.name}
            jira_a_instance = Jira(self.request, Source.A)
            issue_key = jira_a_instance.create_ticket(data)
`

## Contributing
Contributions are welcome! If you find a bug or have a feature request, please open an issue on the GitHub/GitLab repository.
