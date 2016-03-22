from pmesh.logging import log
from pmesh.test.base import AbstractPmeshTest, attr


class Test(AbstractPmeshTest):
    @attr('mpi')
    def test(self):
        log.info('test hello world')

        try:
            raise RuntimeError('test runtime error')
        except:
            log.exception('test log exception')

        log.info('test passed')
