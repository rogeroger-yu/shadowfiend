from shadowfiend.api import hooks

app = {
    'root': 'shadowfiend.api.controllers.root.RootController',
    'modules': ['shadowfiend.api'],
    'debug': False,
    'hooks': [
        hooks.ContextHook(),
        hooks.RPCHook(),
    ],
}
