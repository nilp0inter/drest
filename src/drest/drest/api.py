"""dRest core API connection library."""

from drest import interface, resource, request, serialization, meta, exc

class API(meta.MetaMixin):
    class Meta:
        baseurl = None
        request = request.RequestHandler
        resource = resource.RESTResourceHandler

    resources = []
    
    def __init__(self, baseurl=None, **kw):
        kw['baseurl'] = kw.get('baseurl', baseurl)
        super(API, self).__init__(**kw)        
        self._request = self._meta.request(baseurl=self._meta.baseurl)

    def auth(self, **kw):
        """
        In this implementation, we simply add any keywords passed to 
        self.extra_url_params so that they are passed along with each request
        in the url. For example, auth(user='john.doe', api_key='XXXXX').
                
        """
        for key in kw:
            self._request.add_url_param(key, kw[key])
            
    def request(self, method, path, params={}):
        return self._request.request(method, path, params)
        
    def add_resource(self, name, resource_handler=None, path=None):
        if not path:
            path = '%s' % name
        else:
            path = path.lstrip('/')
            
        if not resource_handler:
            handler = self._meta.resource
        else:
            handler = resource_handler
        
        handler = handler(baseurl=self._meta.baseurl, path=path, resource=name)
        
        resource.resource_validator(resource.IResource, handler)
        if hasattr(self, name):
            raise exc.dRestResourceError(
                "The object '%s' already exist on '%s'" % (name, self))
        setattr(self, name, handler)
        self.resources.append(name)
        
class TastyPieAPI(API):
    """
    This class implements an API client, specifically tailored for
    interfacing with `TastyPie <http://django-tastypie.readthedocs.org/en/latest`_.
    
    Authentication Mechanisms
    ^^^^^^^^^^^^^^^^^^^^^^^^^
    
    Currently the only supported authentication mechanizm is ApiKey.
    
    Usage
    ^^^^^
    
    Please note that the following example use ficticious resource data.  
    What is returned, and sent to the API is unique to the API itself.  Please
    do not copy and paste any of the following directly without modifying the
    request parameters per your use case.
    
    .. code-block:: python
    
        import drest
        api = drest.api.TastyPieAPI('http://localhost:8000/api/v0/')
        api.auth(user='john.doe', api_key='34547a497326dde80bcaf8bcee43e3d1b5f24cc9')
        
        # Get available resources (auto-detected by default)
        api.resources
        
        # Get all objects of a resource
        response, objects = api.users.get()
        
        # Get a single resource
        response, object = api.users.get(1)
        
        # Filter resources (per available TastyPie filtering options set)
        response, objects = api.users.get(icontains='admin')
        
        # Update a resource
        response, data = api.users.get(1)
        updated_data = data.copy()
        updated_data['first_name'] = 'John'
        updated_data['last_name'] = 'Doe'
        
        response, object = api.users.update(1, updated_data)
        
        # Create a resource
        user_data = dict(
                        username='john.doe',
                        password'oober-secure-password',
                        first_name='John',
                        last_name'Doe',
                        )
        response, data = api.users.create(1, user_data)
        
        # Delete a resource
        response, data = api.users.delete(1)
        
    """
    class Meta:
        request = request.TastyPieRequestHandler
        resource = resource.TastyPieResourceHandler
        auto_detect_resources = True
        auth_mech = 'api_key'
        auth_mechanizms = ['api_key']
        
    def __init__(self, baseurl=None, **kw):
        super(TastyPieAPI, self).__init__(baseurl, **kw)
        if self._meta.auto_detect_resources:
            self.find_resources()

    
    def auth(self, *args, **kw):
        """
        Authenticate the request, determined by Meta.auth_mech.  Arguments
        and Keyword arguments are just passed to the auth_mech function.
        
        """
        if self._meta.auth_mech in self._meta.auth_mechanizms:
            func = getattr(self, '_auth_via_%s' % self._meta.auth_mech)
            func(*args, **kw)
            
    def _auth_via_api_key(self, user, api_key, **kw):
        """
        This implementation adds an Authorization header for user/api_key
        per the `TastyPie Documentation <http://django-tastypie.readthedocs.org/en/latest/authentication_authorization.html>`_.
                        
        Required Arguments:
        
            user
                The API username.
                
            api_key
                The API Key of that user.
                
        """
        self._request.add_header('Authorization', 'ApiKey %s:%s' % (user, api_key))
    
    def find_resources(self):
        """
        Find available resources, and add them via add_resource().
        
        """
        response, data = self.request('GET', '/')
        for resource in data.keys():
            if resource not in self.resources:
                self.add_resource(resource)
    