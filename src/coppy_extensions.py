import re
import subprocess
import unicodedata

import jinja2
from jinja2.ext import Extension


def git_user_name() -> str:
    return subprocess.getoutput('git config user.name').strip()


def git_user_email() -> str:
    return subprocess.getoutput('git config user.email').strip()


def slugify(value, separator='-'):
    value = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-_\s]+', separator, value).strip('-_')


@jinja2.pass_context
def gh_action_badge(ctx, ident):
    gh_path = f'{ctx.get("gh_org")}/{ctx.get("gh_repo")}'
    return (
        f'[![{ident}](https://github.com/{gh_path}/actions/workflows/{ident}.yaml/badge.svg)]'
        f'(https://github.com/{gh_path}/actions/workflows/{ident}.yaml)'
    )


class CoppyExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        # globals
        environment.globals['git_user_name'] = git_user_name
        environment.globals['git_user_email'] = git_user_email
        environment.globals['gh_action_badge'] = gh_action_badge

        # filters
        environment.filters['slugify'] = slugify
