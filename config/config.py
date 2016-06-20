# import config.config_default
import config_default

configs = config_default.configs


def merge(default, override):
    r = {}
    for k, v in default.items():
        if k in override:
            if isinstance(v, dict):
                r[k] = merge(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r


try:
    import config_override
    configs = merge(configs, config_override.configs)
except ImportError:
    pass
