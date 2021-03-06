# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import sys
import time
import datetime

from django.test import TestCase
from django.core.cache import cache, get_cache
import redis_cache.cache


from redis_cache.client import herd

herd.CACHE_HERD_TIMEOUT = 2

if sys.version_info[0] < 3:
    text_type = unicode
    bytes_type = str
else:
    text_type = str
    bytes_type = bytes
    long = int


class DjangoRedisCacheTests(TestCase):
    def setUp(self):
        self.cache = cache

        try:
            self.cache.clear()
        except Exception:
            pass

    def test_setnx(self):
        # we should ensure there is no test_key_nx in redis
        self.cache.delete("test_key_nx")
        res = self.cache.get("test_key_nx", None)
        self.assertEqual(res, None)

        res = self.cache.set("test_key_nx", 1, nx=True)
        self.assertTrue(res)
        # test that second set will have
        res = self.cache.set("test_key_nx", 2, nx=True)
        self.assertFalse(res)
        res = self.cache.get("test_key_nx")
        self.assertEqual(res, 1)

        self.cache.delete("test_key_nx")
        res = self.cache.get("test_key_nx", None)
        self.assertEqual(res, None)

    def test_setnx_timeout(self):
        # test that timeout still works for nx=True
        res = self.cache.set("test_key_nx", 1, timeout=2, nx=True)
        self.assertTrue(res)
        time.sleep(3)
        res = self.cache.get("test_key_nx", None)
        self.assertEqual(res, None)

        # test that timeout will not affect key, if it was there
        self.cache.set("test_key_nx", 1)
        res = self.cache.set("test_key_nx", 2, timeout=2, nx=True)
        self.assertFalse(res)
        time.sleep(3)
        res = self.cache.get("test_key_nx", None)
        self.assertEqual(res, 1)

        self.cache.delete("test_key_nx")
        res = self.cache.get("test_key_nx", None)
        self.assertEqual(res, None)

    def test_save_and_integer(self):
        self.cache.set("test_key", 2)
        res = self.cache.get("test_key", "Foo")

        self.assertIsInstance(res, int)
        self.assertEqual(res, 2)

    def test_save_string(self):
        self.cache.set("test_key", "hello")
        res = self.cache.get("test_key")

        self.assertIsInstance(res, text_type)
        self.assertEqual(res, "hello")

        self.cache.set("test_key", "2")
        res = self.cache.get("test_key")

        self.assertIsInstance(res, text_type)
        self.assertEqual(res, "2")

    def test_save_unicode(self):
        self.cache.set("test_key", "heló")
        res = self.cache.get("test_key")

        self.assertIsInstance(res, text_type)
        self.assertEqual(res, "heló")

    def test_save_dict(self):
        now_dt = datetime.datetime.now()
        test_dict = {'id':1, 'date': now_dt, 'name': 'Foo'}

        self.cache.set("test_key", test_dict)
        res = self.cache.get("test_key")

        self.assertIsInstance(res, dict)
        self.assertEqual(res['id'], 1)
        self.assertEqual(res['name'], 'Foo')
        self.assertEqual(res['date'], now_dt)

    def test_save_float(self):
        float_val = 1.345620002

        self.cache.set("test_key", float_val)
        res = self.cache.get("test_key")

        self.assertIsInstance(res, float)
        self.assertEqual(res, float_val)

    def test_timeout(self):
        self.cache.set("test_key", 222, timeout=3)
        time.sleep(4)

        res = self.cache.get("test_key", None)
        self.assertEqual(res, None)

    def test_timeout_0(self):
        self.cache.set("test_key", 222, timeout=0)
        res = self.cache.get("test_key", None)
        self.assertEqual(res, 222)

    def test_timeout_negative(self):
        self.cache.set("test_key", 222, timeout=-1)
        res = self.cache.get("test_key", None)
        self.assertIsNone(res)

        self.cache.set("test_key", 222, timeout=0)
        self.cache.set("test_key", 222, timeout=-1)
        res = self.cache.get("test_key", None)
        self.assertIsNone(res)

        # nx=True should not overwrite expire of key already in db
        self.cache.set("test_key", 222, timeout=0)
        self.cache.set("test_key", 222, timeout=-1, nx=True)
        res = self.cache.get("test_key", None)
        self.assertEqual(res, 222)

    def test_set_add(self):
        self.cache.set('add_key', 'Initial value')
        self.cache.add('add_key', 'New value')
        res = cache.get('add_key')

        self.assertEqual(res, 'Initial value')

    def test_get_many(self):
        self.cache.set('a', 1)
        self.cache.set('b', 2)
        self.cache.set('c', 3)

        res = self.cache.get_many(['a','b','c'])
        self.assertEqual(res, {'a': 1, 'b': 2, 'c': 3})

    def test_get_many_unicode(self):
        self.cache.set('a', '1')
        self.cache.set('b', '2')
        self.cache.set('c', '3')

        res = self.cache.get_many(['a','b','c'])
        self.assertEqual(res, {'a': '1', 'b': '2', 'c': '3'})

    def test_set_many(self):
        self.cache.set_many({'a': 1, 'b': 2, 'c': 3})
        res = self.cache.get_many(['a', 'b', 'c'])
        self.assertEqual(res, {'a': 1, 'b': 2, 'c': 3})

    def test_delete(self):
        self.cache.set_many({'a': 1, 'b': 2, 'c': 3})
        res = self.cache.delete('a')
        self.assertTrue(bool(res))

        res = self.cache.get_many(['a', 'b', 'c'])
        self.assertEqual(res, {'b': 2, 'c': 3})

        res = self.cache.delete('a')
        self.assertFalse(bool(res))

    def test_delete_many(self):
        self.cache.set_many({'a': 1, 'b': 2, 'c': 3})
        res = self.cache.delete_many(['a','b'])
        self.assertTrue(bool(res))

        res = self.cache.get_many(['a', 'b', 'c'])
        self.assertEqual(res, {'c': 3})

        res = self.cache.delete_many(['a','b'])
        self.assertFalse(bool(res))

    def test_incr(self):
        try:
            self.cache.set("num", 1)

            self.cache.incr("num")
            res = self.cache.get("num")
            self.assertEqual(res, 2)

            self.cache.incr("num", 10)
            res = self.cache.get("num")
            self.assertEqual(res, 12)

            #max 64 bit signed int
            self.cache.set("num", 9223372036854775807)

            self.cache.incr("num")
            res = self.cache.get("num")
            self.assertEqual(res, 9223372036854775808)

            self.cache.incr("num", 2)
            res = self.cache.get("num")
            self.assertEqual(res, 9223372036854775810)

            self.cache.set("num", long(3))

            self.cache.incr("num", 2)
            res = self.cache.get("num")
            self.assertEqual(res, 5)

        except NotImplementedError as e:
            print(e)

    def test_get_set_bool(self):
        self.cache.set("bool", True)
        res = self.cache.get("bool")

        self.assertIsInstance(res, bool)
        self.assertEqual(res, True)

        self.cache.set("bool", False)
        res = self.cache.get("bool")

        self.assertIsInstance(res, bool)
        self.assertEqual(res, False)

    def test_decr(self):
        try:
            self.cache.set("num", 20)

            self.cache.decr("num")
            res = self.cache.get("num")
            self.assertEqual(res, 19)

            self.cache.decr("num", 20)
            res = self.cache.get("num")
            self.assertEqual(res, -1)

            self.cache.decr("num", long(2))
            res = self.cache.get("num")
            self.assertEqual(res, -3)

            self.cache.set("num", long(20))

            self.cache.decr("num")
            res = self.cache.get("num")
            self.assertEqual(res, 19)

            #max 64 bit signed int + 1
            self.cache.set("num", 9223372036854775808)

            self.cache.decr("num")
            res = self.cache.get("num")
            self.assertEqual(res, 9223372036854775807)

            self.cache.decr("num", 2)
            res = self.cache.get("num")
            self.assertEqual(res, 9223372036854775805)
        except NotImplementedError as e:
            print(e)

    def test_version(self):
        self.cache.set("keytest", 2, version=2)
        res = self.cache.get("keytest")
        self.assertEqual(res, None)

        res = self.cache.get("keytest", version=2)
        self.assertEqual(res, 2)

    def test_incr_version(self):
        try:
            self.cache.set("keytest", 2)
            self.cache.incr_version("keytest")

            res = self.cache.get("keytest")
            self.assertEqual(res, None)

            res = self.cache.get("keytest", version=2)
            self.assertEqual(res, 2)
        except NotImplementedError as e:
            print(e)

    def test_delete_pattern(self):
        for key in ['foo-aa','foo-ab', 'foo-bb','foo-bc']:
            self.cache.set(key, "foo")

        res = self.cache.delete_pattern('*foo-a*')
        self.assertTrue(bool(res))

        keys = self.cache.keys("foo*")
        self.assertEqual(set(keys), set(['foo-bb','foo-bc']))

        res = self.cache.delete_pattern('*foo-a*')
        self.assertFalse(bool(res))

    def test_close(self):
        cache = get_cache('default')
        cache.set("f", "1")
        cache.close()

    # def test_reuse_connection_pool(self):
    #     try:
    #         cache1 = get_cache('default')
    #         cache2 = get_cache('default')
    #         import pdb; pdb.set_trace()

    #         self.assertNotEqual(cache1, cache2)
    #         self.assertNotEqual(cache1.raw_client, cache2.raw_client)
    #         self.assertEqual(cache1.raw_client.connection_pool,
    #                          cache2.raw_client.connection_pool)
    #     except NotImplementedError:
    #         pass

    def test_master_slave_switching(self):
        try:
            cache = get_cache('sample')
            client = cache.client
            client._server = ["foo", "bar",]
            client._clients = ["Foo", "Bar"]

            self.assertEqual(client.get_client(write=True), "Foo")
            self.assertEqual(client.get_client(write=False), "Bar")
        except NotImplementedError:
            pass


class DjangoOmitExceptionsTests(TestCase):
    def setUp(self):
        self._orig_setting = redis_cache.cache.DJANGO_REDIS_IGNORE_EXCEPTIONS
        redis_cache.cache.DJANGO_REDIS_IGNORE_EXCEPTIONS = True
        self.cache = get_cache('doesnotexist')

    def tearDown(self):
        redis_cache.cache.DJANGO_REDIS_IGNORE_EXCEPTIONS = self._orig_setting

    def test_get(self):
        self.assertIsNone(self.cache.get('key'))
        self.assertEqual(self.cache.get('key', 'default'), 'default')
        self.assertEqual(self.cache.get('key', default='default'), 'default')


from django.contrib.sessions.backends.cache import SessionStore as CacheSession
from django.contrib.sessions.tests import SessionTestsMixin


class SessionTests(SessionTestsMixin, TestCase):
    backend = CacheSession

    def test_actual_expiry(self):
        pass
