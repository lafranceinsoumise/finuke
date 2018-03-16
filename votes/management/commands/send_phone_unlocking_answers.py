class Command(BaseCommand):
    help = 'Importer les demandes de déblocage'

    def add_arguments(self, parser):
        parser.add_argument('-o', '--output', type=FileType(mode='w'), default=self.stdout)

    def get_fields(self, body):
        requester_match = requester_re.search(body)
        voter_match = votant_re.search(body)

        if not requester_match or not voter_match:
            raise SkipException()

        return requester_match.group('email'), requester_match.group('nom'), voter_match.group(1)


