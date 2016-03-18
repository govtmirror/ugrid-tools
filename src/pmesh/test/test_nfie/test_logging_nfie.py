import pytest

from pmesh.logging import log
from pmesh.test.base import AbstractNFIETest


class Test(AbstractNFIETest):

    @pytest.mark.mpi
    def test(self):
        log.info('test hello world')

        try:
            raise RuntimeError('test runtime error')
        except:
            log.exception('test log exception')

        log.info('test passed')
