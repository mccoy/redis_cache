from redis_cache.redis_cache import RedisCache
from unittest import TestCase
from mock import Mock, patch
from inputs import SimpleObject
import pickle


class TestRedisCache(TestCase):
    """
    Test cases for redis_cache.py
    """

    def setUp(self):
        self.address = '10.10.10.10'
        self.port = 2345

    @patch('redis_cache.redis_cache.RedisClient')
    def test_cache_miss(self, mock_client_object):
        """
        Tests a cache miss
        """
        mock_client = Mock()
        # Simulates a cache miss
        mock_client.get.return_value = ''
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        # Create a function with the decorator
        @redis_cache.cache()
        def test_function(a):
            return a

        # Call that function
        test_param = 'input'
        function_response = test_function(test_param)

        mock_client_object.assert_called_once_with(self.address, self.port)
        expected_hash = str(hash('test_function' + test_param))
        mock_client.get.assert_called_once_with(expected_hash)
        mock_client.set.assert_called_once_with(
            expected_hash, pickle.dumps(test_param))

    @patch('redis_cache.redis_cache.RedisClient')
    def test_cache_miss_kwargs(self, mock_client_object):
        """
        Tests a cache miss against a function with kwargs
        """
        mock_client = Mock()
        # Simulates a cache miss
        mock_client.get.return_value = ''
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        # Create a function with the decorator
        @redis_cache.cache()
        def test_function(a, b, c=None, d=None):
            return a

        # Call that function
        test_a = 'input'
        test_b = 'b'
        test_c = True
        test_d = False
        function_response = test_function(test_a, test_b, c=test_c, d=test_d)

        mock_client_object.assert_called_once_with(self.address, self.port)
        expected_signature = \
            '%s,%s,c=%s,d=%s' % (test_a, test_b, str(test_c), str(test_d))
        expected_hash = str(hash('test_function' + expected_signature))
        mock_client.get.assert_called_once_with(expected_hash)
        mock_client.set.assert_called_once_with(
            expected_hash, pickle.dumps(test_a))

    @patch('redis_cache.redis_cache.RedisClient')
    def test_cache_miss_expiration(self, mock_client_object):
        """
        Tests a cache miss with an expiration given
        """
        test_param = 'cache hit test'
        ttl = 100
        mock_client = Mock()
        # Simulates a cache hit
        mock_client.get.return_value = ''
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        # Create a function with the decorator
        @redis_cache.cache(expiration=ttl)
        def test_function(a):
            return a

        # Call that function
        function_response = test_function(test_param)
        expected_hash = str(hash('test_function' + test_param))
        mock_client_object.assert_called_once_with(self.address, self.port)
        mock_client.get.assert_called_once_with(expected_hash)
        mock_client.setex.assert_called_once_with(
            expected_hash, pickle.dumps(test_param), ttl)
        self.assertEqual(mock_client.set.call_count, 0)

    @patch('redis_cache.redis_cache.RedisClient')
    def test_cache_hit(self, mock_client_object):
        """
        Tests a cache hit
        """
        test_param = 'cache hit test'
        mock_client = Mock()
        # Simulates a cache hit
        mock_client.get.return_value = pickle.dumps(test_param)
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        # Create a function with the decorator
        @redis_cache.cache()
        def test_function(a):
            return a

        # Call that function
        function_response = test_function(test_param)
        expected_hash = str(hash('test_function' + test_param))
        mock_client_object.assert_called_once_with(self.address, self.port)
        mock_client.get.assert_called_once_with(expected_hash)
        self.assertEqual(mock_client.set.call_count, 0)
        self.assertEqual(function_response, test_param)

    @patch('redis_cache.redis_cache.RedisClient')
    def test_cache_custom_signature(self, mock_client_object):
        """
        Tests a cache hit with custom signature
        """
        test_param = 'cache hit test'
        mock_client = Mock()
        # Simulates a cache hit
        mock_client.get.return_value = pickle.dumps(test_param)
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        def test_signature_builder(*args, **kwargs):
            return "test"

        # Create a function with the decorator
        @redis_cache.cache(signature_generator=test_signature_builder)
        def test_function(a):
            return a

        # Call that function
        function_response = test_function(test_param)
        expected_hash = str(hash('test_function'+test_signature_builder()))
        mock_client_object.assert_called_once_with(self.address, self.port)
        mock_client.get.assert_called_once_with(expected_hash)
        self.assertEqual(mock_client.set.call_count, 0)
        self.assertEqual(function_response, test_param)

    @patch('redis_cache.redis_cache.RedisClient')
    def test_simple_object(self, mock_client_object):
        """
        Tests caching of a simple Python object with pickling
        """
        mock_client = Mock()
        # Simulates a cache miss
        mock_client.get.return_value = ''
        mock_client_object.return_value = mock_client
        redis_cache = RedisCache(self.address, self.port)

        # Create a function with the decorator
        simple_obj = SimpleObject('test', 42)
        @redis_cache.cache()
        def test_function(a):
            return simple_obj

        # Call that function
        test_param = 'input'
        function_response = test_function(test_param)
        self.assertEqual(function_response, simple_obj)

        mock_client_object.assert_called_once_with(self.address, self.port)
        expected_hash = str(hash('test_function' + test_param))
        mock_client.get.assert_called_once_with(expected_hash)
        mock_client.set.assert_called_once_with(
            expected_hash, pickle.dumps(simple_obj))

        # Call that function, again, expecting a cache hit
        mock_client.get.return_value = pickle.dumps(simple_obj)
        function_response = test_function(test_param)
        self.assertEqual(function_response, simple_obj)
