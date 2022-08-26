DVD Renamer
===========

.. image:: https://github.com/garbled1/dvd_renamer/workflows/ci/badge.svg?branch=main
    :target: https://github.com/garbled1/dvd_renamer/actions?workflow=ci
    :alt: CI

.. image:: https://img.shields.io/readthedocs/dvd_renamer/latest?label=Read%20the%20Docs
    :target: https://dvd_renamer.readthedocs.io/en/latest/index.html
    :alt: Read the Docs

Summary
-------
After you use the Automatic Ripping Machine to process your favorite blu-ray or
dvd movie, you now have a bunch of files in Featurettes named title_1234.mkv or
similar.  This is obnoxious.

http://dvdcompare.net/ is a pretty awesome resource to lookup a dvd, and find all
the extras.  Often, they list titles for all the little extras, as well as
time lengths.  In the past, I would manually lookup lengths, and then use that
to rename the files.  This is also obnoxious.

This program will take a directory of your movie, and try to match the times,
and rename the files for you.  This is better.

Oh, naming convention is for Plex.  Sorry.


Motivation
----------

Laziness

Acknowledgments
---------------
Probably?


How to use this tool
--------------------

'''python3 ./setup.py install'''
dvd_rip_rename -i -d /video/arm_media/completed/movies/GoldenEye\ \(1995\)

'''
.. image::demo.gif


Issues and Discussions
----------------------

As usual for any GitHub-based project, raise an `issue`_ if you find any bug or
want to suggest an improvement, or open a `discussion`_ if you want to discuss
or chat :wink:


Version
-------

v0.1.0

.. _First effort
