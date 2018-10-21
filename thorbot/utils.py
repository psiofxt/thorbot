from functools import wraps


def config_chat_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        update = args[2].to_dict() if not isinstance(args[2], dict) else args[2]
        chat_id = update['message']['chat']['id']
        if int(chat_id) != int(args[0].config.group_id):
            return
        f(*args, **kwargs)
    return wrapper


def admin_only():
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            update = args[2].to_dict() if not isinstance(args[2], dict) else args[2]
            user_id = update['message']['from']['id']
            if user_id not in args[0].config.admin_ids:
                return
            f(*args, **kwargs)
        return wrapper
    return decorator


def exempt_admins():
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            update = args[2].to_dict() if not isinstance(args[2], dict) else args[2]
            user_id = update['message']['from']['id']
            if user_id in args[0].config.admin_ids:
                return
            f(*args, **kwargs)
        return wrapper
    return decorator
