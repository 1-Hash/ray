import webapp2, json
from endpoint import EndpointHandler
from login import LoginHandler, LogoutHandler
from actions import ActionAPI
from . import exceptions, http


def to_json(fnc):
    def inner(*args, **kwargs):
        response = args[0].response
        response.status = 200
        response.headers['Content-Type'] = 'application/json'
        from_func = fnc(*args, **kwargs)

        result = json.dumps({'result': from_func})
        return response.out.write(result)

    return inner


class ApiHandler(webapp2.RequestHandler):
    """
        This class is the beginning of all entrypoint in the Ray API. Here, each url
        will be redirect to the right handler: ActionHandler, LoginHandler or EndpointHandler.
    """

    @to_json
    def dispatch(self):
        url = self.request.path
        if url[-1] == '/':
            url = url[:-1]

        try:
            return self.process(url)
        except (exceptions.MethodNotFound, exceptions.ActionDoNotHaveModel, exceptions.ModelNotFound) as e:
            self.response.status = 404
        except (exceptions.Forbidden, exceptions.NotAuthorized) as e:
            self.response.status = 403
        except Exception as e:
            raise e
        else:
            self.response.status = 500

    def process(self, fullpath):
        if self.is_login(fullpath):
            return LoginHandler(self.request, self.response, fullpath).process()

        if self.is_logout(fullpath):
            return LogoutHandler(self.response).logout()

        elif self.is_endpoint(fullpath):
            return EndpointHandler(self.request, fullpath).process()

        elif self.is_action(fullpath):
            return self.__handle_action(fullpath)

        else:
            self.response.status = 404

    def __handle_action(self, url):
        # url e.g: /api/user/123/action

        arg = None
        if len(url.split('/')) >= 5:  # indicatest that has an id between endpoint and action_name
            arg = http.param_at(url, -2)

        return ActionAPI(url, arg, self.request).process_action()

    def is_login(self, full_path):
        return full_path == '/api/_login'

    def is_logout(self, full_path):
        return full_path == '/api/_logout'

    def is_endpoint(self, full_path):
        full_path = full_path.split('?')[0]
        if len(full_path.split('/')) == 4:
            try:
                int(full_path.split('/')[-1])
                return True
            except:
                return False

        return len(full_path.split('/')) <= 4 and len(full_path.split('/')) > 2

    def is_action(self, full_path):
        # full_path e.g: /api/user/123/action
        # full_path e.g: /api/user/action

        if len(full_path.split('/')) >= 4:
            try:
                int(full_path.split('/')[-1])
            except:
                return True

        return len(full_path.split('/')) == 5
