from keystonemiddleware import auth_token


class AuthTokenMiddleware(auth_token.AuthProtocol):
    """A subclass of keystone auth_token middleware.

    It avoids authentication on public routes.
    """

    def __init__(self, app, conf, public_api_routes=[]):
        self._public_routes = public_api_routes
        super(AuthTokenMiddleware, self).__init__(app, conf)

    def __call__(self, env, start_response):
        # Strip the / from the URL if we're not dealing with '/'
        path = env.get('PATH_INFO').rstrip('/') or '/'

        if path in self._public_routes:
            return self._app(env, start_response)

        return super(AuthTokenMiddleware, self).__call__(env, start_response)

    @classmethod
    def factory(cls, global_config, **local_conf):
        public_routes = local_conf.get('acl_public_routes', '')
        public_api_routes = [path.strip() for path in public_routes.split(',')]

        def _factory(app):
            return cls(app, global_config, public_api_routes=public_api_routes)
        return _factory
