# -*- coding: utf-8 -*-
import db
import click
import ckan.plugins.toolkit as tk


@click.command() 
def featuredmigrate(self):
    if not db.featured_table.exists():
        db.featured_table.create()
    else:
        print 'Featured Views table already exists'
    return [featuredmigrate]


def get_commands():
    return [featuredmigrate]