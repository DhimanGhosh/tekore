from asyncio import run
from unittest import TestCase
from unittest.mock import MagicMock, patch

from httpx import AsyncClient
from requests import Request
from tekore.sender import (
    TransientSender,
    AsyncTransientSender,
    PersistentSender,
    AsyncPersistentSender,
    SingletonSender,
    AsyncSingletonSender,
)

from tests._util import AsyncMock


class MockSessionFactory:
    prepare_return = 'prepared'

    def __init__(self):
        self.instances = []

    def __call__(self, *args, **kwargs):
        mock = MagicMock()
        mock.__enter__ = MagicMock(return_value=mock)
        mock.prepare_request = MagicMock(return_value=self.prepare_return)

        self.instances.append(mock)
        return mock


class TestSingletonSender(TestCase):
    def test_instances_share_session(self):
        s1 = SingletonSender()
        s2 = SingletonSender()
        self.assertTrue(s1.session is s2.session)

    def test_async_instances_share_client(self):
        s1 = AsyncSingletonSender()
        s2 = AsyncSingletonSender()
        self.assertTrue(s1.client is s2.client)

    def test_request_prepared(self):
        mock = MockSessionFactory()
        with patch('tekore.sender.SingletonSender.session', mock()):
            s = SingletonSender()
            r = Request()
            s.send(r)
            mock.instances[0].prepare_request.assert_called_with(r)

    def test_keywords_passed_to_session(self):
        mock = MockSessionFactory()
        kwargs = dict(k1='k1', k2='k2')
        with patch('tekore.sender.SingletonSender.session', mock()):
            s = SingletonSender(**kwargs)
            r = Request()
            s.send(r)
            mock.instances[0].send.assert_called_with(
                mock.prepare_return,
                **kwargs
            )

    def test_async_keywords_passed_to_client(self):
        # Test via raising from incorrect arguments
        s = AsyncSingletonSender(not_an_argument='raises')
        with self.assertRaises(TypeError):
            run(s.send(Request()))


def test_request_prepared(sender_type):
    mock = MockSessionFactory()
    with patch('tekore.sender.Session', mock):
        s = sender_type()
        r = Request()
        s.send(r)
        mock.instances[0].prepare_request.assert_called_with(r)


def test_keywords_passed_to_session(sender_type):
    mock = MockSessionFactory()
    kwargs = dict(k1='k1', k2='k2')
    with patch('tekore.sender.Session', mock):
        s = sender_type(**kwargs)
        s.send(Request())
        mock.instances[0].send.assert_called_with(mock.prepare_return, **kwargs)


class TestPersistentSender(TestCase):
    @patch('tekore.sender.Session', MagicMock)
    def test_session_is_reused(self):
        s = PersistentSender()
        sess1 = s.session
        s.send(Request())
        s.send(Request())
        sess2 = s.session
        self.assertTrue(sess1 is sess2)

    def test_async_client_is_reused(self):
        mock = AsyncMock()

        with patch('tekore.sender.AsyncClient.request', mock):
            s = AsyncPersistentSender()
            c1 = s.client
            run(s.send(Request()))
            run(s.send(Request()))
            c2 = s.client
            self.assertTrue(c1 is c2)

    def test_instances_dont_share_session(self):
        s1 = PersistentSender()
        s2 = PersistentSender()
        self.assertTrue(s1.session is not s2.session)

    def test_async_instances_dont_share_client(self):
        s1 = AsyncPersistentSender()
        s2 = AsyncPersistentSender()
        self.assertTrue(s1.client is not s2.client)

    def test_request_prepared(self):
        test_request_prepared(PersistentSender)

    def test_keywords_passed_to_session(self):
        test_keywords_passed_to_session(PersistentSender)

    def test_async_keywords_passed_to_client(self):
        # Test via raising from incorrect arguments
        s = AsyncPersistentSender(not_an_argument='raises')
        with self.assertRaises(TypeError):
            run(s.send(Request()))


class TestTransientSender(TestCase):
    def test_session_is_not_reused(self):
        mock = MockSessionFactory()
        with patch('tekore.sender.Session', mock):
            s = TransientSender()
            s.send(Request())
            s.send(Request())
            self.assertEqual(len(mock.instances), 2)

    def test_async_client_is_not_reused(self):
        client = AsyncClient()
        client.request = AsyncMock()
        mock = MagicMock(return_value=client)
        with patch('tekore.sender.AsyncClient', mock):
            s = AsyncTransientSender()
            run(s.send(Request()))
            run(s.send(Request()))
            self.assertEqual(mock.call_count, 2)

    def test_request_prepared(self):
        test_request_prepared(TransientSender)

    def test_keywords_passed_to_session(self):
        test_keywords_passed_to_session(TransientSender)

    def test_async_keywords_passed_to_client(self):
        s = AsyncTransientSender(not_an_argument='raises')
        with self.assertRaises(TypeError):
            run(s.send(Request()))
