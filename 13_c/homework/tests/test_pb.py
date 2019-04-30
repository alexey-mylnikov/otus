import os
import unittest
import pb
import gzip
import struct
import deviceapps_pb2

MAGIC = 0xFFFFFFFF
DEVICE_APPS_TYPE = 1
TEST_FILE = "test.pb.gz"


class TestPB(unittest.TestCase):
    deviceapps = [
        {"device": {"type": "idfa", "id": "e7e1a50c0ec2747ca56cd9e1558c0d7c"},
         "lat": 67.7835424444, "lon": -22.8044005471, "apps": [1, 2, 3, 4]},
        {"device": {"type": "gaid", "id": "e7e1a50c0ec2747ca56cd9e1558c0d7d"}, "lat": 42, "lon": -42, "apps": [1, 2]},
        {"device": {"type": "gaid", "id": "e7e1a50c0ec2747ca56cd9e1558c0d7d"}, "lat": 42, "lon": -42, "apps": []},
        {"device": {"type": "gaid", "id": "e7e1a50c0ec2747ca56cd9e1558c0d7d"}, "apps": [1]},
    ]

    def tearDown(self):
        os.remove(TEST_FILE)

    def test_write(self):
        bytes_written = pb.deviceapps_xwrite_pb(self.deviceapps, TEST_FILE)
        self.assertTrue(bytes_written > 0)
        dapps = deviceapps_pb2.DeviceApps()
        with gzip.open(TEST_FILE, 'rb') as fp:
            for app in self.deviceapps:
                magic, apps_type, length = struct.unpack('Ihh', fp.read(8))
                self.assertEqual(MAGIC, magic)
                self.assertEqual(DEVICE_APPS_TYPE, apps_type)

                dapps.ParseFromString(fp.read(length))
                if hasattr(app['device'], 'type'): self.assertEqual(app['device']['type'], dapps.device.type)
                if hasattr(app['device'], 'id'): self.assertEqual(app['device']['id'], dapps.device.id)
                if hasattr(app, 'lat'): self.assertEqual(app['lat'], dapps.lat)
                if hasattr(app, 'lon'): self.assertEqual(app['lon'], dapps.lon)
                for i in range(len(app['apps'])): self.assertEqual(app['apps'][i], dapps.apps[i])

    @unittest.skip("Optional problem")
    def test_read(self):
        pb.deviceapps_xwrite_pb(self.deviceapps, TEST_FILE)
        for i, d in enumerate(pb.deviceapps_xread_pb(TEST_FILE)):
            self.assertEqual(d, self.deviceapps[i])
