from utools.logging import log
from utools.test.base import AbstractUToolsTest, attr


class Test(AbstractUToolsTest):
    @attr('mpi')
    def test(self):
        log.info('test hello world')

        try:
            raise RuntimeError('test runtime error')
        except:
            log.exception('test log exception')

        log.info('test passed')
