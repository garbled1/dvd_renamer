"""
DOCSTRING for first public console interface.

USAGE:
    dvd_rip_rename <basedir>
"""

from __future__ import print_function, unicode_literals
from dvd_renamer.libs import process_dvd, dvd_rewind
from pprint import pprint
from prompt_toolkit.validation import Validator, ValidationError
from PyInquirer import prompt, print_json
from rich import print
from rich.console import Console
import argparse
import os
import re


q_rename = [
    {
        'type': 'confirm',
        'name': 'doit',
        'message': 'Rename these files?',
        'default': False,
    }
]

q_mkdir = [
    {
        'type': 'confirm',
        'name': 'doit',
        'message': 'Make this directory?',
        'default': False,
    }
]


class NumberValidator(Validator):
    def validate(self, document):
        try:
            int(document.text)
        except ValueError:
            raise ValidationError(
                message='Please enter a number',
                cursor_position=len(document.text))  # Move cursor to end


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', action='store',
                        dest='directory',
                        help='Directory to process')
    parser.add_argument('-i', '--ignore_main_feature', action='store_true',
                        dest='imf', default=False,
                        help='Ignore the main feature in the base directory')
    parser.add_argument('-t', '--title_files_only', action='store_true',
                        dest='title_files', default=False,
                        help='Only process files with title_ in the name')
    parser.add_argument('-s', '--series', action='store_true',
                        dest='series', default=False,
                        help='Process this as a series not a movie')
    parser.add_argument('-m', '--manual', action='store_true',
                        dest='manual', default=False,
                        help='Skip lookup, process manually (series only)')
    args = parser.parse_args()
    return args


def mkdir_maybe(dirname):
    """Confirm then make directory."""

    if not os.path.exists(dirname):
        print("[red]", dirname)
        answers = prompt(q_mkdir)
        if answers['doit']:
            os.mkdir(dirname)


def unhandled_files(data):
    """Show which files could not be handled."""

    print("The following files could not be processed:")
    for extra in data:
        if 'new_filename' not in extra:
            timestr = str(extra['minutes']) + ':' + str(extra['seconds']).zfill(2)
            print(extra['filename'] + ' ' + timestr)

def show_files_to_rename(data):
    """Show which files will be renamed."""

    for episode in data:
        if 'new_filename' not in episode:
            continue
        print('[red]Rename[/red] [green]{}[/green] to [magenta]{}[/magenta]'.format(episode['filename'], episode['new_filename']))


def rename_files(data):
    """Rename all the files."""

    print("[bold red on white]The following will modify your files!")
    print()
    answers = prompt(q_rename)

    # rename them
    if answers['doit']:
        for episode in data:
            if 'new_filename' in episode:
                if os.path.exists(episode['new_filename']):
                    print("[red]Cowardly refusing to overwrite ",
                          episode['new_filename'])
                    continue
                os.rename(episode['filename'], episode['new_filename'])
        print("[bold red]Files have been renamed.")
    else:
        print("[bold green]Skipped renaming of files.")
    print()


def attempt_item_match(rewind, questions, extra, extra_name, add_time):
    """Try to match this item to something from the web."""

    timestr = str(extra['minutes']) + ':' + str(extra['seconds']).zfill(2)
    print("[bold green]File:[/bold green] ", extra['filename'])
    print("[bold green]Length:[/bold green] ", timestr)
    choices = rewind.find_time_in_movie(timestr, add_time)
    choices.append('None of the above')
    answers = None
    if len(choices) > 1:
        questions[0]['choices'] = choices
        answers = prompt(questions)

    # try again with fuzzy match
    if answers is None or answers[extra_name] == 'None of the above':
        print("[bold red] Trying a fuzzy match of time:")
        choices = rewind.find_fuzzy_time_in_movie(timestr, add_time)
        choices.append('None of the above')
        questions[0]['choices'] = choices
        if len(choices) > 1:
            answers = prompt(questions)

    return answers


def full_process_series(args):
    """Process a series."""
    season = 1
    specials = 100
    if args.manual:
        series_found = True
    else:
        series_found = False
    have_special = False
    used_ep = []
    series_name = ""

    console = Console()
    console.clear()
    dvd = process_dvd.Gather_DVD(args.directory)

    dvd.process_dir(args.imf, args.title_files)
    data = dvd.get_mkv_data()

    def header():
        console.clear()
        print("[bold green]DVD Name: ", dvd.guess_name())
        print("[bold green]Year:[/bold green] ", str(dvd.guess_year()))
        print(f"[bold green]Season: {season}")
        print("[bold green]Episodes assigned: ", used_ep)
        print("")

    questions = [
        {
            'type': 'input',
            'name': 'series',
            'message': 'Series Search name (blank to give up)',
            'default': dvd.guess_name(),
        },
        {
            'type': 'input',
            'name': 'year',
            'message': 'Series Search year (enter partial like 19 or 20 if unsure)',
            'default': str(dvd.guess_year()),
        },
        {
            'type': 'input',
            'name': 'season',
            'message': 'Season number',
            'validate': NumberValidator,
            'filter': lambda val: int(val),
        },
    ]
    while not series_found:
        answers = prompt(questions)
        if answers['series'] == "":
            print("Giving up")
            return 1
        season = answers['season']
        rewind = dvd_rewind.Lookup_Movie(answers['series'], answers['year'])
        series_found = rewind.search_for_movie()

        if series_found:
            mlist = rewind.get_movie_list()
            nlist = ['None of the below']
            for x in mlist:
                nlist.append(x['name'])
                ser_questions = [
                    {
                        'type': 'list',
                        'name': 'series',
                        'message': 'Which Title?',
                        'choices': nlist,
                    },
                ]
            ser_answers = prompt(ser_questions)
            if ser_answers['series'] == 'None of the below':
                print("Not found, searching again.")
                series_found = False

    if not series_found:
        return 1

    # if doing manual mode, we skip the above, and ask slightly differently
    if args.manual:
        questions[0]['message'] = 'Series Name'
        questions[1]['message'] = 'Series Year'
        answers = prompt(questions)
        season = answers['season']

    series_name = answers['series']
    final_dir = args.directory
    if final_dir[-1] == '/':
        final_dir = final_dir[:-1]
    final_dir = '/'.join(final_dir.split('/')[:-1])
    if final_dir == '':
        final_dir = '.'
    final_dir = final_dir + '/' + answers['series'] + ' (' + str(answers['year']) + ')'

    fd_questions = [
        {
            'type': 'input',
            'name': 'final_dir',
            'message': 'Final directory to place files in (blank to process in-place)',
            'default': final_dir,
        }
    ]
    fd_answers = prompt(fd_questions)
    if fd_answers['final_dir'] == '':
        final_dir = args.directory
    else:
        final_dir = fd_answers['final_dir']

    if not args.manual:
        series_url = rewind.get_url_for_movie(ser_answers['series'])
        rewind.process_movie(series_url)
    specials = season * 100
    cur_ep = 0

    for index, episode in enumerate(data):
        header()
        questions = [
            {
                'type': 'list',
                'name': 'ep_title',
                'message': 'Select a title for this episode:',
            },
            {
                'type': 'input',
                'name': 'ep_number',
                'message': 'Episode number (0 for extra/special)',
                'validate': NumberValidator,
                'filter': lambda val: int(val),
                'default': str(cur_ep + 1),
            },
        ]
        if args.manual:
            questions[0] = {
                'type': 'input',
                'name': 'ep_title',
                'message': 'Title for this episode (enter SKIP to skip)',
            }
            timestr = str(episode['minutes']) + ':' + str(episode['seconds']).zfill(2)
            print("[bold green]File:[/bold green] ", episode['filename'])
            print("[bold green]Length:[/bold green] ", timestr)
            answers = prompt(questions)
        else:
            answers = attempt_item_match(rewind, questions, episode, 'ep_title', True)

        if (answers is not None and answers['ep_title'] != 'None of the above'
            and answers['ep_title'] != 'SKIP'):
            fixed_ep_title = re.sub(re.compile('\(.*\)'), '', answers['ep_title'])
            if answers['ep_number'] == 0:
                have_special = True
                sp_questions = [
                    {
                        'type': 'input',
                        'name': 'ep_number',
                        'message': 'Episode number for this special',
                        'validate': NumberValidator,
                        'filter': lambda val: int(val),
                        'default': str(specials + 1),
                    },
                ]
                sp_answers = prompt(sp_questions)
                if sp_answers['ep_number'] == (specials + 1):
                    specials = specials + 1
                elif sp_answers['ep_number'] > specials:
                    specials = sp_answers['ep_number'] + 1

                ep_str = str(sp_answers['ep_number']).zfill(2)
                if sp_answers['ep_number'] > 99:
                    ep_str = str(sp_answers['ep_number']).zfill(3)
                if sp_answers['ep_number'] > 999:
                    ep_str = str(sp_answers['ep_number']).zfill(4)
                new_filename = final_dir + '/' + 'Season 00' + '/' + 'S00E' + ep_str + ' - ' + fixed_ep_title + '.mkv'

            # non special
            else:
                used_ep.append(answers['ep_number'])
                cur_ep = answers['ep_number']
                new_filename = final_dir + '/' + 'Season ' + str(season).zfill(2) + '/' + 'S' + str(season).zfill(2) + 'E' + str(answers['ep_number']).zfill(2) + ' - ' + fixed_ep_title + '.mkv'
            data[index]['new_filename'] = new_filename


    # pprint(data)
    header()

    # handle making directories
    mkdir_maybe(final_dir)
    if have_special:
        spdir_str = final_dir + '/' + 'Season 00'
        mkdir_maybe(spdir_str)

    sdir_str = final_dir + '/' + 'Season ' + str(season).zfill(2)
    mkdir_maybe(sdir_str)

    # now rename files?
    header()
    show_files_to_rename(data)

    # rename them
    rename_files(data)

    # tell about unhandled files
    unhandled_files(data)


def full_process_movie(args):
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
            return 1
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
            answers = attempt_item_match(rewind, questions, extra, 'extra', False)

            if answers is not None and answers['extra'] != 'None of the above':
                new_filename = args.directory + '/' + answers['type'] + '/' + answers['extra'] + '.mkv'
                data[index]['new_filename'] = new_filename
                data[index]['extra_type'] = answers['type']

        # pprint(data)
        header()
        
        # handle making directories
        header()
        for extra in data:
            if 'extra_type' in extra:
                edir = args.directory + '/' + extra['extra_type']
                mkdir_maybe(edir)

        # now rename files?
        header()
        show_files_to_rename(data)

        # rename them
        rename_files(data)

        # tell about unhandled files
        unhandled_files(data)

    # Movie not found.
    else:
        print("Could not find movie on http://dvdcompare.net/comparisons/")
        exit(1)

def main():
    args = parse_args()
    if not args.series:
        full_process_movie(args)
    else:
        full_process_series(args)

