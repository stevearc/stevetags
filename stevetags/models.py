import calendar
import json
from datetime import datetime
from pyramid.settings import asbool
from sqlalchemy import Column, Text, Boolean, DateTime, ForeignKey, Index, DDL, event, func
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict


Base = declarative_base()  # pylint: disable=C0103


def set_property(cls, prop):
    if len(prop) == 2 and issubclass(prop[1], DictWrapper):
        name = prop[0]
        type = prop[1]

        def getter(self):
            return type(self._obj, self._data)

        def setter(self, val):
            getter(self).update(val)
    else:
        name = prop[0]
        key = prop[1]
        idx = 2
        if isinstance(key, basestring):
            type = prop[2]
            idx += 1
        else:
            type = key
            key = name
        default = None if len(prop) < idx + 1 else prop[idx]
        if isinstance(type, (tuple, list)):
            deserialize, serialize = type
        else:
            noop = lambda x: x
            deserialize, serialize = noop, noop

        def getter(self):
            if key in self._data:
                return deserialize(self._data[key])
            else:
                if callable(default):
                    return default(self)
                else:
                    return default

        def setter(self, val):
            if val is None or type in (str, unicode, basestring) and not val.strip():
                if key in self._data:
                    del self._data[key]
            else:
                self._data[key] = serialize(val)
    setattr(cls, name, property(getter, setter))


class DictWrapperMeta(type):

    def __new__(mcs, name, bases, dct):
        cls = super(DictWrapperMeta, mcs).__new__(mcs, name, bases, dct)
        for prop in cls.__props__:
            set_property(cls, prop)

        return cls


class DictWrapper(object):
    __metaclass__ = DictWrapperMeta
    __props__ = []

    def __init__(self, obj, data):
        self._obj = obj
        self._data = data

    def update(self, data):
        for key, val in data.iteritems():
            setattr(self, key, val)

    def __json__(self, request=None):
        data = {}
        for prop in dir(self):
            if not prop.startswith('_') and not callable(getattr(self, prop)):
                data[prop] = getattr(self, prop)
        return data


MIME_TYPES = {
    'text': lambda x: x == 'text/plain',
    'pdf': lambda x: x == 'application/pdf',
    'image': lambda x: x.startswith('image/'),
}


class UserSettings(DictWrapper):
    __props__ = [
        ('roots', list, ['/']),
        ('filetypes', list, []),
        ('box', str, 'personal'),
        ('tour_step', int, 1),
        ('tour_complete', bool, False),
    ]


class User(Base):

    """ User model """

    __tablename__ = 'users'
    id = Column(Text, primary_key=True)
    email = Column(Text, nullable=False)
    display_name = Column(Text, nullable=False)
    familiar_name = Column(Text, nullable=False)
    created = Column(DateTime(timezone=True), index=True, nullable=False, default=func.now())
    data = Column(MutableDict.as_mutable(JSONB), nullable=False)

    def __init__(self, id, email, display_name, familiar_name):
        self.id = id
        self.email = email
        self.display_name = display_name
        self.familiar_name = familiar_name
        self.data = {}

    @property
    def settings(self):
        """ Getter for settings """
        return UserSettings(self, self.data)

    def should_save_file(self, metadata):
        # If no filetypes specified, save all.
        if not self.settings.filetypes:
            return True
        mime_type = metadata.get('mime_type')
        if mime_type is None:
            return False
        for key in self.settings.filetypes:
            if MIME_TYPES[key](mime_type):
                return True
        return False

    def __repr__(self):
        return 'User(%s)' % self.email

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == getattr(other, 'id', None)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __json__(self, request=None):
        data = {
            'id': self.id,
            'display_name': self.display_name,
            'familiar_name': self.familiar_name,
            'settings': self.settings,
            '_mime_types': MIME_TYPES.keys(),
        }
        return data



class Directory(Base):

    __tablename__ = 'dirs'
    path = Column(Text, primary_key=True)
    ownerid = Column(Text, ForeignKey(User.id, ondelete='cascade'), primary_key=True)
    hash = Column(Text)
    # Marked for sweeping
    marked = Column(Boolean, index=True, nullable=False, default=False)

    def __init__(self, ownerid, path, hash):
        self.ownerid = ownerid
        self.path = path
        self.hash = hash

    def __hash__(self):
        return hash(self.ownerid) + hash(self.path)

    def __eq__(self, other):
        return self.ownerid == getattr(other, 'ownerid', None) and \
            self.path == getattr(other, 'path', None)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'Dir(%s)' % self.path

    def __json__(self, request=None):
        return {
            'path': self.path,
            'hash': self.hash,
        }


class File(Base):

    __tablename__ = 'files'
    path = Column(Text, primary_key=True)
    ownerid = Column(Text, ForeignKey(User.id, ondelete='cascade'), primary_key=True)
    search_text = Column(TSVECTOR, nullable=False)
    tags = Column(Text, nullable=False, default='')
    created = Column(DateTime(timezone=True), index=True, nullable=False, default=func.now())
    modified = Column(DateTime(timezone=True), index=True, nullable=False)
    tagged = Column(Boolean, index=True, nullable=False, default=False)
    # Marked for sweeping
    marked = Column(Boolean, index=True, nullable=False, default=False)
    mime_type = Column(Text)
    __table_args__ = (
        Index('search_text_idx', 'search_text', postgresql_using='gin'),
    )

    def __init__(self, ownerid, path, modified, mime_type):
        self.ownerid = ownerid
        self.path = path
        self.modified = modified
        self.mime_type = mime_type

    def __hash__(self):
        return hash(self.ownerid) + hash(self.path)

    def __eq__(self, other):
        return self.ownerid == getattr(other, 'ownerid', None) and \
            self.path == getattr(other, 'path', None)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'File(%s)' % self.path

    def __json__(self, request=None):
        return {
            'path': self.path,
            'tags': self.tags,
            'created': self.created,
            'modified': self.modified,
            'mime_type': self.mime_type,
        }


def attach_triggers():
    """ Attach some database triggers to the File table """
    function_snippet = DDL("""
    CREATE OR REPLACE FUNCTION update_file_search_text_vector() RETURNS TRIGGER AS $$
    BEGIN
        IF TG_OP = 'INSERT' THEN
            new.search_text = to_tsvector('pg_catalog.english', NEW.tags) || to_tsvector('pg_catalog.english', translate(NEW.path, '/.', '  '));
        END IF;
        IF TG_OP = 'UPDATE' THEN
            IF NEW.tags <> OLD.tags || NEW.path <> OLD.path THEN
                new.search_text = to_tsvector('pg_catalog.english', NEW.tags) || to_tsvector('pg_catalog.english', translate(NEW.path, '/.', '  '));
            END IF;
        END IF;
        RETURN NEW;
    END
    $$ LANGUAGE 'plpgsql';
    """)

    trigger_snippet = DDL("""
    CREATE TRIGGER search_text_update BEFORE INSERT OR UPDATE
    ON files
    FOR EACH ROW EXECUTE PROCEDURE
    update_file_search_text_vector()
    """)

    event.listen(File.__table__, 'after_create',
                 function_snippet.execute_if(dialect='postgresql'))
    event.listen(File.__table__, 'after_create',
                 trigger_snippet.execute_if(dialect='postgresql'))

attach_triggers()
