#!/usr/bin/env python
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0OA
#
# Authors:
# - Wen Guan, <wen.guan@cern.ch>, 2019


"""
operations related to Messages.
"""

import re

from sqlalchemy import or_
from sqlalchemy.exc import DatabaseError, IntegrityError

from idds.common import exceptions
from idds.orm.base import models
from idds.orm.base.session import read_session, transactional_session


@transactional_session
def add_message(msg_type, status, source, msg_content, session=None):
    """
    Add a message to be submitted asynchronously to a message broker.

    :param msg_type: The type of the msg as a number, e.g., finished_stagein.
    :param status: The status about the message
    :param source: The source where the message is from.
    :param msg_content: The message msg_content as JSON.
    :param session: The database session.
    """

    try:
        new_message = models.Message(msg_type=msg_type, status=status,
                                     source=source, msg_content=msg_content)
        new_message.save(session=session)
    except TypeError as e:
        raise exceptions.DatabaseException('Invalid JSON for msg_content: %s' % str(e))
    except DatabaseError as e:
        if re.match('.*ORA-12899.*', e.args[0]) \
           or re.match('.*1406.*', e.args[0]):
            raise exceptions.DatabaseException('Could not persist message, msg_content too large: %s' % str(e))
        else:
            raise exceptions.DatabaseException('Could not persist message: %s' % str(e))


@read_session
def retrieve_messages(bulk=1000, msg_type=None, status=None, source=None, session=None):
    """
    Retrieve up to $bulk messages.

    :param bulk: Number of messages as an integer.
    :param msg_type: Return only specified msg_type.
    :param status: The status about the message
    :param source: The source where the message is from.
    :param session: The database session.

    :returns messages: List of dictionaries
    """
    messages = []
    try:
        query = session.query(models.Message)
        if msg_type is not None:
            query = query.filter_by(msg_type=msg_type)
        if status is not None:
            query = query.filter_by(status=status)
        if source is not None:
            query = query.filter_by(source=source)

        query = query.order_by(models.Message.created_at).limit(bulk)
        # query = query.with_for_update(nowait=True)

        tmp = query.all()
        if tmp:
            for t in tmp:
                messages.append(t.to_dict())
        return messages
    except IntegrityError as e:
        raise exceptions.DatabaseException(e.args)


@transactional_session
def delete_messages(messages, session=None):
    """
    Delete all messages with the given IDs.

    :param messages: The messages to delete as a list of dictionaries.
    """
    message_condition = []
    for message in messages:
        message_condition.append(models.Message.msg_id == message['msg_id'])

    try:
        if message_condition:
            session.query(models.Message).\
                with_hint(models.Message, "index(messages MESSAGES_PK)", 'oracle').\
                filter(or_(*message_condition)).\
                delete(synchronize_session=False)
    except IntegrityError as e:
        raise exceptions.DatabaseException(e.args)


@transactional_session
def update_messages(messages, session=None):
    """
    Update all messages status with the given IDs.

    :param messages: The messages to be updated as a list of dictionaries.
    """
    try:
        for msg in messages:
            session.query(models.Message).filter_by(msg_id=msg['msg_id']).update({'status': msg['status']}, synchronize_session=False)
    except IntegrityError as e:
        raise exceptions.DatabaseException(e.args)
