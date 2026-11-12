"""Host tests for release metadata; official firmware parsers tested separately."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
import prepare_managed_release as release


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.binary = b'\xe9' + bytes(range(256)) * 8
        self.manifest = release.create_manifest('1.2.0-dev.1', self.binary)

    def test_checksums_and_pinned_url(self):
        ota = self.manifest['builds'][0]['ota']
        self.assertEqual(ota['md5'], hashlib.md5(self.binary).hexdigest())
        self.assertEqual(ota['sha256'], hashlib.sha256(self.binary).hexdigest())
        self.assertIn('/download/v1.2.0-dev.1/', ota['path'])
        self.assertNotIn('/latest/', ota['path'])
        self.assertEqual(json.loads(json.dumps(self.manifest)), self.manifest)

    def test_release_validation_rejects_wrong_project_board_chip_or_hash(self):
        for key, value in [('project', 'foreign.project'), ('hardware', 'different-board'), ('version', 'unknown')]:
            with self.subTest(key=key):
                m = copy.deepcopy(self.manifest)
                m[key] = value
                with self.assertRaises(AssertionError):
                    release.validate_manifest(m)
        for key, value in [('md5', 'abc'), ('sha256', 'xyz'), ('path', 'http://untrusted/firmware.bin')]:
            with self.subTest(ota=key):
                m = copy.deepcopy(self.manifest)
                m['builds'][0]['ota'][key] = value
                with self.assertRaises(AssertionError):
                    release.validate_manifest(m)
        m = copy.deepcopy(self.manifest)
        m['builds'][0]['chipFamily'] = 'ESP32-C3'
        with self.assertRaises(AssertionError):
            release.validate_manifest(m)

    def test_factory_is_optional_for_preview_only(self):
        self.assertNotIn('parts', self.manifest['builds'][0])
        m = release.create_manifest('1.2.0', self.binary, include_factory=True)
        self.assertEqual(m['builds'][0]['parts'][0]['offset'], 0)
        self.assertTrue(m['builds'][0]['parts'][0]['path'].endswith('/onju-voice.factory.bin'))


    def test_same_build_factory_segments_and_app_must_match(self):
        import tempfile, struct
        with tempfile.TemporaryDirectory(prefix='onju-release-test-') as directory:
            root = Path(directory)
            build = root/'build-root'
            (build/'src/esphome/core').mkdir(parents=True)
            (build/'build').mkdir()
            (build/'src/main.cpp').write_text('// onju_identity::pre_setup( /* generic defaults */ , nullptr);\n// http_request::HttpRequestUpdate http_request::OtaHttpRequestComponent ESPHomeOTAComponent\n')
            (build/'src/esphome/core/defines.h').write_text('#define ESPHOME_PROJECT_VERSION "1.2.0-dev.1"\n#define ESPHOME_PROJECT_NAME "tetele.onju_voice_satellite"\n#define USE_ONJU_IDENTITY\n#define USE_IMPROV_SERIAL\n#define USE_UPDATE\n#define USE_HTTP_REQUEST\n#define USE_OTA\n')
            (build/'build_info.json').write_text(json.dumps({'esphome_version':'2026.10.2'}))
            (build/'partitions.csv').write_text('otadata,data,ota,0xe000,0x2000\napp0,app,ota_0,0x10000,0x7c0000\n')
            app = bytearray(1024)
            app[0] = 0xE9
            app[12:14] = (9).to_bytes(2,'little')
            app[32:36] = bytes.fromhex('3254cdab')
            (build/'build/firmware.ota.bin').write_bytes(app)
            (build/'build/onju-voice.bin').write_bytes(app)
            parts = {'0x0':'boot.bin','0x8000':'part.bin','0xe000':'ota.bin','0x10000':'onju-voice.bin'}
            (build/'build/boot.bin').write_bytes(b'\xe9'+b'B'*127)
            table = struct.pack('<HBBII16sI',0x50AA,1,0,0xe000,8192,b'otadata',0) + struct.pack('<HBBII16sI',0x50AA,0,16,0x10000,0x7c0000,b'app0',0) + struct.pack('<HBBII16sI',0x50AA,0,17,0x7d0000,0x7c0000,b'app1',0)
            (build/'build/part.bin').write_bytes(table+b'\xff'*32)
            (build/'build/partition_table').mkdir()
            (build/'build/partition_table/partition-table.bin').write_bytes(table+b'\xff'*32)
            (build/'build/ota.bin').write_bytes(b'\xff'*8192)
            (build/'build/flasher_args.json').write_text(json.dumps({'flash_files':parts}))
            factory = bytearray(b'\xff'*(0x10000+len(app)))
            for address,name in parts.items():
                address=int(address,0)
                data=(build/'build'/name).read_bytes()
                factory[address:address+len(data)]=data
            (build/'build/firmware.factory.bin').write_bytes(factory)
            result=release.package(build,root/'valid','a'*40,require_factory=True)
            self.assertTrue(result['factory_app_equals_ota'])
            self.assertEqual((root/'valid'/release.OTA_NAME).read_bytes(),app)
            factory[0x10001]^=1
            (build/'build/firmware.factory.bin').write_bytes(factory)
            with self.assertRaises(AssertionError):
                release.package(build,root/'mismatched','a'*40,require_factory=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
