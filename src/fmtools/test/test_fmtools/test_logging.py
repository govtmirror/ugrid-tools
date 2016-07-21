from fmtools.logging import log
from fmtools.test.base import AbstractFMToolsTest, attr


class Test(AbstractFMToolsTest):
    @attr('mpi')
    def test(self):
        log.info('test hello world')

        try:
            raise RuntimeError('test runtime error')
        except:
            log.exception('test log exception')

        log.info('test passed')
