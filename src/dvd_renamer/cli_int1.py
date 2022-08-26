"""
DOCSTRING for first public console interface.

USAGE:
    dvd_rip_rename <basedir>
"""

from __future__ import print_function, unicode_literals
from dvd_renamer.libs import process_dvd, dvd_rewind
from pprint import pprint
from PyInquirer import prompt, print_json
from rich import print
from rich.console import Console
import argparse
import os


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', action='store',
                        dest='directory',
                        help='Directory to process')
    parser.add_argument('-i', '--ignore_main_feature', action='store_true',
                        dest='imf', default=False,
                        help='Ignore the main feature')
    parser.add_argument('-t', '--title_files_only', action='store_true',
                        dest='title_files', default=False,
                        help='Only process files with title_ in the name')
    args = parser.parse_args()
    return args


def full_process(args):
    """Do it."""
    console = Console()
    console.clear()
    dvd = process_dvd.Gather_DVD(args.directory)
    
    dvd.process_dir(args.imf, args.title_files)
    data = dvd.get_mkv_data()

    def header():
        console.clear()
        print("[bold green]DVD Name: ", dvd.guess_name())
        print("[bold green]Year:[/bold green] ", str(dvd.guess_year()))

    header()
    rewind = dvd_rewind.Lookup_Movie(dvd.guess_name(), dvd.guess_year())

    movie_found = rewind.search_for_movie()
    if not movie_found:
        questions = [
            {
                'type': 'input',
                'name': 'movie',
                'message': 'Movie Search name',
                'default': dvd.guess_name(),
            },
            {
                'type': 'input',
                'name': 'year',
                'message': 'Movie Search year (enter partial like 19 or 20 if unsure)',
                'default': str(dvd.guess_year()),
            },
        ]
        answers = prompt(questions)
        rewind = dvd_rewind.Lookup_Movie(answers['movie'], answers['year'])
        movie_found = rewind.search_for_movie()
    
    if movie_found:
        mlist = rewind.get_movie_list()
        nlist = ['Abort']
        for x in mlist:
            nlist.append(x['name'])
        questions = [
            {
                'type': 'rawlist',
                'name': 'movie',
                'message': 'Which Title?',
                'choices': nlist,
            },
        ]
        answers = prompt(questions)
        if answers['movie'] == 'Abort':
            print("Aborting.")
            return
        movie_url = rewind.get_url_for_movie(answers['movie'])

        rewind.process_movie(movie_url)

        extra_type = {
            'type': 'list',
            'name': 'type',
            'message': 'Extra type:',
            'choices': [
                'Featurettes',
                'Trailers',
                'Behind The Scenes',
                'Deleted Scenes',
                'Interviews',
                'Scenes',
                'Shorts',
                'Other',
                ],
            }

        for index, extra in enumerate(data):
            header()
            questions = [
                {
                    'type': 'list',
                    'name': 'extra',
                    'message': 'Select a title for this extra:',
                },
                extra_type,
            ]
            timestr = str(extra['minutes']) + ':' + str(extra['seconds']).zfill(2)
            print("[bold green]File:[/bold green] ", extra['filename'])
            print("[bold green]Length:[/bold green] ", timestr)
            choices = rewind.find_time_in_movie(timestr)
            choices.append('None of the above')
            answers = None
            if len(choices) > 1:
                questions[0]['choices'] = choices
                answers = prompt(questions)

            # try again with fuzzy match
            if answers is None or answers['extra'] == 'None of the above':
                print("[bold red] Trying a fuzzy match of time:")
                choices = rewind.find_fuzzy_time_in_movie(timestr)
                choices.append('None of the above')
                questions[0]['choices'] = choices
                if len(choices) > 1:
                    answers = prompt(questions)

            if answers is not None and answers['extra'] != 'None of the above':
                new_filename = args.directory + '/' + answers['type'] + '/' + answers['extra'] + '.mkv'
                data[index]['new_filename'] = new_filename
                data[index]['extra_type'] = answers['type']

        # pprint(data)
        header()
        rename = [ {
            'type': 'confirm',
            'name': 'doit',
            'message': 'Rename these files?',
            'default': False,
        } ]

        mkdir = [ {
            'type': 'confirm',
            'name': 'doit',
            'message': 'Make this directory?',
            'default': False,
        } ]
        
        # handle making directories
        header()
        for extra in data:
            if 'extra_type' in extra and not os.path.exists(args.directory + '/' + extra['extra_type']):
                print("[red]", args.directory + '/' + extra['extra_type'])
                answers = prompt(mkdir)
                if answers['doit']:
                    os.mkdir(args.directory + '/' + extra['extra_type'])

        # now rename files?
        header()
        for extra in data:
            if 'new_filename' not in extra:
                continue
            print('[red]Rename[/red] [green]{}[/green] to [magenta]{}[/magenta]'.format(extra['filename'], extra['new_filename']))
        print("[bold red on white]The following will modify your files!")
        print()
        answers = prompt(rename)

        # rename them
        if answers['doit']:
            for extra in data:
                if 'new_filename' in extra:
                    if os.path.exists(extra['new_filename']):
                        print("[red]Cowardly refusing to overwrite ",
                              extra['new_filename'])
                        continue
                    os.rename(extra['filename'], extra['new_filename'])
        print("[bold red]Files have been renamed.")

        # tell about unhandled files
        print("The following files could not be processed:")
        for extra in data:
            if 'new_filename' not in extra:
                timestr = str(extra['minutes']) + ':' + str(extra['seconds']).zfill(2)
                print(extra['filename'] + ' ' + timestr)

    # Movie not found.
    else:
        print("Could not find movie on http://dvdcompare.net/comparisons/")
        exit(1)

def main():
    args = parse_args()
    full_process(args)
