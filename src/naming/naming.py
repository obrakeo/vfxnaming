# coding=utf-8
'''
Heavily based upon the work of Cesar Saez https://www.cesarsaez.me
'''
from __future__ import absolute_import, print_function

import copy
import os
import json

import six

# TODO: Add separator functionality

NAMING_REPO_ENV = "NAMING_REPO"
_rules = {'_active': None}
_tokens = dict()


class Serializable(object):
    def data(self):
        retval = copy.deepcopy(self.__dict__)
        retval["_Serializable_classname"] = type(self).__name__
        retval["_Serializable_version"] = "1.0"
        return retval

    @classmethod
    def from_data(cls, data):
        if data.get("_Serializable_classname") != cls.__name__:
            return None
        del data["_Serializable_classname"]
        if data.get("_Serializable_version") is not None:
            del data["_Serializable_version"]

        if cls.__name__ == 'Rule':
            this = cls(None, [None])
        else:
            this = cls(None)
        this.__dict__.update(data)
        return this


class Token(Serializable):
    def __init__(self, name):
        super(Token, self).__init__()
        self._name = name
        self._default = None
        self._options = dict()

    def add_option(self, key, value):
        self._options[key] = value

    def solve(self, name=None):
        """Solve for abbreviation given a certain name. Ex: center could return C"""
        if name is None:
            return self.default
        return self._options.get(name)

    def parse(self, value):
        """Get metatada (origin) for given value in name. Ex: L could return left"""
        for k, v in six.iteritems(self._options):
            if v == value:
                return k

    @property
    def required(self):
        return self.default is None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, n):
        self._name = n

    @property
    def default(self):
        if self._default is None and len(self._options) >= 1:
            self._default = self._options.values()[0]
        return self._default

    @default.setter
    def default(self, d):
        self._default = d

    @property
    def options(self):
        return copy.deepcopy(self._options)

    @property
    def is_number(self):
        return False


class TokenNumber(Token):
    def __init__(self, name):
        super(TokenNumber, self).__init__(name)
        self._is_number = True

    def solve(self, number):
        """Solve for number with given padding parameter.
            Ex: 1 could return 001 with padding 3"""
        numberStr = str(number).zfill(self.padding)
        return '{}{}{}'.format(self.prefix, numberStr, self.suffix)

    def parse(self, value):
        """Get metatada (number) for given value in name. Ex: v0025 could return 25"""
        if value.isdigit():
            return int(value)
        else:
            prefix_index = 0
            for each in value[::1]:
                if each.isdigit() and prefix_index == 0:
                    prefix_index = -1
                    break
                if not each.isdigit():
                    prefix_index += 1
                else:
                    break
            suffix_index = 0
            for each in value[::-1]:
                if each.isdigit() and suffix_index == 0:
                    suffix_index = -1
                    break
                if not each.isdigit():
                    suffix_index += 1
                else:
                    break

            if prefix_index == -1 and suffix_index >= 0:
                return int(value[:-suffix_index])
            elif prefix_index >= 0 and suffix_index == -1:
                return int(value[prefix_index:])
            elif prefix_index >= 0 and suffix_index >= 0:
                return int(value[prefix_index:-suffix_index])

    @property
    def padding(self):
        return self._options['padding']

    @padding.setter
    def padding(self, p):
        if p <= 0:
            p = 1
        self._options['padding'] = int(p)

    @property
    def prefix(self):
        return self._options['prefix']

    @prefix.setter
    def prefix(self, p):
        self._options['prefix'] = p

    @property
    def suffix(self):
        return self._options['suffix']

    @suffix.setter
    def suffix(self, s):
        self._options['suffix'] = s

    @property
    def default(self):
        self._default = 1
        return self._default

    @property
    def required(self):
        return True

    @property
    def is_number(self):
        return True


class Rule(Serializable):
    def __init__(self, name, fields):
        super(Rule, self).__init__()
        self.name = name
        self._fields = list()
        self.add_fields(fields)

    def add_fields(self, tokenNames):
        self._fields.extend(tokenNames)
        return True

    def solve(self, **values):
        """Build the name string with given values and return it"""
        return self._pattern.format(**values)

    def parse(self, name):
        """Build and return dictionary with keys as tokens and values as given names"""
        retval = dict()
        split_name = name.split('_')
        for i, f in enumerate(self.fields):
            name_part = split_name[i]
            token = _tokens[f]
            if token.required:
                if token.is_number:
                    retval[f] = token.parse(name_part)
                else:
                    retval[f] = name_part
                continue
            retval[f] = token.parse(name_part)
        return retval

    @property
    def _pattern(self):
        return '{' + '}_{'.join(self.fields) + '}'

    @property
    def fields(self):
        return tuple(self._fields)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, n):
        self._name = n


def add_rule(name, *fields):
    rule = Rule(name, fields)
    _rules[name] = rule
    if get_active_rule() is None:
        set_active_rule(name)
    return rule


def remove_rule(name):
    if has_rule(name):
        del _rules[name]
        return True
    return False


def has_rule(name):
    return name in _rules.keys()


def reset_rules():
    _rules.clear()
    _rules['_active'] = None
    return True


def get_active_rule():
    name = _rules['_active']
    return _rules.get(name)


def set_active_rule(name):
    if has_rule(name):
        _rules['_active'] = name
        return True
    return False


def get_rule(name):
    return _rules.get(name)


def save_rule(name, filepath):
    rule = get_rule(name)
    if not rule:
        return False
    with open(filepath, "w") as fp:
        json.dump(rule.data(), fp)
    return True


def load_rule(filepath):
    if not os.path.isfile(filepath):
        return False
    try:
        with open(filepath) as fp:
            data = json.load(fp)
    except Exception:
        return False
    rule = Rule.from_data(data)
    _rules[rule.name] = rule
    return True


def add_token(name, **kwargs):
    token = Token(name)
    for k, v in six.iteritems(kwargs):
        if k == "default":
            token.default = v
            continue
        token.add_option(k, v)
    _tokens[name] = token
    return token


def remove_token(name):
    if has_token(name):
        del _tokens[name]
        return True
    return False


def has_token(name):
    return name in _tokens.keys()


def reset_tokens():
    _tokens.clear()
    return True


def get_token(name):
    return _tokens.get(name)


def save_token(name, filepath):
    token = get_token(name)
    if not token:
        return False
    with open(filepath, "w") as fp:
        json.dump(token.data(), fp)
    return True


def load_token(filepath):
    if not os.path.isfile(filepath):
        return False
    try:
        with open(filepath) as fp:
            data = json.load(fp)
    except Exception:
        return False
    if data.get("_Serializable_classname") == 'TokenNumber':
        token = TokenNumber.from_data(data)
    else:
        token = Token.from_data(data)
    _tokens[token.name] = token
    return True


def add_token_number(name, prefix='', padding=3, suffix=''):
    token = TokenNumber(name)
    token.add_option('prefix', prefix)
    token.add_option('padding', padding)
    token.add_option('suffix', suffix)
    _tokens[name] = token
    return token


def parse(name):
    rule = get_active_rule()
    return rule.parse(name)


def solve(*args, **kwargs):
    values = dict()
    rule = get_active_rule()
    i = 0
    for f in rule.fields:
        token = _tokens[f]
        if isinstance(token, TokenNumber):
            if kwargs.get(f) is not None:
                values[f] = token.solve(kwargs[f])
                continue
            values[f] = token.solve(args[i])
            i += 1
            continue
        if token.required:
            if kwargs.get(f) is not None:
                values[f] = kwargs[f]
                continue
            values[f] = args[i]
            i += 1
            continue
        values[f] = token.solve(kwargs.get(f))

    return rule.solve(**values)


def get_repo():
    env_repo = os.environ.get(NAMING_REPO_ENV)
    local_repo = os.path.join(os.path.expanduser("~"), ".NXATools", "naming")
    return env_repo or local_repo


def save_session(repo=None):
    repo = repo or get_repo()
    if not os.path.exists(repo):
        os.mkdir(repo)
    # tokens and rules
    for name, token in six.iteritems(_tokens):
        filepath = os.path.join(repo, name + ".token")
        save_token(name, filepath)
    for name, rule in six.iteritems(_rules):
        if not isinstance(rule, Rule):
            continue
        filepath = os.path.join(repo, name + ".rule")
        save_rule(name, filepath)
    # extra configuration
    active = get_active_rule()
    config = {"set_active_rule": active.name if active else None}
    filepath = os.path.join(repo, "naming.conf")
    with open(filepath, "w") as fp:
        json.dump(config, fp, indent=4)
    return True


def load_session(repo=None):
    repo = repo or get_repo()
    # tokens and rules
    for dirpath, dirnames, filenames in os.walk(repo):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if filename.endswith(".token"):
                load_token(filepath)
            elif filename.endswith(".rule"):
                load_rule(filepath)
    # extra configuration
    filepath = os.path.join(repo, "naming.conf")
    if os.path.exists(filepath):
        with open(filepath) as fp:
            config = json.load(fp)
        for k, v in six.iteritems(config):
            globals()[k](v)  # executes set_active_rule and sets it
    return True