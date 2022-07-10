# from unittest import TestCase
#
# import config
# from wcdimportbot.models.ssdb_database import SsdbDatabase
#
#
# class TestSsdbAwsDatabase(TestCase):
#     @staticmethod
#     def test_set():
#         if config.use_cache:
#             r = SsdbDatabase(host="archive-wcd.aws.scatter.red")
#             r.connect()
#             r.set_value(key="test", value="test")
#             result = r.get_value("test").decode("UTF-8")
#             print(result)
#             assert result == "test"
#
#     def test_flush_database(self):
#         if config.use_cache:
#             r = SsdbDatabase(host="archive-wcd.aws.scatter.red")
#             r.connect()
#             r.set_value(key="test", value="test")
#             r.flush_database()
#             result = r.get_value("test")
#             # print(result)
#             assert result == None
