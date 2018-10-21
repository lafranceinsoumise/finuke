import json
import os
from tqdm import tqdm

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from django.conf import settings
from django.core.management import BaseCommand

from votes.models import VoterListItem


def actions(it):
    for voter in it:
        yield {
            "_id": voter.pk,
            "_op_type": "index",
            "_index": "voters",
            "_type": "voter",
            "_source": {
                "first_names": voter.first_names,
                "last_name": voter.last_name,
                "use_last_name": voter.use_last_name,
                "commune": voter.commune,
                "departement": voter.departement,
            }
        }


class Command(BaseCommand):
    def handle(self, *args, **options):
        es = Elasticsearch(hosts=[settings.ELASTICSEARCH_HOST])

        if es.indices.exists('voters'):
            es.indices.delete('voters')

        with open(os.path.join(os.path.dirname(__file__), '../../elasticsearch/index.json')) as f:
            index_config = json.load(f)

        es.indices.create('voters', body=index_config)

        qs = VoterListItem.objects.all()

        if settings.ENABLE_HIDING_VOTERS:
            qs = qs.filter(vote_status=VoterListItem.VOTE_STATUS_NONE)
        count = qs.count()

        bulk(es, tqdm(actions(qs.iterator()), desc="Indexing", total=count))
