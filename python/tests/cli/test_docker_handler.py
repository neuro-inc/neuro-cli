import pytest
from neuromation.cli.docker_handler import Image
from yarl import URL


class TestImage:
    @pytest.mark.parametrize("test_url,expected_url,expected_local", [
        (URL('image://bob/php:7-fpm'), URL('image://bob/php:7-fpm'),
         'php:7-fpm'),
        (URL('image://bob/php'), URL('image://bob/php:latest'),
         'php:latest'),
        (URL('image:php:7-fpm'), URL('image://bob/php:7-fpm'),
         'php:7-fpm'),
        (URL('image:php'), URL('image://bob/php:latest'),
         'php:latest'),
        (URL('image://bob/project/php:7-fpm'),
         URL('image://bob/project/php:7-fpm'),
         'project/php:7-fpm'),
        (URL('image:project/php'),
         URL('image://bob/project/php:latest'),
         'project/php:latest')
    ])
    def test_correct_url(self, test_url, expected_url, expected_local):
        image = Image.from_url(test_url, 'bob')
        assert image.url == expected_url
        assert image.local == expected_local

    def test_from_empty_url(self):
        with pytest.raises(ValueError, match='Image URL cannot be empty'):
            Image.from_url(url=URL(''), username='bob')
        pass

    def test_from_invalid_scheme_url(self):
        with pytest.raises(ValueError, match=r'Invalid scheme'):
            Image.from_url(
                url=URL('http://neuromation.io/what/does/the/fox/say'),
                username='ylvis')
        pass

    def test_empty_path_url(self):
        with pytest.raises(ValueError, match=r'Image URL cannot be empty'):
            Image.from_url(url=URL('image:'), username='bob')
        with pytest.raises(ValueError, match=r'Invalid image'):
            Image.from_url(url=URL('image:///'), username='bob')
        pass

    def test_url_with_query(self):
        with pytest.raises(ValueError, match=r'Invalid image'):
            Image.from_url(url=URL('image://bob/image?bad=idea'),
                           username='bob')
        pass

    def test_url_with_user(self):
        with pytest.raises(ValueError, match=r'Invalid image'):
            Image.from_url(url=URL('image://alien@bob/image'), username='bob')
        pass

    def test_url_with_port(self):
        with pytest.raises(ValueError, match=r'Invalid image'):
            Image.from_url(url=URL('image://bob:80/image'), username='bob')
        pass

    def test_url_with_few_colons(self):
        with pytest.raises(ValueError, match=r'only one colon allowed'):
            Image.from_url(url=URL('image://bob/image:tag1:tag2'),
                           username='bob')
        pass

    @pytest.mark.parametrize("test_local,expected_url,expected_local", [
        ('php:7-fpm', URL('image://bob/php:7-fpm'), 'php:7-fpm'),
        ('php', URL('image://bob/php:latest'), 'php:latest'),
        ('project/php:7-fpm', URL('image://bob/project/php:7-fpm'),
         'project/php:7-fpm'),
        ('project/php', URL('image://bob/project/php:latest'),
         'project/php:latest')
    ])
    def test_correct_local(self, test_local, expected_url, expected_local):
        image = Image.from_local(test_local, 'bob')
        assert image.url == expected_url
        assert image.local == expected_local

    def test_local_with_few_colons(self):
        with pytest.raises(ValueError, match=r'only one colon allowed'):
            Image.from_local('image:tag1:tag2', 'bob')

    def test_repo(self):
        image = Image.from_url(URL('image:php:5'), 'bob')
        assert image.to_repo('registry.neuromation.io') == 'registry.neuromation.io/bob/php:5'


class TestDockerHandler:
    pass