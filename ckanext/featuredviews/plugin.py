import db
import actions
import ckan.model as model
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.dictization.model_dictize as md

from ckan.lib.dictization import table_dictize

from ckanext.featuredviews.cli import get_commands

try:
    from ckan.common import config
except ImportError:
    from pylons import config

class FeaturedviewsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    plugins.implements(plugins.IConfigurable, inherit=True)
    plugins.implements(plugins.IClick)

    #IClick for CKAN 2.9+
    def get_commands(self):
        """Call me via: `ckan featuredmigrate`"""
        return get_commands()
            

    # IConfigurable
    def configure(self, config):
        if model.repo.are_tables_created() and not db.featured_table.exists():
            db.featured_table.create()

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'featured')

    def get_actions(self):
        actions_dict = {
            'featured_create': actions.featured_create,
            'featured_show': actions.featured_show,
            'featured_upsert': actions.featured_upsert
        }
        return actions_dict

    def get_helpers(self):
        helpers = {
            'get_featured_view': _get_featured_view,
            'get_canonical_resource_view': _get_canonical_view,
            'get_homepage_resource_views': _get_homepage_views,
            'display_homepage_views': _display_homepage_views
        }
        return helpers

def _get_featured_view(resource_view_id):
    if not resource_view_id:
        return None

    featured = db.Featured.get(resource_view_id=resource_view_id)

    return featured

def _get_canonical_view(package_id):
    canonical_view_ids = [
        view.resource_view_id for view in db.Featured.find(package_id=package_id, canonical=True).all()
    ]

    if not canonical_view_ids:
        return None

    resource_views = model.Session.query(model.ResourceView).filter(
        model.ResourceView.id.in_(canonical_view_ids)
    ).all()

    if resource_views is None:
        return None
    
    for view in resource_views:
        resource_view = md.resource_view_dictize(view, {'model': model})
        resource_obj = model.Resource.get(resource_view['resource_id'])

        if resource_obj.state == 'deleted':
            continue

        resource = md.resource_dictize(resource_obj, {'model': model})

        return {'resource': resource, 'resource_view': resource_view}

    return None

def _get_homepage_views():
    homepage_view_ids = [
        view.resource_view_id for view in db.Featured.find(homepage=True).all()
    ]

    resource_views = model.Session.query(model.ResourceView).filter(
        model.ResourceView.id.in_(homepage_view_ids)
    ).all()

    homepage_views = []
    for view in resource_views:
        resource_view = md.resource_view_dictize(view, {'model': model})
        resource_obj = model.Resource.get(resource_view['resource_id'])
        
        if resource_obj.state == 'deleted':
            continue
        
        resource = md.resource_dictize(resource_obj, {'model': model})

        homepage_views.append({
            'resource_view': resource_view,
            'resource': resource,
            'package': md.package_dictize(resource_obj.package, {'model':model})
        })

    return homepage_views

def _display_homepage_views():
    return toolkit.asbool(config.get('ckanext.homepage_views', 'False'))
