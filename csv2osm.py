#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

""" Simple script to convert source Mali Schools CSV to OSM XML """

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import sys
import datetime

import unicodecsv as csv

xml_head = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<osm version="0.6" generator="Custom">\n'
            '<bounds minlat="54.0889580" minlon="12.2487570" '
            'maxlat="54.0913900" maxlon="12.2524800"/>\n')

xml_tail = '</osm>\n'

node_tmpl = '<node id="{id}" version="1" changeset="12370172" ' \
            'lat="{lat}" lon="{lon}" user="Open Data Mali" ' \
            'uid="2306601" visible="true" timestamp="{timestamp}">\n' \
            '{tags}\n' \
            '</node>'


def getTag(key, value):
    return '<tag k="{key}" v="{value}"/>'.format(key=key, value=value)


def getTags(**tags):
    return "\n".join([getTag(key, value) for key, value in tags.items()])


def getTimestamp():
    return datetime.datetime.now().isoformat().split('.')[0] + 'Z'


def yesno(cond):
    return 'yes' if cond else 'no'


def clean(s):
    return s.strip().replace('"', "'").replace('&uml;', 'è')


def getNode(entry, lnum):

    # Schools are `1er cycle` or `2ème cycle`
    cycle = 1 if entry.get('CYCLE') == "1er cycle" else 2
    has_latrines = entry.get('PRESENCE_LATRINES') == '1'
    has_girl_latrines = entry.get('LATRINES_FILLES_SEPAREES') == '1'
    nb_latrines = int(entry.get('NOMBRE_LATRINES')) \
        if entry.get('NOMBRE_LATRINES') else 0
    nb_teachers = int(entry.get('NBRE ENSEIGNANTS')) \
        if entry.get('NBRE ENSEIGNANTS') else None

    statuses = {
        "Communautaire": "community",
        "Medersa": "private_religious",
        "Privé confessionnel": "private_religious",
        "Privé laïc": "private_laic",
        "Public": "public"
    }

    water_options = {
        "1) robinet ": "tap",
        "2) forage fonctionnel": "working_drilling",
        "3) puits non tarrissable": "inexhaustible_well",
        "4) puits tarrissable": "exhaustible_well",
        "5) pas de point d'eau": "no_water_point",
        "indeterminé": "unknown",
        "": "unknown"
    }

    water_point = water_options.get(entry.get('EAU_POTABLE'))
    has_drinkable_water = water_point in [
        'tap', 'working_drilling', 'inexhaustible_well', 'exhaustible_well']

    # status are `Communautaire` or `Medersa` or `Privé confessionnel`
    # or `Privé laïc` or `Public`

    tags = {
        'amenity': 'school',
        'name': clean(entry.get('NOM_ETABLISSEMENT')),
        'operator_type': statuses.get(entry.get('STATUT')),

        # school classification
        'school:ML:academie': entry.get('AE'),
        'school:ML:cap': entry.get('CAP'),

        'school:fondamental_first_cycle': yesno(cycle == 1),
        'school:fondamental_second_cycle': yesno(cycle == 2),

        # Students
        'school:nb_schoolboys_2012': int(entry.get('GARCONS')),
        'school:nb_schoolgirls_2012': int(entry.get('FILLES')),
        'school:nb_pupils_2012': int(entry.get('TOTAL')),

        'school:has_drinkable_water': yesno(has_drinkable_water),

        'school:has_restaurant':
            yesno(entry.get('PRESENCE_RESTAURANT') == '1'),
        'school:has_latrines': yesno(has_latrines),
        'school:nb_latrines': nb_latrines,
    }
    # admin levels of Mali
    if entry.get('Région'):
        tags.update({'is_in:region': clean(entry.get('Région'))})
    if entry.get('Cercle'):
        tags.update({'is_in:cercle': clean(entry.get('Cercle'))})
    if entry.get('Commune'):
        tags.update({'is_in:commune': clean(entry.get('Commune'))})
    if entry.get('Localites'):
        tags.update({'is_in:village': clean(entry.get('Localites'))})

    # School code
    if entry.get('CODE_ETABLISSEMENT'):
        tags.update({'school:ML:code': entry.get('CODE_ETABLISSEMENT')})

    if has_latrines:
        tags.update({'school:has_separated_girls_latrines':
                     yesno(has_girl_latrines)})

    if has_drinkable_water:
        tags.update({'school:water_point_type': water_point})

    if nb_teachers is not None:
        tags.update({'school:nb_teachers_2012': nb_teachers})

    data = {
        'tags': getTags(**tags),
        'id': -lnum,
        'changeset': -lnum,
        'lat': entry.get('Y'),
        'lon': entry.get('X'),
        'timestamp': getTimestamp()
    }
    return node_tmpl.format(**data)


def main(filename):
    headers = ['Région', 'AE', 'CAP', 'Cercle', 'Commune',
               'NOM_ETABLISSEMENT', 'Localites', 'X', 'Y',
               'CODE_ETABLISSEMENT', 'Localisation', 'CYCLE',
               'STATUT', 'PRESENCE_RESTAURANT', 'PRESENCE_LATRINES',
               'LATRINES_FILLES_SEPAREES', 'NOMBRE_LATRINES',
               'EAU_POTABLE', 'GARCONS', 'FILLES', 'TOTAL',
               'NBRE ENSEIGNANTS']
    input_csv_file = open(filename, 'r')
    csv_reader = csv.DictReader(input_csv_file, fieldnames=headers)
    output_osm_file = open('MLI_schools.osm', 'w')

    output_osm_file.write(xml_head)

    for entry in csv_reader:

        if csv_reader.line_num == 1:
            continue

        # don't export data without coordinates
        if not entry.get('X') or not entry.get('Y'):
            continue

        print(entry.get('NOM_ETABLISSEMENT'))

        school_node = getNode(entry, csv_reader.line_num)
        output_osm_file.write(school_node.encode('utf-8'))
        output_osm_file.write('\n')

    output_osm_file.write(xml_tail)

    output_osm_file.close()
    input_csv_file.close()

    print("Export complete.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("You must pass the MLI_schools.csv path")
        sys.exit(1)
    main(sys.argv[1])
