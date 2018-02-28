import csv
from operator import itemgetter

from os import path

departements = [{
    'code': dep['CodeDept'],
    'name': dep['NomDeptEnr'],
    'state': dep['NivDetail']
} for dep in csv.DictReader(open(path.join(path.dirname(__file__), 'departements.csv')), delimiter=';')]

communes = [{
    'code': c['CodeINSEE'],
    'dep': c['CodeDept'],
    'name': c['NomCommuneEnr']
} for c in csv.DictReader(open(path.join(path.dirname(__file__), 'communes.csv')), delimiter=';')]

communes_names = dict(map(itemgetter('code', 'name'), communes))