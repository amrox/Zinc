from tests import *
#from zinc import ZincCatalog, create_repo_at_path, ZINC_FORMAT
from zinc import *
import os.path

class ZincCatalogTestCase(TempDirTestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.dir, "repo")
        os.mkdir(self.repo_dir)
        self.scratch_dir = os.path.join(self.dir, "scratch")
        os.mkdir(self.scratch_dir)

    def test_repo_create(self):
        repo = create_repo_at_path(self.repo_dir, 'com.mindsnacks.test')
        assert repo is not None
        assert repo.is_loaded() == True
        assert len(repo.verify()) == 0
        assert len(repo.bundle_names()) == 0
        assert repo.format() == ZINC_FORMAT

    def test_repo_create_manifest(self):
        repo = create_repo_at_path(self.repo_dir, 'com.mindsnacks.test')
        manifest = repo._add_manifest("beep")
        assert manifest is not None
 
    def test_repo_create_duplicate_manifest(self):
        repo = create_repo_at_path(self.repo_dir, 'com.mindsnacks.test')
        manifest1 = repo._add_manifest("beep")
        assert manifest1 is not None
        self.assertRaises(ValueError, repo._add_manifest, "beep")

    def test_repo_read_invalid_format(self):
        create_repo_at_path(self.repo_dir, 'com.mindsnacks.test')
        index_path = os.path.join(self.repo_dir, ZINC_REPO_INDEX)
        index = load_index(index_path)
        index.format = 2
        index.write(index_path)
        self.assertRaises(Exception, ZincCatalog, (self.repo_dir))

    def test_repo_import_file(self):
        repo = create_repo_at_path(self.repo_dir, 'com.mindsnacks.test')
        f1 = create_random_file(self.scratch_dir)
        repo._import_path(f1)

    # TODO: kill test?
    #def test_bundle_add_version_without_repo(self):
    #    bundle = ZincBundle("honk")
    #    assert bundle is not None
    #    self.assertRaises(Exception, bundle.add_version)

    def test_bundle_names_with_no_bundles(self):
        repo = create_repo_at_path(self.repo_dir, 'com.mindsnacks.test')
        assert len(repo.bundle_names()) == 0

    def test_version_for_bundle(self):
        repo = create_repo_at_path(self.repo_dir, 'com.mindsnacks.test')
        repo._add_manifest("meep", 1)
        versions = repo.versions_for_bundle("meep")
        assert 1 in versions
        assert len(versions) == 1

    def test_versions_for_nonexistant_bundle(self):
        repo = create_repo_at_path(self.repo_dir, 'com.mindsnacks.test')
        versions = repo.versions_for_bundle("meep")
        assert len(versions) == 0

    def _build_test_repo(self):
        repo = create_repo_at_path(self.repo_dir, 'com.mindsnacks.test')
        f1 = create_random_file(self.scratch_dir)
        f2 = create_random_file(self.scratch_dir)
        repo.create_bundle_version("meep", self.scratch_dir)
        return repo

    def test_create_bundle_version(self):
        repo = self._build_test_repo()
        assert "meep" in repo.bundle_names()
        assert 1 in repo.versions_for_bundle("meep")
        manifest = repo.manifest_for_bundle("meep", 1)
        assert manifest is not None
        for (file, props) in manifest.files.items():
            sha = props['sha']
            formats = props['formats']
            for format in formats.keys():
                ext = None
                if format == 'gz':
                    ext = '.gz'
                object_path = repo._path_for_file_with_sha(file, sha, ext)
                assert os.path.exists(object_path)

    def test_create_bundle_with_subdirs(self):
        f1 = create_random_file(self.scratch_dir)
        one_dir = os.mkdir(os.path.join(self.scratch_dir, "one"))
        f2 = create_random_file(one_dir)
        repo = create_repo_at_path(self.repo_dir, 'com.mindsnacks.test')
        repo.create_bundle_version("meep", self.scratch_dir)
        results = repo.verify()
        
    def test_create_second_bundle_version(self):
        repo = self._build_test_repo()
        # add a file
        f3 = create_random_file(self.scratch_dir)
        repo.create_bundle_version("meep", self.scratch_dir)
        assert 2 in repo.versions_for_bundle("meep")
        new_index = load_index(os.path.join(repo.path, ZINC_REPO_INDEX))
        assert 1 in new_index.bundles["meep"]
        assert 2 in new_index.bundles["meep"]

    def test_create_identical_bundle_version(self):
        repo = self._build_test_repo()
        repo.create_bundle_version("meep", self.scratch_dir)
        assert len(repo.versions_for_bundle("meep"))==1

    def test_repo_verify(self):
        repo = self._build_test_repo()
        results = repo.verify()

class ZincIndexTestCase(TempDirTestCase):

    def test_versions_for_nonexistant_bundle(self):
        index = ZincIndex()
        assert len(index.versions_for_bundle("meep")) == 0

    def test_add_version_for_bundle(self):
        index = ZincIndex()
        index.add_version_for_bundle("meep", 1)
        assert 1 in index.bundles["meep"]

    def test_add_duplicate_version_for_bundle(self):
        index = ZincIndex()
        index.add_version_for_bundle("meep", 1)
        index.add_version_for_bundle("meep", 1)
        assert 1 in index.bundles["meep"]
        assert len(index.bundles["meep"]) == 1

    def test_del_version_for_nonexistant_bundle(self):
        index = ZincIndex()
        index.del_version_for_bundle("meep", 1)
        assert len(index.versions_for_bundle("meep")) == 0

    def test_del_version_for_bundle(self):
        index = ZincIndex()
        index.add_version_for_bundle("meep", 1)
        index.add_version_for_bundle("meep", 2)
        index.del_version_for_bundle("meep", 1)
        assert len(index.versions_for_bundle("meep")) == 1
        assert 2 in index.versions_for_bundle("meep")

    def test_del_nonexistant_version_for_bundle(self):
        index = ZincIndex()
        index.add_version_for_bundle("meep", 1)
        index.del_version_for_bundle("meep", 2)
        assert len(index.versions_for_bundle("meep")) == 1
        assert 1 in index.versions_for_bundle("meep")

    def test_del_nonexistant_version_for_bundle(self):
        index = ZincIndex()
        index.add_version_for_bundle("meep", 1)
        index.del_version_for_bundle("meep", 2)

    def test_update_distro_bad_bundle(self):
        index = ZincIndex()
        self.assertRaises(ValueError, index.update_distribution, "live", "beep", 1)

    def test_update_distro_bad_bundle_version(self):
        index = ZincIndex()
        index.add_version_for_bundle("beep", 1)
        self.assertRaises(ValueError, index.update_distribution, "live", "beep", 2)

    def test_update_distro_ok(self):
        index = ZincIndex()
        index.add_version_for_bundle("meep", 1)
        index.update_distribution("live", "meep", 1)

class ZincManifestTestCase(TempDirTestCase):

    def test_save_and_load(self):
        manifest1 = ZincManifest("meep", 1)
        manifest1.files = {
                'a': {
                    'sha': 'ea502a7bbd407872e50b9328956277d0228272d4',
                    'formats': { 
                        'raw' : {
                            'size': 123
                            }
                        }
                    }
                }
        path = os.path.join(self.dir, "manifest.json")
        manifest1.write(path)
        manifest2 = load_manifest(path)
        assert manifest1.equals(manifest2)
